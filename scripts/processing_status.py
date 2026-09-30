#!/usr/bin/env python3
"""Live archive coverage and an explicit, per-attempt processing journal."""
import argparse
import concurrent.futures
import datetime as dt
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import uuid

from automation_state import video_id
from video_identity import fetch_youtube_title, title_class_date

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'data' / 'processing-status.json'
ARCHIVE = 'https://sites.google.com/rumail.ru.ac.th/1-2569'
SITE = 'https://vachio.github.io/youtube-class-notes/'
ALLOWED = {'POL3128', 'POL1101', 'POL2129', 'POL2107', 'POL3179', 'POL2100', 'POL2102'}
THAI = dt.timezone(dt.timedelta(hours=7))


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def fetch(url):
    request = urllib.request.Request(urllib.parse.quote(url, safe=':/?=&%'),
                                     headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode('utf-8-sig')


class DateLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = {}
        self.href = None
        self.text = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href')
            self.text = ''

    def handle_data(self, text):
        if self.href:
            self.text += text

    def handle_endtag(self, tag):
        if tag == 'a' and self.href:
            label = self.text.strip()
            url = urllib.parse.urljoin(ARCHIVE, self.href)
            if re.fullmatch(r'\d{1,2}/\d{1,2}/69', label) and url.startswith(ARCHIVE + '/'):
                self.links[url] = label
            self.href = None


def snapshot():
    links = DateLinks()
    links.feed(fetch(ARCHIVE))
    if not links.links:
        raise ValueError('No archive date pages found')

    def page(pair):
        url, date = pair
        ids = set(re.findall(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([\w-]{11})',
                             html.unescape(fetch(url))))
        return url, date, ids

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        pages = list(pool.map(page, links.links.items()))
    locations = {}
    for url, date, ids in pages:
        for key in ids:
            locations.setdefault(key, []).append((url, date))
    if not locations:
        raise ValueError('No embedded videos found')

    def identify(key):
        url = 'https://www.youtube.com/watch?v=' + key
        title = fetch_youtube_title(url)
        match = re.search(r'\bPOL\s*(\d{4})\b', title, re.I)
        subject = 'POL' + match[1] if match else None
        if subject not in ALLOWED:
            return None
        date = title_class_date(title)
        matches = [(u, d) for u, d in locations[key] if title_class_date(d) == date]
        if not date or not matches:
            raise ValueError(f'Archive/title date mismatch: {key} {title}')
        return dict(videoId=key, subject=subject, classDate=date, title=title,
                    url=url, archiveUrl=matches[0][0], archiveDateRaw=matches[0][1])

    # Unknown/private titles prevent a complete claim, including for unknown subjects.
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        videos = [item for item in pool.map(identify, sorted(locations)) if item]
    index = json.loads(fetch(SITE + 'data/site-index.json'))
    published = {video_id(x['sourceUrl']): x for x in index['lectures'] if x.get('sourceUrl')}

    def available(item):
        entry = published.get(item['videoId'])
        if not entry:
            return False
        path = entry['summaryPath']
        if not path.startswith('classes/') or '..' in path.split('/'):
            raise ValueError('Invalid published summary path')
        return bool(fetch(SITE + urllib.parse.quote(path)).strip())

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        ready = list(pool.map(available, videos))
    remaining = sorted([v for v, done in zip(videos, ready) if not done],
                       key=lambda v: (v['classDate'], v['subject'], v['videoId']))
    return dict(checkedAt=now(), datePages=len(pages), embeddedVideos=len(locations),
                allowedVideos=len(videos), remaining=remaining, sourceUrl=ARCHIVE)


def load():
    if PATH.exists():
        return json.loads(PATH.read_text(encoding='utf-8'))
    return dict(version=1, trackingStartedAt=now(), attempts=[], scan=None)


def save(data):
    data['updatedAt'] = now()
    temporary = PATH.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(PATH)


def start(data, key):
    if data.get('scanError') or not data.get('scan'):
        raise ValueError('A complete live scan is required before starting')
    age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(data['scan']['checkedAt'])
    if age.total_seconds() > 3600:
        raise ValueError('Live scan is older than one hour')
    if any(a['status'] == 'running' for a in data['attempts']):
        raise ValueError('Another attempt is running; resolve it before starting')
    item = next((v for v in data['scan']['remaining'] if v['videoId'] == key), None)
    if not item:
        raise ValueError('Video is not in the verified remaining queue')
    attempt = dict(id=uuid.uuid4().hex, videoId=key, subject=item['subject'],
                   classDate=item['classDate'], startedAt=now(), status='running')
    data['attempts'].append(attempt)
    return attempt


def finish(data, attempt_id, status):
    attempt = next((a for a in data['attempts'] if a['id'] == attempt_id), None)
    if not attempt:
        raise ValueError('Unknown attempt ID')
    if attempt['status'] != 'running':
        if attempt['status'] == status:
            return attempt  # Repeating finalization must not add another attempt.
        raise ValueError('Attempt already finalized')
    if status == 'succeeded':
        scan = snapshot()
        if any(v['videoId'] == attempt['videoId'] for v in scan['remaining']):
            raise ValueError('Summary is not published yet; keep attempt running')
        # A removed source is not evidence that processing succeeded.
        index = json.loads(fetch(SITE + 'data/site-index.json'))
        entry = next((v for v in index['lectures'] if video_id(v['sourceUrl']) == attempt['videoId']), None)
        if not entry or not fetch(SITE + urllib.parse.quote(entry['summaryPath'])).strip():
            raise ValueError('Published output not found')
        data['scan'] = scan
        data['scanError'] = None
    attempt.update(status=status, finishedAt=now())
    return attempt


def counts(data, day):
    attempts = [a for a in data['attempts']
                if dt.datetime.fromisoformat(a['startedAt']).astimezone(THAI).date().isoformat() == day]
    return {**{s: sum(a['status'] == s for a in attempts) for s in ('succeeded', 'failed', 'running')},
            'total': len(attempts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['scan', 'start', 'finish', 'show'])
    parser.add_argument('--video')
    parser.add_argument('--attempt')
    parser.add_argument('--status', choices=['succeeded', 'failed'])
    args = parser.parse_args()
    data = load()
    try:
        if args.command == 'scan':
            try:
                data['scan'] = snapshot()
                data['scanError'] = None
            except Exception:
                data['scanError'] = dict(at=now(), message='ตรวจแหล่งวิดีโอไม่ครบ กรุณาดูผลตรวจครั้งล่าสุด')
                save(data)
                raise
        elif args.command == 'start':
            if not args.video:
                parser.error('start requires --video')
            print(json.dumps(start(data, video_id(args.video)), ensure_ascii=False))
        elif args.command == 'finish':
            if not args.attempt or not args.status:
                parser.error('finish requires --attempt and --status')
            finish(data, args.attempt, args.status)
        if args.command != 'show':
            save(data)
        print(json.dumps(dict(scan=data['scan'], scanError=data.get('scanError'),
                              today=counts(data, dt.datetime.now(THAI).date().isoformat())), ensure_ascii=False, indent=2))
    except Exception as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    main()
