"""Run with python tests/test_processing_status.py; no network required."""
import copy
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import processing_status as p


def check():
    parser = p.DateLinks()
    parser.feed('<a href="/rumail.ru.ac.th/1-2569/tapes/21969"><span>21/9/69</span></a>'
                '<a href="https://example.org/21969">21/9/69</a>')
    assert len(parser.links) == 1
    key = 'qoDYh_8_Ls0'
    item = dict(videoId=key, subject='POL3128', classDate='2026-09-21')
    data = dict(attempts=[], scan=dict(checkedAt=p.now(), remaining=[item]))
    a = p.start(data, key)
    try:
        p.start(data, key)
        raise AssertionError('Concurrent start accepted')
    except ValueError:
        pass
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'processing-status.json'
        old = dict(version=1, attempts=[], scan=dict(checkedAt=p.now(), remaining=[item]))
        path.write_text(json.dumps(old), encoding='utf-8')
        with patch.object(p, 'PATH', path), patch.object(p, 'snapshot', side_effect=ValueError('offline')), \
                patch.object(sys, 'argv', ['processing_status.py', 'scan']):
            try:
                p.main()
                raise AssertionError('Failed scan reported success')
            except SystemExit as exc:
                assert exc.code == 1
        saved = json.loads(path.read_text(encoding='utf-8'))
        assert saved['scan'] == old['scan'] and saved['scanError']
    p.finish(data, a['id'], 'failed')
    p.finish(data, a['id'], 'failed')
    b = p.start(data, key)
    assert a['id'] != b['id'] and len(data['attempts']) == 2
    with patch.object(p, 'snapshot', return_value=dict(remaining=[item])):
        try:
            p.finish(data, b['id'], 'succeeded')
            raise AssertionError('Unpublished success accepted')
        except ValueError:
            pass
    assert b['status'] == 'running'
    with patch.object(p, 'snapshot', return_value=dict(remaining=[])), patch.object(p, 'fetch',
          side_effect=[json.dumps(dict(lectures=[dict(sourceUrl='https://youtu.be/' + key,
                                                    summaryPath='classes/x/lecture-summary.txt')])), 'summary']):
        p.finish(data, b['id'], 'succeeded')
    a['startedAt'] = '2026-09-30T16:59:59+00:00'
    b['startedAt'] = '2026-09-30T17:00:00+00:00'
    assert p.counts(data, '2026-09-30') == dict(succeeded=0, failed=1, running=0, total=1)
    assert p.counts(data, '2026-10-01') == dict(succeeded=1, failed=0, running=0, total=1)
    assert p.counts(data, '2026-10-02')['total'] == 0
    bad = copy.deepcopy(data)
    bad['scanError'] = {'at': p.now()}
    try:
        p.start(bad, key)
        raise AssertionError('Incomplete scan accepted')
    except ValueError:
        pass
    # Test full discovery: fresh embedded IDs, explicit titles and live publication.
    archive = '<a href="/rumail.ru.ac.th/1-2569/tapes/21969">21/9/69</a>'
    page = '<iframe src="https://www.youtube.com/embed/' + key + '"></iframe>'
    responses = {p.ARCHIVE: archive, p.ARCHIVE + '/tapes/21969': page,
                 p.SITE + 'data/site-index.json': '{"lectures":[]}'}
    with patch.object(p, 'fetch', side_effect=lambda url: responses[url]), patch.object(
            p, 'fetch_youtube_title', return_value='POL3128 21/09/69'):
        scan = p.snapshot()
        assert scan['datePages'] == 1 and scan['remaining'][0]['videoId'] == key
    with patch.object(p, 'fetch', side_effect=lambda url: responses[url]), patch.object(
            p, 'fetch_youtube_title', return_value='POL3128 22/09/69'):
        try:
            p.snapshot()
            raise AssertionError('Mismatched date accepted')
        except ValueError:
            pass
    print('processing status checks passed')


if __name__ == '__main__':
    check()
