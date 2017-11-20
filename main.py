import praw
import os


def setup_bot():
	reddit = praw.Reddit('mc_bot')
	subreddit = reddit.subreddit("StockCheckerTesting")
	pass


if __name__=="__main__":
	setup_bot()
