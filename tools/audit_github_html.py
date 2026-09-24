# SPDX-License-Identifier: GPL-3.0-or-later
"""Inspect saved anonymous HTML + optional saved headers. NO NETWORK requests.
This cannot determine whether Google indexed a page or whether an account is flagged.
"""
import argparse
from html.parser import HTMLParser
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

class AuditParser(HTMLParser):
    def __init__(self,host):
        super().__init__(convert_charrefs=True);self.host=host;self.meta=[];self.links=[];self.canonical=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='meta' and d.get('name','').lower() in ('robots','googlebot','bingbot'):
            self.meta.append({'name':d['name'],'content':d.get('content','')})
        if tag=='link' and 'canonical' in d.get('rel','').lower().split():self.canonical.append(d.get('href',''))
        if tag=='a':
            href=d.get('href','')
            try:host=(urlsplit(href).hostname or '').lower()
            except ValueError:return
            if host in {self.host,'www.'+self.host}:
                self.links.append({'href':href,'rel':d.get('rel',''),'nofollow':'nofollow' in d.get('rel','').lower().split()})

def audit(html,headers,host):
    p=AuditParser(host);p.feed(html)
    h={str(k).lower():v for k,v in (headers or {}).items()}
    robot_header=h.get('x-robots-tag','')
    values=[x['content'] for x in p.meta]+([str(robot_header)] if robot_header else [])
    noindex=any(re.search(r'\b(?:noindex|none)\b', v, re.IGNORECASE) for v in values)
    return {'robots_meta':p.meta,'x_robots_tag':robot_header or ('ABSENT_IN_SAVED_HEADERS' if headers is not None else 'HEADERS_NOT_PROVIDED'),
            'noindex_seen':noindex,'canonical':p.canonical,'website_links':p.links,
            'google_index_status':'UNKNOWN','account_restriction_status':'UNKNOWN',
            'note':'Anonymous snapshot only. No noindex does not guarantee crawling or indexing. A noindex tag does not identify its cause.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('html');p.add_argument('--headers',help='JSON object of response headers, not browser cookies');p.add_argument('--website-host',default='jrdelipack.com')
    a=p.parse_args()
    try:
        if Path(a.html).stat().st_size>8_000_000:raise ValueError('HTML exceeds 8 MB')
        text=Path(a.html).read_text(encoding='utf-8',errors='replace')
        headers=None
        if a.headers:
            if Path(a.headers).stat().st_size>64000:raise ValueError('headers file exceeds 64 KB')
            headers=json.loads(Path(a.headers).read_text(encoding='utf-8'))
            if not isinstance(headers,dict):raise ValueError('headers must be a JSON object')
        print(json.dumps(audit(text,headers,a.website_host.lower()),indent=2,ensure_ascii=False))
    except (OSError,ValueError) as e:
        p.exit(2,f'Error: {e}\n')
if __name__=='__main__':main()
