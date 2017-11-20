import praw
import os
import re
import json
import urllib2

reddit = None
subreddit = None
posts_replied_to = None


def setup_bot():
    global reddit, subreddit, posts_replied_to

    reddit = praw.Reddit('mc_bot')
    subreddit = reddit.subreddit("StockCheckerTesting")

    if not os.path.isfile("posts_replied_to.txt"):
        posts_replied_to = []
    else:
        with open("posts_replied_to.txt", "r") as f:
            posts_replied_to = f.read()
            posts_replied_to = posts_replied_to.split()


def start_searching():
    global posts_replied_to

    print "Listening for posts from microcenter.com..."
    for submission in subreddit.stream.submissions():
        if submission.id not in posts_replied_to:
            #  only operate on links that are pointed to microcenter.com
            if re.search("microcenter.com", submission.url, re.IGNORECASE):
                #  travel to the link and start parsing
                print "navigating to %s" % submission.url
                try:
                    page = urllib2.urlopen(submission.url)
                    stocks = get_stock(page)
                    reply_stocks(submission, stocks)
                    posts_replied_to.append(submission.id)
                    mark_post_as_replied(submission.id)
                except urllib2.URLError:
                    reply_with_error(submission, "urlerror")


def get_stock(page_object):
    raw_html = page_object.read()
    #  Extract stock from javascript
    stock_json = re.search("(?<=inventory = )(.*)", raw_html).group(0).strip()
    stocks = json.loads(stock_json)

    #  Return the stocks as tuples
    return [(x["storeName"], x["qoh"]) for x in stocks]


def reply_stocks(submission, stocks):
    print "replying to submission %s" % submission.id
    header = "Store | Quantity\n------|---------\n"

    for stock in stocks:
        header += " " + stock[0] + " | " + str(stock[1]) + "\n"

    reply = header + get_base_submission()

    submission.reply(reply)


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
