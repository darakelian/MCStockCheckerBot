import praw
import os
import re
import json
import urllib2


reddit = None
subreddit = None
posts_replied_to = []


def setup_bot():
	global reddit, subreddit, posts_replied_to
	
	reddit = praw.Reddit('mc_bot')
	subreddit = reddit.subreddit("StockCheckerTesting")
	
	if not os.path.isfile("posts_replied_to.txt"):
		post_replied_to = []
	else:
		with open("posts_replied_to.txt", "r") as f:
			posts_replied_to = f.read()
			posts_replied_to = posts_replied_to.split()


def start_searching():
	for submission in subreddit.new(limit=10):
		if submission.id not in posts_replied_to:
			#  only operate on links that are pointed to microcenter.com
			if re.search("microcenter.com", submission.url, re.IGNORECASE):
				#  travel to the link and start parsing
				print "navigating to %s" % submission.url
				try:
					page = urllib2.urlopen(submission.url)
				except:
					reply_with_error(submission, "urlerror")
				stocks = get_stock(page)
				reply_stocks(submission, stocks)
	pass


def get_stock(page_object):
	raw_html = page_object.read()
	#  Extract stock from javascript
	stock_json = re.search("(?<=inventory = )(.*)", raw_html).group(0).strip()
	stocks = json.loads(stock_json)
	
	#  Return the stocks as tuples
	return [(x["storeName"], x["qoh"]) for x in stocks]


def reply_stocks(submission, stocks):
	header = """|Store | Quantity|\n
				|------|---------|\n"""
	for stock in stocks:
		header += "|"+stock[0]+"|"+str(stock[1])+"|\n"
	
	reply = header + get_base_submission()
	
	submission.reply(reply)


def reply_with_error(submission, errortype):
	if errortype == "urlerror":
		submission.reply("I was unable to find stock information for this page.  " + get_base_submission())


def get_base_submission():
	return """This bot was created by /u/hiloser12221  
			source code [here](https://github.com/darakelian/MCStockCheckerBot) report errors [here](https://vec3d.xyz/projects/reporterror)
			"""



if __name__=="__main__":
	setup_bot()
	start_searching()
