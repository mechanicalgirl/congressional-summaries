import anthropic
import requests

from datetime import date
import os
import sys
from urllib.parse import urljoin

API_URL = "https://api.congress.gov/"
API_VERSION = "v3"
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

def summarize(text):
    """Summarize article using Claude"""
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",  # approx. cost .20-.30 per day
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"Summarize this digest of events in 10-15 concise paragraphs:\n\n{text}"
        }]
    )
    return {
        'text': message.content[0].text,
        'input_tokens': message.usage.input_tokens,
        'output_tokens': message.usage.output_tokens
    }

def main():
    daily = get_daily_record_meta()
    digest_url = f"https://www.congress.gov/congressional-record/volume-{daily['volumeNumber']}/issue-{daily['issueNumber']}/daily-digest"
    article_urls = get_daily_article_urls(daily)
    all_articles = []
    for a in article_urls:
        article_text = get_article_text(a)
        all_articles.append(article_text)
    digest = '\n'.join(all_articles)
    summary = summarize(digest)

    today = date.today().strftime("%Y-%m-%d")
    filepath = f"summaries/{today}.md"
    os.makedirs('summaries', exist_ok=True)
    with open(f"summaries/{today}.md", 'w') as f:
        header = f"# Congressional Summary - {today}\n\n"
        f.write(header)
        if summary:
            f.write(f"{digest_url}\n\n")
            f.write(f"{summary['text']}\n\n")
            f.write(f"Input: {summary['input_tokens']}, Output: {summary['output_tokens']}\n\n")
        else:
            f.write("---\n\n")
            f.write(f"No summaries for {today}\n\n")
    print(f"File written. Size: {os.path.getsize(filepath)} bytes")

if __name__ == "__main__":
    main()
