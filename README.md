# Check_RSS_Feed

The following files serve the following general functions:

Feeder.py - Using an existing list of working and relevant links to RSS feeds and a list of keywords, return the relevant posts from each feed and compile statistics.

Screener.py - Using an existing list of links to RSS feeds and a list of keywords, return the relevant feeds and compile statistics. Used to build Feeds.txt file for Feeder.py

Finder.py - Using a family of links to RSS feeds defined by a set alphanumberic pattern,  brute-force check every possible patern as fast as possible with multi-threading and return the relevant feeds and compile statistics. Used to build Feeds.txt file for Screener.py
