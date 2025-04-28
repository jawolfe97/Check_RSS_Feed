import itertools
import string
import feedparser
import os
from datetime import datetime, timedelta
import requests
from requests.exceptions import Timeout, RequestException
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import (
    ConnectionError, HTTPError, URLRequired, TooManyRedirects,
    SSLError, InvalidURL, InvalidSchema, MissingSchema
)

print(f"Imported Libraries")

# Set up a session with headers and retry strategy
session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )
})
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    backoff_factor=1
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# -------------------------------------------
# Set working directory to the script's folder
# -------------------------------------------
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# -------------------------------------------
# Load keywords from Keywords.txt
# (Each keyword is stripped and converted to lowercase)
# -------------------------------------------
def load_keywords(filename):
    with open(filename, 'r') as file:
        return [line.strip().lower() for line in file.readlines()]

keywords = load_keywords('Keywords.txt')

# -------------------------------------------
# Define Feed Keyword Check (Handles ATOM)
# -------------------------------------------
def check_feed_for_keywords(feed, keywords):
    combined_feed_text = ""
    for entry in feed.entries:
        title = entry.get('title', '').lower()
        summary = entry.get('summary', '')
        if not summary:
            content_list = entry.get('content', [])
            if content_list and isinstance(content_list, list):
                summary = content_list[0].get('value', '')
        combined_feed_text += title + " " + summary.lower() + " "
    return any(keyword in combined_feed_text for keyword in keywords)

# -------------------------------------------
# Prepare output file with timestamped filename
# -------------------------------------------
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
output_filename = f"Relevant_Journals_{timestamp}.txt"
print(f"Environment Setup")

# -------------------------------------------
# Read all RSS feed URLs and journal names from Feeds.txt
# Format per line: Journal Name - RSS URL
# -------------------------------------------


feed_count = 0
relevant_feed_count = 0
grand_total_entries = 0
count = 0


# -------------------------------------------
# Open output file and begin processing each feed
# -------------------------------------------
with open(output_filename, 'w', encoding='utf-8') as output_file:
    L = 3
    for letters in itertools.product(string.ascii_lowercase, repeat=L):
        CODE = ''.join(letters)
        feed_url = f'https://journals.sagepub.com/action/showFeed?ui=0&mi=ehikzz&ai=2b4&jc={CODE}&type=etoc&feed=rss'

        count += 1
        feed_count += 1

        # -------------------------------------------
        # Access Feeds
        # -------------------------------------------
        try:
            response = session.get(feed_url, timeout=2)
            if response.status_code == 403:
                # Fallback: fetch with feedparser (since access is denied)
                feed = feedparser.parse(feed_url)
            else:
                response.raise_for_status()
                feed = feedparser.parse(response.content)  # <--- use .content (bytes) for better accuracy

            # -------------------------------------------
            # Parse Feed and Write Journals
            # -------------------------------------------
            total_entries = len(feed.entries)
            grand_total_entries += total_entries

            feed_type = feed.version
            if feed_type and 'atom' in feed_type.lower():
                pass  # Skip ATOM feeds (instead of continue)

            if feed.bozo:
                pass  # Skip feeds with bozo errors (instead of continue)

            if check_feed_for_keywords(feed, keywords):
                relevant_feed_count += 1
                output_file.write(f"{CODE} - {feed_url}\n")
            else:
                pass  # Skip feeds with no relevant keywords

        except Timeout:
            #print(f"Timeout Error for {CODE} - {feed_url}")
            continue
        except ConnectionError:
            #print(f"Connection Error for {CODE} - {feed_url}")
            continue
        except SSLError:
            #print(f"SSL Error for {CODE} - {feed_url}")
            continue
        except (InvalidURL, MissingSchema, InvalidSchema, URLRequired):
            #print(f"Invalid URL Error for {CODE} - {feed_url}")
            continue
        except TooManyRedirects:
            #print(f"Too Many Redirects for {CODE} - {feed_url}")
            continue
        except HTTPError as e:
           #print(f"HTTP Error for {CODE} - {feed_url}: {e.response.status_code}")
            continue
        except RequestException as e:
            #print(f"Request Error for {CODE} - {feed_url}: {str(e)}")
            continue
        except Exception as e:
            #print(f"General Error for {CODE} - {feed_url}: {str(e)}")
            continue

        if count % 50 == 0:
            print(f"{count} / {26**L} processed")

# -------------------------------------------
# Write Summary File
# -------------------------------------------
with open(output_filename, 'a', encoding='utf-8') as output_file:
    output_file.write("=" * 7 + "\nSummary\n")
    output_file.write("=" * 7 + "\n")
    output_file.write(f"Total Feeds Processed: {feed_count}\n")
    output_file.write(f"Total Relevant Feeds: {relevant_feed_count}\n")
    output_file.write(f"Total Entries Checked: {grand_total_entries}\n")
    output_file.write(f"Feeds checked at {timestamp} EST\n")
    output_file.write(f"Disclaimer: Inaccessible feeds and feeds without relevant posts are removed for clarity, this is not a comprehensive list :)")

print(f"\nResults written to {output_filename}")
