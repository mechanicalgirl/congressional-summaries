import anthropic
import requests

from datetime import date
import os
import sys
import time
from urllib.parse import urljoin

API_URL = "https://api.congress.gov/"
API_VERSION = "v3"
DIR_PATH = os.path.join(os.getcwd(), 'summaries')
X_API_KEY = os.getenv("X_API_KEY")

def get_daily_record_meta():
    api_url = urljoin(API_URL, API_VERSION) + "/"
    headers = {"format": "json", "x-api-key": X_API_KEY}
    metadata_path = 'daily-congressional-record'
    r = requests.get(api_url + metadata_path, headers=headers)
    response = r.json()
    metadata = {
        'congress': response['dailyCongressionalRecord'][0]['congress'],
        'issueDate': response['dailyCongressionalRecord'][0]['issueDate'],
        'issueNumber': response['dailyCongressionalRecord'][0]['issueNumber'],
        'sessionNumber': response['dailyCongressionalRecord'][0]['sessionNumber'],
        'url': response['dailyCongressionalRecord'][0]['url'],
        'volumeNumber': response['dailyCongressionalRecord'][0]['volumeNumber']
    }
    # print(f"Metadata: {metadata}")
    return metadata

def get_daily_article_urls(d):
    urls = []
    api_url = urljoin(API_URL, API_VERSION) + "/"
    headers = {"format": "json", "x-api-key": X_API_KEY}
    articles_path = f"daily-congressional-record/{d['volumeNumber']}/{d['issueNumber']}/articles"
    r = requests.get(api_url + articles_path, headers=headers)
    response = r.json()
    pag_count = response['pagination']['count']
    offset = 0
    while offset < pag_count:
        path = f"daily-congressional-record/{d['volumeNumber']}/{d['issueNumber']}/articles?offset={offset}&limit=20"
        r = requests.get(api_url + path, headers=headers)
        resp = r.json()
        for a in resp['articles']:
            section = a['name']
            for b in a['sectionArticles']:
                title = b['title']
                url = [x['url'] for x in b['text'] if x['type'] == 'Formatted Text'][0]
                urls.append({'section': section, 'title': title, 'url': url})
        offset = offset+20
    return urls

def get_article_text(article):
    r = requests.get(article['url'])
    return article['section'] + ': ' + article['title'] + '\n\n' + r.text

def split_oversized(text, max_size=200_000):
    """Last resort: split by character count, trying to break on paragraph boundaries."""
    chunks = []
    while len(text) > max_size:
        # Try to find a paragraph break near the limit
        split_at = text.rfind('\n\n', 0, max_size)
        if split_at == -1:
            split_at = text.rfind('\n', 0, max_size)
        if split_at == -1:
            split_at = max_size  # hard cut if no newlines found
        chunks.append(text[:split_at])
        text = text[split_at:]
    if text:
        chunks.append(text)
    return chunks

def clean_digest(text, max_size=200_000):
    text = text.replace('<pre>', '').replace('</pre>', '').replace('&#x27;', "'")
    text = text.replace('  ', ' ').replace('  ', ' ').replace('  ', ' ')
    text = text.replace("From the Congressional Record Online through the Government Publishing Office [<a href='https://www.gpo.gov'>www.gpo.gov</a>]", '')

    chunks = []
    for section in text.split('____________________'):
        section = section.replace('\n', '')
        if not section:
            continue

        if len(section) > max_size:
            for subsection in section.split('______'):
                if not subsection:
                    continue
                if len(subsection) > max_size:
                    chunks.extend(split_oversized(subsection, max_size))
                else:
                    chunks.append(subsection)
        else:
            chunks.append(section)

    # Greedy bin-packing (unchanged from before)
    bins = []
    current_bin = []
    current_size = 0

    for chunk in chunks:
        chunk_size = len(chunk)
        if current_size + chunk_size <= max_size:
            current_bin.append(chunk)
            current_size += chunk_size
        else:
            if current_bin:
                bins.append('\n'.join(current_bin))
            current_bin = [chunk]
            current_size = chunk_size
    
    if current_bin:
        bins.append('\n'.join(current_bin))
    
    return bins

def summarize(text, bin_index, total_bins):
    """Summarize article using Claude"""
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",  # approx. cost .20-.30 per day
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"You are summarizing section {bin_index} of {total_bins} sections of a Congressional Record digest. Each section will be combined into a single document, so write as if the reader has general knowledge of current Congressional activity but may not have read the previous sections. Summarize in 1-2 concise paragraphs with no headers, titles, or markdown formatting. Begin your response directly with the first sentence of the summary.\n\n{text[:200000]}"
        }]
    )
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens
    text = message.content[0].text
    return text

def main():
    daily = get_daily_record_meta()
    digest_url = f"https://www.congress.gov/congressional-record/volume-{daily['volumeNumber']}/issue-{daily['issueNumber']}/daily-digest"

    article_urls = get_daily_article_urls(daily)
    all_articles = []
    for a in article_urls:
        article_text = get_article_text(a)
        all_articles.append(article_text)
    raw_text = '\n'.join(all_articles)

    """
    # for local testing:
    with open('text.txt', 'r') as f:
        raw_text = f.read()
    """
    summaries = []
    bins = clean_digest(raw_text)
    for i, bin_text in enumerate(bins):
        print(f"Bin {i+1}: {len(bin_text)} chars")
        response = summarize(bin_text, i+1, len(bins))
        summary = response.strip()
        summary = '\n'.join(line for line in summary.split('\n') 
                    if not line.startswith('# ')).strip()
        print(summary, '\n')
        time.sleep(60)
        summaries.append(summary)
    digest = '\n\n'.join(summaries)

    today = date.today().strftime("%Y-%m-%d")
    filepath = f"{DIR_PATH}/{today}.md"
    os.makedirs(DIR_PATH, exist_ok=True)
    with open(f"{DIR_PATH}/{today}.md", 'w') as f:
        header = f"# Congressional Summary - {today}\n\n"
        f.write(header)
        if digest:
            f.write(f"[{digest_url}]({digest_url})\n\n")
            f.write(f"{digest}\n\n")
        else:
            f.write("---\n\n")
            f.write(f"No summaries for {today}\n\n")
    print(f"File written. Size: {os.path.getsize(filepath)} bytes")

if __name__ == "__main__":
    main()
