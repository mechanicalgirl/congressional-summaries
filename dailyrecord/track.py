from datetime import datetime

from flask import abort
from ua_parser import user_agent_parser

from dailyrecord.db import get_db
from dailyrecord.extensions import cache


def capture(request_headers, request_url):
    user_agent = request_headers.get('User-Agent', '')
    ua_dict = user_agent_parser.Parse(user_agent)
    ua_dict['referer'] = request_headers.get('Referer')
    ua_dict['request_url'] = request_url

    disallowed_agents, disallowed_strs, disallowed_paths = get_disallowed()

    blocked = (
        ua_dict['user_agent']['family'] in disallowed_agents or
        any(b in ua_dict['string'] for b in disallowed_strs) or
        any(b in ua_dict['request_url'] for b in disallowed_paths)
    )
    simple_tracking(ua_dict, blocked=blocked)
    if blocked:
        abort(401)

@cache.cached(timeout=1200, key_prefix='blocklist')
def get_disallowed():
    db = get_db()
    disallowed_request = db.execute("SELECT value, block_type FROM blocklist", ()).fetchall()
    disallowed_agents = [d['value'] for d in disallowed_request if d['block_type'] == 'ua_agent']
    disallowed_strs = [d['value'] for d in disallowed_request if d['block_type'] == 'ua_string']
    disallowed_paths = [d['value'] for d in disallowed_request if d['block_type'] == 'path']
    return disallowed_agents, disallowed_strs, disallowed_paths

def simple_tracking(ua_dict, blocked):
    insert_query = ("INSERT INTO track (ua, device, os, browser, referer, url, blocked, request_date) "
                    "VALUES(?, ?, ?, ?, ?, ?, ?, ?) "
                    "RETURNING id;")
    try:
        db = get_db()
        track_insert = db.execute(insert_query, (
            ua_dict['string'],
            str(ua_dict['device']),
            str(ua_dict['os']),
            str(ua_dict['user_agent']),
            str(ua_dict['referer']),
            str(ua_dict['request_url']),
            blocked,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )).fetchone()
        ua_id = track_insert['id']
        db.commit()
    except Exception as e:
        print(e)
