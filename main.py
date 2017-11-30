import praw
import os
import re
import json
import urllib2

import prawcore

reddit = None
subreddit = None
posts_replied_to = None


def setup_bot():
    global reddit, subreddit, posts_replied_to

    reddit = praw.Reddit('mc_bot')
    subreddit = reddit.subreddit("buildapcsales")

    if not os.path.isfile("posts_replied_to.txt"):
        posts_replied_to = []
    else:
        with open("posts_replied_to.txt", "r") as f:
            posts_replied_to = f.read()
            posts_replied_to = posts_replied_to.split()


def start_searching():
    global posts_replied_to

    print "Listening for posts from microcenter.com..."
    try:
        for submission in subreddit.stream.submissions():
            if submission.id not in posts_replied_to:
                #  only operate on links that are pointed to microcenter.com
                if re.search("microcenter.com", submission.url, re.IGNORECASE):
                    #  travel to the link and start parsing
                    print "navigating to %s" % submission.url
                    try:
                        page = urllib2.urlopen(submission.url)
                        raw_html = page.read()

                        stocks = get_stock(raw_html)
                        stocks_reply = reply_stocks(stocks)

                        price = get_price(raw_html)
                        price_reply = reply_price(price)

                        master_reply = stocks_reply + price_reply + get_base_submission()
                        submission.reply(master_reply)

                        posts_replied_to.append(submission.id)
                        mark_post_as_replied(submission.id)
                    except urllib2.URLError:
                        reply_with_error(submission, "urlerror")
    except prawcore.exceptions.RequestException:
        print "Some sort of error with reddit API. Restarting bot"
        start_searching()


def get_stock(raw_html):
    #  Extract stock from javascript

    reg = re.search("(?<=inventory = )(.*)", raw_html)

    try:
        stock_json = reg.group(0).strip()
        stocks = json.loads(stock_json)
    except AttributeError:
        print "Error accessing JSON"
        return []

    # Return the stocks as tuples
    return [(x["storeName"], x["qoh"]) for x in stocks]


def get_price(raw_html):
    reg = re.search("(?s)(?<=dataLayer = \[)(.*?)(?=\];)", raw_html)
    try:
        data_layer_json = reg.group(0).strip()
        data_layer_json = data_layer_json.replace("'", "\"")
        data_layer_obj = json.loads(data_layer_json)
    except AttributeError:
        print "Error accessing JSON"
        return "Couldn't determine price."

    return "$" + data_layer_obj["productPrice"]


def reply_stocks(stocks):
    print "Generating reply"
    header = "I found this product at the following stores\n\nStore | Quantity\n------|---------\n"

    for stock in stocks:
        header += " " + stock[0] + " | " + str(stock[1]) + "\n"

    return header


def reply_price(price):
    return "\n\nAdditionally, I found the item priced at %s\n\n" % price


def reply_with_error(submission, errortype):
    if errortype == "urlerror":
        submission.reply("I was unable to find stock information for this page." + get_base_submission())


def get_base_submission():
    return """\n\n
[source code](https://github.com/darakelian/MCStockCheckerBot) - [report errors](https://github.com/darakelian/MCStockCheckerBot/issues) 
    """


def mark_post_as_replied(post_id):
    with open("posts_replied_to.txt", "a+") as f:
        f.write(post_id + "\n")


if __name__ == "__main__":
    setup_bot()
    start_searching()
