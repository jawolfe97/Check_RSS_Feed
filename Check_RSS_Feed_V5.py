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
# Set up a session with headers and retry strategy
session = requests.Session()
#session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; RSSChecker/1.0)"}) ###Can't Access Frontier Journals
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
# Define cutoff datetime (7.5 days ago from now)
# Only articles newer than this will be considered
# -------------------------------------------
cutoff = datetime.now() - timedelta(days=7.5)

# -------------------------------------------
# Prepare output file with timestamped filename
# -------------------------------------------
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
output_filename = f"Check_{timestamp}.txt"

# -------------------------------------------
# Read all RSS feed URLs and journal names from Feeds.txt
# Format per line: Journal Name - RSS URL
# -------------------------------------------
with open('Feeds.txt', 'r') as f:
    feed_lines = [line.strip() for line in f.readlines() if line.strip()]

N_Feeds = len(feed_lines)
feed_count = 0
relevant_feed_count = 0
grand_total_entries = 0
grand_total_relevant_entries = 0
count = 0

# -------------------------------------------
# Open output file and begin processing each feed
# -------------------------------------------

with open(output_filename, 'w', encoding='utf-8') as output_file:
    output_file.write(header)
    for line in feed_lines:
        if ' - ' not in line:
            output_file.write("=" * len(line) + "\n" + line + "\n" + "=" * len(line) + "\n")
            continue

        count += 1
        journal, feed_url = line.split(' - ', 1)
        feed_count += 1

        output_file.write("-" * 105 + "\n")
        output_file.write(f"Source: {journal}\n")
        output_file.write("Titles:\n")

        try:
            response = session.get(feed_url, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            total_entries = len(feed.entries)
            grand_total_entries += total_entries

            feed_type = feed.version
            if feed_type and 'atom' in feed_type.lower():
                output_file.write("Detected Feed Type: ATOM\n")
            else:
                output_file.write(f"Detected Feed Type: {feed_type or 'Unknown'}\n")

            if feed.bozo:
                output_file.write(f"⚠️ Feed Parsing Warning: {feed.bozo_exception}\n")

            if check_feed_for_keywords(feed, keywords):
                relevant_feed_count += 1
                for entry in feed.entries:
                    title = entry.get('title', 'No Title').strip()

                    description = entry.get('summary', '')
                    if not description:
                        content_list = entry.get('content', [])
                        if content_list and isinstance(content_list, list):
                            description = content_list[0].get('value', '')

                    entry_time_struct = entry.get('updated_parsed') or entry.get('published_parsed')
                    if entry_time_struct:
                        entry_datetime = datetime(*entry_time_struct[:6])
                        if entry_datetime >= cutoff:
                            combined_text = (title + ' ' + description).lower()
                            if any(keyword in combined_text for keyword in keywords):
                                output_file.write(f"- {title}\n")
                                grand_total_relevant_entries += 1
                output_file.write("-" * 105 + "\n")
            else:
                output_file.write("-" * 105 + "\n")

        except Timeout:
            output_file.write("Unable to Access Feed (Timeout)\n")
            output_file.write("-" * 105 + "\n")
        except ConnectionError:
            output_file.write("Unable to Access Feed (Connection Error)\n")
            output_file.write("-" * 105 + "\n")
        except SSLError:
            output_file.write("Unable to Access Feed (SSL Error)\n")
            output_file.write("-" * 105 + "\n")
        except (InvalidURL, MissingSchema, InvalidSchema, URLRequired):
            output_file.write("Unable to Access Feed (Invalid or Malformed URL)\n")
            output_file.write("-" * 105 + "\n")
        except TooManyRedirects:
            output_file.write("Unable to Access Feed (Redirect Loop Detected)\n")
            output_file.write("-" * 105 + "\n")
        except HTTPError as e:
            output_file.write(f"Unable to Access Feed (HTTP Error: {e.response.status_code})\n")
            output_file.write("-" * 105 + "\n")
        except RequestException as e:
            output_file.write(f"Unable to Access Feed (General Request Error: {str(e)})\n")
            output_file.write("-" * 105 + "\n")



        except Exception as e:
            output_file.write("Unable to Access Feed (General Error)\n")
            output_file.write("-" * 105 + "\n")

        if count % 50 == 0:
            print(f"{count} / {N_Feeds}")

    # -------------------------------------------
    # Write summary
    # -------------------------------------------
    output_file.write("=" * 7 + "\nSummary\n")
    output_file.write("=" * 7 + "\n")
    output_file.write(f"Total Feeds Processed: {feed_count}\n")
    output_file.write(f"Total Relevant Feeds: {relevant_feed_count}\n")
    output_file.write(f"Total Entries Checked: {grand_total_entries}\n")
    output_file.write(f"Total Relevant Entries: {grand_total_relevant_entries}\n")

print(f"\nResults written to {output_filename}")
