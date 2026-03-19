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

def pagination():
    digest_count = sum(1 for entry in os.listdir(DIR_PATH) if os.path.isfile(os.path.join(DIR_PATH, entry)))
    print("COUNT", digest_count)
    total = math.ceil(digest_count/20)
    page_list = [int(a) for a in range(1, total+1, 1)]
    return page_list

@bp.route('/')
def index():
    capture(request.headers.get('User-Agent'))
    page_list = pagination()

    files = sorted(os.listdir(DIR_PATH), reverse=True)
    digests = files[0:20]

    entries = []
    for d in digests:
        digest_date = d.split('.')[0]
        entry = {}
        entry['title'] = f"Congressional Daily Record for {digest_date}"
        entry['slug'] = f"/digest/{digest_date}"
        entry['date'] = digest_date
        entries.append(entry)

    return render_template('blog/index.html', digests=entries)

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

@bp.route('/pages/<page_number>/')
def pages(page_number):
    capture(request.headers.get('User-Agent'))
    page_list = pagination()
    db = get_db()

    total = len(page_list) * 20
    ids = total - ((int(page_number) * 20) - 20)

    page_query = f"SELECT * FROM digest WHERE id <= {ids} ORDER BY created_at DESC LIMIT 20"
    digests = db.execute(page_query).fetchall()

    entries = []
    for p in digests:
        entry = {}
        entry['title'] = p['title']
        entry['slug'] = p['slug']
        entry['body_snippet'] = remove_html_tags(p['body'])[0:100]
        entry['date'] = p['created_at'][0:10]
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

