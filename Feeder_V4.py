import feedparser
import os
from datetime import datetime, timedelta
import requests  # Import the requests module
from requests.exceptions import Timeout, RequestException

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
# Define Feed Keyword Check
# -------------------------------------------
def check_feed_for_keywords(feed, keywords):
    # Combine titles and summaries of all entries in the feed
    combined_feed_text = ""
    for entry in feed.entries:
        combined_feed_text += entry.get('title', '').lower() + " "
        combined_feed_text += entry.get('summary', '').lower() + " "
    
    # Check if any keyword is in the combined text
    for keyword in keywords:
        if keyword in combined_feed_text:
            return True  # Feed contains the keyword

    return False  # Feed does not contain any keyword

# -------------------------------------------
# Define cutoff datetime (7.5 days ago from now)
# Only articles newer than this will be considered
# -------------------------------------------
X = 30
cutoff = datetime.now() - timedelta(days=X)

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
# Store the number of valid feeds
N_Feeds = len(feed_lines)
# Initialize counters
feed_count = 0
relevant_feed_count = 0
grand_total_entries = 0
grand_total_relevant_entries = 0
count = 0

# -------------------------------------------
# Open output file and begin processing each feed
# -------------------------------------------
header = f"Pet News\nFrom the last {X} Days\n"

with open(output_filename, 'w', encoding='utf-8') as output_file:
    output_file.write(header)
    for line in feed_lines:
        if ' - ' not in line:
            output_file.write("=" * len(line) + "\n" + line + "\n" + "=" * len(line) + "\n")
            continue  # Skip malformed lines

        count = count + 1
        journal, feed_url = line.split(' - ', 1)
        feed_count += 1  # Increment feed counter

        output_file.write("-" * 105 + "\n")
        output_file.write(f"Source: {journal}\n")
        output_file.write("Titles:\n")

        try:
            # Fetch feed with timeout using requests
            response = requests.get(feed_url, timeout=5)  # 5 seconds timeout
            response.raise_for_status()  # Raises an HTTPError for bad responses
            feed = feedparser.parse(response.text)  # Parse the content with feedparser
            total_entries = len(feed.entries)
            grand_total_entries += total_entries

            if check_feed_for_keywords(feed, keywords):
                relevant_feed_count = relevant_feed_count + 1
                for entry in feed.entries:
                    title = entry.get('title', 'No Title').strip()
                    description = entry.get('description', '').strip()
                    updated_parsed = entry.get('updated_parsed')

                    if updated_parsed:
                        entry_datetime = datetime(*updated_parsed[:6])

                        if entry_datetime >= cutoff:
                            combined_text = (title + ' ' + description).lower()
                            if any(keyword in combined_text for keyword in keywords):
                                output_file.write(f"- {title}\n")
                                grand_total_relevant_entries = grand_total_relevant_entries + 1
                output_file.write("-" * 105 + "\n")
            else:
                output_file.write("-" * 105 + "\n")

        except Timeout:
            output_file.write(f"Unable to Access Feed (Timeout)\n")
            output_file.write("-" * 105 + "\n")
            #print(f"Timeout error processing {journal}")
        except RequestException as e:
            output_file.write(f"Unable to Access Feed (Request Error)\n")
            output_file.write("-" * 105 + "\n")
            #print(f"Request error processing {journal}: {e}")
        except Exception as e:
            output_file.write(f"Unable to Access Feed (General Error)\n")
            output_file.write("-" * 105 + "\n")
            #print(f"Error processing {journal}: {e}")

        # Print progress every 50 feeds
        if count % 50 == 0:
            print(f"{count} / {N_Feeds}")
        else:
            continue

    # -------------------------------------------
    # Write summary of total feeds and entries processed
    # -------------------------------------------
    output_file.write("=" * 7 + "\n" +"Summary\n")
    output_file.write("=" * 7 + "\n")
    output_file.write(f"Total Feeds Processed: {feed_count}\n")
    output_file.write(f"Total Relevant Feeds: {relevant_feed_count}\n")
    output_file.write(f"Total Entries Checked: {grand_total_entries}\n")
    output_file.write(f"Total Relevant Entries: {grand_total_relevant_entries}\n")

print(f"\nResults written to {output_filename}")
