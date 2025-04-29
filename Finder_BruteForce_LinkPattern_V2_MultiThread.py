import feedparser
import os
import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import *
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Setup output directory and session
os.chdir(os.path.dirname(os.path.abspath(__file__)))

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

# Load keywords
with open('Keywords.txt', 'r') as f:
    keywords = [line.strip().lower() for line in f if line.strip()]

# Thread-safe counters
lock = Lock()
total_attempted = 0
total_processed = 0
total_relevant = 0
total_entries = 0

# Timestamped output file
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
output_filename = f"Relevant_Journals_{timestamp}.txt"
output_lines = []

# Generate 8-digit numeric codes starting with 0 or 1
def generate_codes():
    for i in range(0, 200_000_000):
        code = f"{i:08d}"
        if code[0] in ('0', '1'):
            yield code

# Keyword checker
def check_feed_for_keywords(feed):
    combined_text = " ".join(
        entry.get('title', '').lower() + " " +
        (entry.get('summary') or next((c.get('value', '') for c in entry.get('content', [])), '')).lower()
        for entry in feed.entries
    )
    return any(k in combined_text for k in keywords)

# Feed processor
def process_code(code):
    global total_attempted, total_processed, total_relevant, total_entries

    feed_url = f'https://journals.sagepub.com/action/showFeed?ui=0&mi=ehikzz&ai=2b4&jc={code}&type=etoc&feed=rss'
    with lock:
        total_attempted += 1
    try:
        response = session.get(feed_url, timeout=2)
        feed = feedparser.parse(response.content if response.status_code != 403 else feed_url)

        if feed.bozo or 'atom' in (feed.version or '').lower():
            return None

        entries = len(feed.entries)
        with lock:
            total_processed += 1
            total_entries += entries

        if check_feed_for_keywords(feed):
            with lock:
                total_relevant += 1
            return f"{code} - {feed_url}\n"

    except (Timeout, ConnectionError, SSLError, InvalidURL, MissingSchema, InvalidSchema, URLRequired,
            TooManyRedirects, HTTPError, RequestException):
        return None
    except Exception:
        return None

    return None

# Main logic
BATCH_SIZE = 1000
MAX_WORKERS = 15

def process_batches():
    global output_lines
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    futures = []
    batch = []

    for i, code in enumerate(generate_codes(), 1):
        batch.append(code)
        if len(batch) == BATCH_SIZE:
            futures = [executor.submit(process_code, b) for b in batch]
            for f in as_completed(futures):
                result = f.result()
                if result:
                    output_lines.append(result)
            batch = []
            print(f"Processed {i:,} codes so far...")

    # Final batch
    if batch:
        futures = [executor.submit(process_code, b) for b in batch]
        for f in as_completed(futures):
            result = f.result()
            if result:
                output_lines.append(result)

    executor.shutdown()

process_batches()

# Write output
with open(output_filename, 'w', encoding='utf-8') as out:
    out.writelines(output_lines)
    out.write("\n=======\nSummary\n=======\n")
    out.write(f"Total Feeds Attempted: {total_attempted}\n")
    out.write(f"Total Feeds Processed (non-bozo, non-ATOM): {total_processed}\n")
    out.write(f"Total Relevant Feeds: {total_relevant}\n")
    out.write(f"Total Entries Checked: {total_entries}\n")
    out.write(f"Checked at {timestamp} EST\n")
    out.write("Disclaimer: Inaccessible or irrelevant feeds are skipped for clarity. This is not a comprehensive list.\n")

print(f"\nResults written to {output_filename}")
