from datetime import datetime, timezone
import json
import math
import os
import sys

from feedgen.feed import FeedGenerator
from flask import (
    Blueprint, render_template, request, Response
)
import markdown

from dailyrecord.track import capture


bp = Blueprint('blog', __name__)
DIR_PATH = os.path.join(os.getcwd(), 'summaries')
PAGE_COUNT = 10

def pagination():
    digest_count = sum(1 for entry in os.listdir(DIR_PATH) if os.path.isfile(os.path.join(DIR_PATH, entry)))
    total = math.ceil(digest_count/PAGE_COUNT)
    page_list = [int(a) for a in range(1, total+1, 1)]
    return page_list

@bp.route('/')
def index():
    capture(request.headers.get('User-Agent'))
    page_list = pagination()

    files = sorted(os.listdir(DIR_PATH), reverse=True)
    digests = files[0:PAGE_COUNT]

    entries = []
    for d in digests:
        digest_date = d.split('.')[0]
        entry = {}
        entry['title'] = f"Congressional Daily Record for {digest_date}"
        entry['slug'] = f"/digest/{digest_date}"
        entry['date'] = digest_date
        entries.append(entry)

    return render_template('blog/index.html', digests=entries, pagination=page_list)

@bp.route('/digest/<digest_date>/')
def digest(digest_date):
    capture(request.headers.get('User-Agent'))
    page_list = pagination()

    with open(f"{DIR_PATH}/{digest_date}.md", 'r') as f:
        digest_body = f.read()

    entry = {}
    entry['title'] = f"Congressional Daily Record for {digest_date}"
    entry['date'] = digest_date
    entry['body']  = markdown.markdown(digest_body)
    return render_template('blog/digest.html', entry=entry)

@bp.route('/pages/<int:page_number>/')
def pages(page_number):
    capture(request.headers.get('User-Agent'))
    page_list = pagination()

    files = sorted(os.listdir(DIR_PATH), reverse=True)
    digests = files[(page_number-1)*PAGE_COUNT:][0:PAGE_COUNT]

    entries = []
    for d in digests:
        digest_date = d.split('.')[0]
        entry = {}
        entry['title'] = f"Congressional Daily Record for {digest_date}"
        entry['slug'] = f"/digest/{digest_date}"
        entry['date'] = digest_date
        entries.append(entry)

    return render_template('blog/index.html', digests=entries, pagination=page_list)

@bp.route('/rss')
def rss():
    fg = FeedGenerator()
    fg.id('https://www.congress-daily.com')
    fg.title('Summary of the Congressional Daily Record')
    fg.author({'name':'congress-daily.com','email':'digest@congress-daily.com'})
    fg.link(href='https://www.congress-daily.com/rss', rel='alternate')
    fg.subtitle('RSS feed from congress-daily.com')
    fg.language('en')

    files = sorted(os.listdir(DIR_PATH), reverse=True)
    digests = files[0:10]

    entries = []
    for d in digests:
        digest_date = d.split('.')[0]
        with open(f"{DIR_PATH}/{digest_date}.md", 'r') as f:
            digest_body = f.read()
        entry = {}
        entry['title'] = f"Congressional Daily Record for {digest_date}"
        entry['slug'] = f"digest/{digest_date}"

        datetime_obj = datetime.strptime(digest_date, '%Y-%m-%d')
        datetime_obj = datetime_obj.replace(tzinfo=timezone.utc)
        entry['date'] = datetime_obj

        entry['body']  = markdown.markdown(digest_body)
        entries.append(entry)

    for e in entries:
        fe = fg.add_entry(order="append")
        fe.id()
        fe.title(e['title'])
        fe.guid(e['slug'])
        fe.link(href=f"https://www.congress-daily.com/{e['slug']}")
        fe.description(e['title'])
        fe.content(e['body'], type='html')
        fe.published(e['date'])

    fg.rss_file('rss.xml')
    rssfeed = fg.rss_str()
    return Response(fg.rss_str(), mimetype='application/rss+xml')

