import os
import feedparser
from datetime import datetime

# Set the working directory to the folder containing the Python script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Function to load keywords from a file
def load_keywords(filename):
    with open(filename, 'r') as file:
        return [line.strip().lower() for line in file.readlines() if line.strip()]

# Load keywords from Keywords.txt
keywords = load_keywords('Keywords.txt')
keywords_present = len(keywords) > 0

# Function to process feed entries based on keywords
def process_feed(feed_url, keywords, keywords_present):
    feed = feedparser.parse(feed_url)
    entries = feed.entries
    matched_entries = []

    for entry in entries:
        title = entry.title
        summary = entry.summary if 'summary' in entry else ''
        published = entry.published if 'published' in entry else 'No date available'
        lower_title = title.lower()
        lower_summary = summary.lower()

        if not keywords_present:
            matched_entries.append((title, published))
        else:
            if any(kw in lower_title or kw in lower_summary for kw in keywords):
                matched_entries.append((title, published))

    return matched_entries

# Generate timestamp for the output filename
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
output_filename = f'Output_Feed_{timestamp}.txt'

# Write results to the timestamped file
with open(output_filename, 'w', encoding='utf-8') as output_file:
    with open('Feeds.txt', 'r') as file:
        for line in file:
            if ' - ' not in line:
                continue  # Skip lines that don't have expected format
            feed_name, feed_url = line.strip().split(' - ', 1)
            if feed_url:
                matched_entries = process_feed(feed_url, keywords, keywords_present)

                output_file.write(f"Source: {feed_name}\n")
                if matched_entries:
                    output_file.write("Entries:\n")
                    for title, published in matched_entries:
                        output_file.write(f"- {title} ({published})\n")
                else:
                    output_file.write("No matching entries found.\n")

                output_file.write('-' * 40 + '\n')

print(f"Results have been written to {output_filename}.")
