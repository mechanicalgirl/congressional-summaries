from feedgen.feed import FeedGenerator
import markdown

from datetime import datetime, timezone


today = datetime.now().strftime('%Y-%m-%d')
todaysfile = f"summaries/{today}.md"

count = 0
url = ''
title = ''
body = ''
with open(todaysfile, 'r') as file:
    for line in file:
        count += 1
        if count == 3:
            url += line.strip()
        if count == 5:
            title += line.strip()
        if count >= 7:
            body += line.strip()+'\n'
        # print("Line{}: {}".format(count, line.strip()))

content = markdown.markdown(body)
datetime_obj = datetime.strptime(today, '%Y-%m-%d')
datetime_obj = datetime_obj.replace(tzinfo=timezone.utc)
title = title.replace('# ', '')

fg = FeedGenerator()
fg.id('http://bloodredrose.com/congressional-summaries.github.io/rss.xml')
fg.title('Congressional Daily Record')
fg.author({'name':'Barbara','email':'barbara@mechanicalgirl.com'})
fg.link(href='http://bloodredrose.com/congressional-summaries.github.io/rss.xml', rel='alternate')
fg.subtitle('RSS feed from congressional-summaries.github.io/')
fg.language('en')

fe = fg.add_entry(order="append")
fe.id()
fe.title(title)
fe.guid(url)
fe.link(href=url)
fe.description(title)
fe.content(content, type='html')
fe.published(datetime_obj)

fg.rss_file('index.xml')
rssfeed = fg.rss_str()

