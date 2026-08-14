"""Offline tests for scrape.py.

All network access goes through a local threaded http.server fixture or
FakeFetch doubles; no test touches the real internet.
"""

import gzip as gzip_mod
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'scrape.py')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import scrape  # noqa: E402


# ── Local HTTP fixture ─────────────────────────────────────────────────
PAGE_HTML = (
    '<html><head><title>Local Test Page</title></head><body>'
    '<article><h1>Local Test Page</h1>'
    '<p>This is a locally served page used for offline testing of the scraper. '
    'It contains enough prose to look like real content.</p>'
    '<p>A second paragraph with a <a href="/about">link to about</a> inside.</p>'
    '</article></body></html>'
)
BIG_HTML = (
    '<html><head><title>Big Page</title></head><body><article>'
    + ('<p>' + 'lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 8 + '</p>') * 120
    + '</article></body></html>'
)
UTF16_HTML = (
    '<html><head><title>UTF16 页面</title></head>'
    '<body><article><p>这是 UTF-16 编码的测试页面内容, 用于验证 BOM 检测.</p>'
    '</article></body></html>'
).encode('utf-16')  # utf-16 codec prepends a BOM
BINARY_PAYLOAD = bytes(range(256)) * 4  # 1024 bytes, not valid gzip


def _raw_deflate(data: bytes) -> bytes:
    c = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    return c.compress(data) + c.flush()


class _Handler(BaseHTTPRequestHandler):
    base_b = ''  # set in setUpModule (second origin for cross-origin tests)

    def log_message(self, *args):
        pass

    def _send(self, body: bytes, status: int = 200,
              content_type: str = 'text/html; charset=utf-8', headers: dict = None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str):
        self.send_response(302)
        self.send_header('Location', location)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):  # noqa: N802 (stdlib naming)
        path = urllib.parse.urlparse(self.path).path
        if path == '/':
            self._send(PAGE_HTML.encode('utf-8'))
        elif path == '/gzip':
            self._send(gzip_mod.compress(PAGE_HTML.encode('utf-8')),
                       headers={'Content-Encoding': 'gzip'})
        elif path == '/deflate':
            self._send(zlib.compress(PAGE_HTML.encode('utf-8')),
                       headers={'Content-Encoding': 'deflate'})
        elif path == '/deflate-raw':
            self._send(_raw_deflate(PAGE_HTML.encode('utf-8')),
                       headers={'Content-Encoding': 'deflate'})
        elif path == '/utf16':
            self._send(UTF16_HTML)
        elif path == '/big':
            self._send(BIG_HTML.encode('utf-8'))
        elif path == '/gzip-big':
            self._send(gzip_mod.compress(BIG_HTML.encode('utf-8')),
                       headers={'Content-Encoding': 'gzip'})
        elif path == '/binary':
            self._send(BINARY_PAYLOAD, content_type='application/octet-stream')
        elif path == '/file.gz':
            self._send(gzip_mod.compress(BINARY_PAYLOAD),
                       content_type='application/octet-stream',
                       headers={'Content-Encoding': 'gzip'})
        elif path == '/loop':
            self._redirect('/loop')
        elif path == '/to-b':
            self._redirect(self.base_b + '/echo')
        elif path == '/echo':
            body = json.dumps({
                'authorization': self.headers.get('Authorization'),
                'cookie': self.headers.get('Cookie'),
            }).encode('utf-8')
            self._send(body, content_type='application/json')
        elif re.fullmatch(r'/redirect/\d+', path):
            n = int(path.rsplit('/', 1)[1])
            self._redirect('/final' if n == 0 else f'/redirect/{n - 1}')
        elif path == '/final':
            self._send(b'<html><head><title>Final</title></head><body>'
                       b'<article><p>final destination reached after redirects.</p>'
                       b'</article></body></html>')
        else:
            self.send_error(404)


SERVER_A = None
SERVER_B = None
BASE_A = ''
BASE_B = ''


def setUpModule():
    global SERVER_A, SERVER_B, BASE_A, BASE_B
    SERVER_B = ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
    SERVER_A = ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
    BASE_B = f'http://127.0.0.1:{SERVER_B.server_address[1]}'
    BASE_A = f'http://127.0.0.1:{SERVER_A.server_address[1]}'
    _Handler.base_b = BASE_B
    for srv in (SERVER_A, SERVER_B):
        threading.Thread(target=srv.serve_forever, daemon=True).start()


def tearDownModule():
    for srv in (SERVER_A, SERVER_B):
        srv.shutdown()
        srv.server_close()


def run_cli(*args, timeout=30, cwd=None, allow_private=False):
    env = dict(os.environ)
    if allow_private:
        env['SCRAPE_ALLOW_PRIVATE_HOSTS'] = '1'
    else:
        env.pop('SCRAPE_ALLOW_PRIVATE_HOSTS', None)
    r = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, timeout=timeout, cwd=cwd, env=env,
    )
    for name in ('stdout', 'stderr'):
        raw = getattr(r, name)
        if isinstance(raw, bytes):
            try:
                setattr(r, name, raw.decode('utf-8'))
            except UnicodeDecodeError:
                setattr(r, name, raw.decode('utf-8', errors='replace'))
    return r


def allow_private():
    return mock.patch.object(scrape, 'ALLOW_PRIVATE_HOSTS', True)


def deny_private():
    """Pin ALLOW_PRIVATE_HOSTS=False regardless of the shell environment,
    so in-process SSRF tests also pass under SCRAPE_ALLOW_PRIVATE_HOSTS=1."""
    return mock.patch.object(scrape, 'ALLOW_PRIVATE_HOSTS', False)


def _env_without_proxies(**extra):
    """Copy of os.environ with all *_proxy variables removed (+ extras)."""
    env = {k: v for k, v in os.environ.items()
           if not k.lower().endswith('_proxy')}
    env.update(extra)
    return env


# ── Browse against the local server (subprocess CLI) ───────────────────
class TestBrowseLocalServer(unittest.TestCase):
    def test_browse_basic(self):
        r = run_cli('browse', BASE_A + '/', allow_private=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 200)
        self.assertEqual(data['title'], 'Local Test Page')
        self.assertIn('locally served page', data['markdown'])
        self.assertIn('text/html', data['content_type'])
        self.assertIsInstance(data.get('resources'), list)

    def test_browse_gzip(self):
        r = run_cli('browse', BASE_A + '/gzip', allow_private=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 200)
        self.assertIn('locally served page', data['markdown'])
        self.assertFalse(
            any('decompression failed' in w
                for w in data['extraction']['warnings']))

    def test_browse_deflate(self):
        r = run_cli('browse', BASE_A + '/deflate', allow_private=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn('locally served page', data['markdown'])

    def test_browse_deflate_raw_no_spurious_truncation_warning(self):
        # Raw deflate streams have no end marker; a complete stream must not
        # be reported as truncated.
        r = run_cli('browse', BASE_A + '/deflate-raw', allow_private=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn('locally served page', data['markdown'])
        self.assertFalse(
            any('truncated' in w for w in data['extraction']['warnings']),
            data['extraction']['warnings'])

    def test_browse_utf16_bom(self):
        r = run_cli('browse', BASE_A + '/utf16', allow_private=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['title'], 'UTF16 页面')
        self.assertIn('UTF-16 编码', data['markdown'])

    def test_redirect_chain(self):
        r = run_cli('browse', BASE_A + '/redirect/3', allow_private=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 200)
        self.assertTrue(data['url'].endswith('/final'), data['url'])
        self.assertIn('final destination', data['markdown'])

    def test_redirect_loop_reports_error(self):
        r = run_cli('browse', BASE_A + '/loop', allow_private=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('redirect limit exceeded', data['error'])


# ── Size limits (in-process, patched constants) ────────────────────────
class TestResponseLimits(unittest.TestCase):
    def test_browse_response_truncation_warning(self):
        with allow_private(), \
                mock.patch.object(scrape, 'MAX_RESPONSE_BYTES', 1024):
            data = scrape.BrowseWeb().browse(BASE_A + '/big')
        warnings = data['extraction']['warnings']
        self.assertTrue(any('truncated at 1024 bytes' in w for w in warnings),
                        warnings)

    def test_gzip_decompressed_output_cap_warning(self):
        # Compressed body fits under the cap; decompressed output exceeds it.
        with allow_private(), \
                mock.patch.object(scrape, 'MAX_RESPONSE_BYTES', 4096):
            data = scrape.BrowseWeb().browse(BASE_A + '/gzip-big')
        warnings = data['extraction']['warnings']
        self.assertTrue(
            any('decompressed response truncated at 4096 bytes' in w
                for w in warnings),
            warnings)


# ── Download against the local server ──────────────────────────────────
class TestDownloadLocalServer(unittest.TestCase):
    def test_download_success(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'blob.bin')
            r = run_cli('download', BASE_A + '/binary', path, allow_private=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data['status'], 200)
            self.assertEqual(data['size'], len(BINARY_PAYLOAD))
            self.assertEqual(data['content_type'], 'application/octet-stream')
            with open(path, 'rb') as f:
                self.assertEqual(f.read(), BINARY_PAYLOAD)

    def test_download_404_error_json_no_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'missing.bin')
            r = run_cli('download', BASE_A + '/nope', path, allow_private=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data['status'], 404)
            self.assertIn('404', data['error'])
            self.assertFalse(os.path.exists(path))

    def test_download_gzip_is_decoded(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'blob.bin')
            r = run_cli('download', BASE_A + '/file.gz', path, allow_private=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data['status'], 200)
            self.assertEqual(data['size'], len(BINARY_PAYLOAD))
            with open(path, 'rb') as f:
                self.assertEqual(f.read(), BINARY_PAYLOAD)

    def test_download_relative_path_creates_parents(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            r = run_cli('download', BASE_A + '/binary', 'nested/dir/file.bin',
                        cwd=tmp, allow_private=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertTrue(os.path.exists(data['path']))
            self.assertEqual(data['size'], len(BINARY_PAYLOAD))

    def test_download_over_limit_removes_partial_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'blob.bin')
            with allow_private(), \
                    mock.patch.object(scrape, 'MAX_DOWNLOAD_BYTES', 100):
                result = scrape.BrowseWeb().download(BASE_A + '/binary', path)
            self.assertEqual(result['status'], 0)
            self.assertIn('exceeded', result['error'])
            self.assertFalse(os.path.exists(path))


class TestDownloadPreservesTargetFile(unittest.TestCase):
    """An explicit download path is written via a sibling temp file and
    atomically replaced on success; failures leave it untouched."""

    def _existing_file(self, tmp):
        path = os.path.join(tmp, 'keep.bin')
        with open(path, 'wb') as f:
            f.write(b'original-content')
        return path

    def _read(self, path):
        with open(path, 'rb') as f:
            return f.read()

    def test_404_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._existing_file(tmp)
            with allow_private():
                result = scrape.BrowseWeb().download(BASE_A + '/nope', path)
            self.assertEqual(result['status'], 404)
            self.assertEqual(self._read(path), b'original-content')
            self.assertEqual(sorted(os.listdir(tmp)), ['keep.bin'])

    def test_over_limit_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._existing_file(tmp)
            with allow_private(), \
                    mock.patch.object(scrape, 'MAX_DOWNLOAD_BYTES', 100):
                result = scrape.BrowseWeb().download(BASE_A + '/binary', path)
            self.assertEqual(result['status'], 0)
            self.assertIn('exceeded', result['error'])
            self.assertEqual(self._read(path), b'original-content')
            self.assertEqual(sorted(os.listdir(tmp)), ['keep.bin'])

    def test_mid_stream_failure_preserves_existing_file(self):
        class BrokenResp:
            def __init__(self):
                self._reads = 0

            def read(self, amt=-1):
                self._reads += 1
                if self._reads == 1:
                    return b'partial-data'
                raise ConnectionError('connection dropped mid-stream')

            def close(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            path = self._existing_file(tmp)
            bw = scrape.BrowseWeb()
            with allow_private(), mock.patch.object(
                    bw._fetch, 'stream',
                    return_value=(BrokenResp(), BASE_A + '/binary', {}, 200)):
                with self.assertRaises(ConnectionError):
                    bw.download(BASE_A + '/binary', path)
            self.assertEqual(self._read(path), b'original-content')
            self.assertEqual(sorted(os.listdir(tmp)), ['keep.bin'])

    def test_success_replaces_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._existing_file(tmp)
            with allow_private():
                result = scrape.BrowseWeb().download(BASE_A + '/binary', path)
            self.assertEqual(result['status'], 200)
            self.assertEqual(result['path'], path)
            self.assertEqual(self._read(path), BINARY_PAYLOAD)
            self.assertEqual(sorted(os.listdir(tmp)), ['keep.bin'])


class _ChunkedResp:
    """Fake response object replaying a fixed chunk sequence."""

    def __init__(self, chunks):
        self._chunks = list(chunks)

    def read(self, amt=-1):
        return self._chunks.pop(0) if self._chunks else b''

    def close(self):
        pass


class TestDownloadDeflateSniffing(unittest.TestCase):
    def _download_chunked(self, chunks, headers, tmp):
        bw = scrape.BrowseWeb()
        path = os.path.join(tmp, 'out.bin')
        with allow_private(), mock.patch.object(
                bw._fetch, 'stream',
                return_value=(_ChunkedResp(chunks), BASE_A + '/x', headers, 200)):
            result = bw.download(BASE_A + '/x', path)
        return result, path

    def test_raw_deflate_one_byte_first_chunk(self):
        # A lone first byte cannot discriminate raw vs zlib-wrapped deflate
        # (both variants accept it without error); deciding on it would pick
        # zlib-wrapped and fail every later chunk. Must buffer >= 2 bytes.
        payload = _raw_deflate(BINARY_PAYLOAD)
        with tempfile.TemporaryDirectory() as tmp:
            result, path = self._download_chunked(
                [payload[:1], payload[1:]], {'content-encoding': 'deflate'}, tmp)
            self.assertEqual(result.get('status'), 200, result)
            with open(path, 'rb') as f:
                self.assertEqual(f.read(), BINARY_PAYLOAD)

    def test_zlib_wrapped_deflate_one_byte_first_chunk(self):
        payload = zlib.compress(BINARY_PAYLOAD)
        with tempfile.TemporaryDirectory() as tmp:
            result, path = self._download_chunked(
                [payload[:1], payload[1:]], {'content-encoding': 'deflate'}, tmp)
            self.assertEqual(result.get('status'), 200, result)
            with open(path, 'rb') as f:
                self.assertEqual(f.read(), BINARY_PAYLOAD)

    def test_one_byte_compressed_body_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, path = self._download_chunked(
                [b'\x78'], {'content-encoding': 'deflate'}, tmp)
            self.assertEqual(result['status'], 0)
            self.assertIn('decompression failed', result['error'])
            self.assertFalse(os.path.exists(path))


# ── Cross-origin redirect header stripping ─────────────────────────────
class TestCrossOriginRedirect(unittest.TestCase):
    def test_sensitive_headers_stripped_on_cross_origin_redirect(self):
        with allow_private():
            result = scrape.Fetch().fetch(
                BASE_A + '/to-b',
                headers={'Authorization': 'Bearer secret-token',
                         'Cookie': 'session=secret-cookie'})
        self.assertEqual(result['status'], 200)
        self.assertTrue(result['url'].endswith('/echo'))
        self.assertNotIn('secret-token', result['content'])
        self.assertNotIn('secret-cookie', result['content'])
        echoed = json.loads(result['content'])
        self.assertIsNone(echoed['authorization'])
        self.assertIsNone(echoed['cookie'])


# ── Search with canned engine responses ────────────────────────────────
DDG_HTML = '''<html><body>
<div class="results">
<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fdocs.python.org%2F3%2F&amp;rut=abc123">Python 3 Docs</a>
<a class="result__snippet">Official documentation for Python 3.</a>
<a class="result__a" href="https://no-snippet.example.com/page">No Snippet Page</a>
</div>
</body></html>'''

BRAVE_HTML = '''<html><body>
<div class="snippet">
<a class="result-header" href="https://brave-result.example.com/post"><span>Brave Result Title</span></a>
<div class="snippet-description">Brave snippet body.</div>
</div>
</body></html>'''


class CannedFetch:
    """FakeFetch with the same signature as Fetch.fetch."""

    def __init__(self, ddg=None, brave=None):
        # values: dict payload, or Exception instance to raise
        self._routes = {'duckduckgo.com': ddg, 'brave.com': brave}

    def fetch(self, url, headers=None, ua=None, max_bytes=None):
        for marker, payload in self._routes.items():
            if marker in url:
                if isinstance(payload, Exception):
                    raise payload
                return payload
        raise AssertionError(f'unexpected url: {url}')


def _ok(html: str) -> dict:
    return {
        'status': 200,
        'content': html,
        'raw': html.encode('utf-8'),
        'content_type': 'text/html; charset=utf-8',
        'url': 'https://engine.example/',
        'headers_dict': {},
        'warnings': [],
    }


class TestSearchOffline(unittest.TestCase):
    def _search_with(self, fake):
        with mock.patch.object(scrape, 'Fetch', return_value=fake):
            return scrape.SearchEngine().search('python docs', num=5)

    def test_ddg_results_and_no_snippet_result_kept(self):
        out = self._search_with(CannedFetch(ddg=_ok(DDG_HTML)))
        self.assertIsInstance(out, list)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]['url'], 'https://docs.python.org/3/')
        self.assertEqual(out[0]['title'], 'Python 3 Docs')
        self.assertEqual(out[0]['snippet'],
                         'Official documentation for Python 3.')
        self.assertEqual(out[0]['source'], 'ddg')
        # Result without a snippet element must be kept, with empty snippet.
        self.assertEqual(out[1]['url'], 'https://no-snippet.example.com/page')
        self.assertEqual(out[1]['snippet'], '')

    def test_brave_used_when_ddg_fails(self):
        fake = CannedFetch(ddg={'status': 500, 'content': '', 'raw': b'',
                                'content_type': '', 'url': '',
                                'headers_dict': {}, 'warnings': []},
                           brave=_ok(BRAVE_HTML))
        out = self._search_with(fake)
        self.assertIsInstance(out, list)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['url'], 'https://brave-result.example.com/post')
        self.assertEqual(out[0]['source'], 'brave')
        self.assertEqual(out[0]['snippet'], 'Brave snippet body.')

    def test_both_engines_fail_returns_warnings_payload(self):
        fake = CannedFetch(ddg=ConnectionError('no network'),
                           brave=ConnectionError('no network'))
        out = self._search_with(fake)
        self.assertIsInstance(out, dict)
        self.assertEqual(out['results'], [])
        self.assertEqual(len(out['warnings']), 2)
        self.assertTrue(any(w.startswith('ddg:') for w in out['warnings']))
        self.assertTrue(any(w.startswith('brave:') for w in out['warnings']))

    def test_both_engines_unparseable_returns_warnings_payload(self):
        fake = CannedFetch(ddg=_ok('<html><body>nothing useful</body></html>'),
                           brave=_ok('<html><body>nothing useful</body></html>'))
        out = self._search_with(fake)
        self.assertIsInstance(out, dict)
        self.assertEqual(out['results'], [])
        self.assertTrue(out['warnings'])

    def test_normalize_search_url_decodes_ddg_redirect(self):
        url = '//duckduckgo.com/l/?uddg=https%3A%2F%2Fdocs.python.org%2F3%2F&rut=abc'
        self.assertEqual(scrape._normalize_search_url(url),
                         'https://docs.python.org/3/')

    def test_clean_results_filters_ads_and_decodes_targets(self):
        results = [
            {'title': 'Ad',
             'url': '//duckduckgo.com/l/?uddg=https%3A%2F%2Fduckduckgo.com%2Fy.js%3Fad_domain%3Dudemy.com',
             'snippet': 'ad snippet'},
            {'title': 'Docs',
             'url': '//duckduckgo.com/l/?uddg=https%3A%2F%2Fdocs.python.org%2F&rut=abc',
             'snippet': 'docs snippet'},
        ]
        cleaned = scrape.SearchEngine()._clean_results(results, 'ddg', 5)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0]['url'], 'https://docs.python.org/')
        self.assertEqual(cleaned[0]['source'], 'ddg')


# ── HTMLToMarkdown behaviour ───────────────────────────────────────────
class TestHTMLToMarkdown(unittest.TestCase):
    def convert(self, html, base_url='https://example.com'):
        return scrape.HTMLToMarkdown().convert(html, base_url=base_url)

    def test_table_to_markdown(self):
        html = '''<html><body>
<table>
<tr><th>Name</th><th>Value</th></tr>
<tr><td>A</td><td>1</td></tr>
<tr><td>B</td><td>2</td></tr>
</table>
</body></html>'''
        md = self.convert(html)['markdown']
        self.assertIn('Name', md)
        self.assertIn('---', md)
        self.assertIn('| A | 1 |', md)

    def test_table_cell_keeps_inline_markup(self):
        html = '''<html><body>
<table>
<tr><th>Name</th><th>Link</th></tr>
<tr><td>A</td><td><a href="/about">About</a> <b>bold</b> <code>x=1</code></td></tr>
</table>
</body></html>'''
        md = self.convert(html)['markdown']
        row = next(l for l in md.splitlines() if 'About' in l)
        self.assertTrue(row.startswith('|'), row)
        self.assertIn('[About](https://example.com/about)', row)
        self.assertIn('**bold**', row)
        self.assertIn('`x=1`', row)

    def test_pre_code_preserves_whitespace(self):
        html = '''<html><body>
<pre><code>def foo():
    x = 1
    return x</code></pre>
</body></html>'''
        md = self.convert(html)['markdown']
        self.assertIn('    x = 1', md)
        self.assertIn('    return x', md)

    def test_base_href_resolves_relative_links(self):
        html = '''<html><head><base href="https://cdn.example.com/assets/"></head>
<body><a href="page.html">Link</a><img src="img.png" alt="pic"></body></html>'''
        result = self.convert(html, base_url='https://example.com/')
        self.assertIn('https://cdn.example.com/assets/page.html',
                      result['markdown'])
        self.assertIn('https://cdn.example.com/assets/img.png',
                      result['markdown'])

    def test_img_with_empty_src_is_skipped(self):
        html = '<p>a</p><img src="" alt="empty"><img src="ok.png" alt="ok">'
        result = self.convert(html)
        self.assertNotIn('![](', result['markdown'])
        self.assertEqual(len(result['resources']), 1)
        self.assertTrue(result['resources'][0]['url'].endswith('/ok.png'))

    def test_javascript_href_stripped(self):
        html = '<p><a href="  JAVASCRIPT:alert(1)">x</a></p>'
        md = self.convert(html)['markdown']
        self.assertNotIn('alert', md)
        self.assertNotIn('javascript', md.lower())

    def test_javascript_href_with_embedded_whitespace_stripped(self):
        # Browsers ignore whitespace inside the scheme, so "java\tscript:"
        # and "java\nscript:" must be blocked too.
        html = ('<p><a href="java\tscript:alert(1)">x</a>'
                '<a href="java\nscript:alert(2)">y</a></p>')
        md = self.convert(html)['markdown']
        self.assertNotIn('alert', md)
        self.assertNotIn('javascript', md.lower())

    def test_table_cell_link_url_escapes_pipe(self):
        html = '''<html><body>
<table>
<tr><th>Link</th></tr>
<tr><td><a href="/a|b">x</a></td></tr>
</table>
</body></html>'''
        md = self.convert(html)['markdown']
        row = next(l for l in md.splitlines()
                   if l.startswith('|') and 'x' in l)
        self.assertIn('[x](https://example.com/a\\|b)', row)
        # No unescaped pipe in the link target (would split the table cell).
        self.assertNotIn('a|b', row)

    def test_table_cell_img_src_escapes_pipe(self):
        html = '''<html><body>
<table>
<tr><td><img src="/i|mg.png" alt="pic"></td></tr>
</table>
</body></html>'''
        result = self.convert(html)
        self.assertIn('![pic](https://example.com/i\\|mg.png)',
                      result['markdown'])
        # The resources list keeps the raw, unescaped URL.
        self.assertEqual(result['resources'][0]['url'],
                         'https://example.com/i|mg.png')


# ── Charset detection ──────────────────────────────────────────────────
class TestCharsetDetection(unittest.TestCase):
    def test_utf8_bom(self):
        self.assertEqual(scrape.detect_charset({}, b'\xef\xbb\xbf<html>'),
                         'utf-8-sig')

    def test_utf16_bom_le_be(self):
        self.assertEqual(scrape.detect_charset({}, b'\xff\xfe<\x00'), 'utf-16')
        self.assertEqual(scrape.detect_charset({}, b'\xfe\xff\x00<'), 'utf-16')

    def test_utf32_bom_checked_before_utf16(self):
        self.assertEqual(scrape.detect_charset({}, b'\xff\xfe\x00\x00<\x00'),
                         'utf-32')
        self.assertEqual(scrape.detect_charset({}, b'\x00\x00\xfe\xff\x00<'),
                         'utf-32')

    def test_header_and_meta_fallback(self):
        self.assertEqual(
            scrape.detect_charset(
                {'content-type': 'text/html; charset=gbk'}, b'<html>'), 'gbk')
        self.assertEqual(
            scrape.detect_charset(
                {}, b'<html><head><meta charset="shift_jis"></head>'),
            'shift_jis')


# ── SSRF (no network: literal IPs are rejected before any I/O) ─────────
class TestSSRF(unittest.TestCase):
    def assert_blocked(self, *args):
        r = run_cli(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('private', data['error'].lower())

    def test_browse_private_ip_10(self):
        self.assert_blocked('browse', 'http://10.0.0.1/')

    def test_browse_private_ip_192_168(self):
        self.assert_blocked('browse', 'http://192.168.1.1/')

    def test_browse_private_ip_127(self):
        self.assert_blocked('browse', 'https://127.0.0.1/')

    def test_browse_private_ip_0_0_0_0(self):
        self.assert_blocked('browse', 'http://0.0.0.0/')

    def test_browse_private_ipv6_loopback(self):
        self.assert_blocked('browse', 'http://[::1]/')

    def test_browse_ipv4_mapped_ipv6_loopback(self):
        # ::ffff:127.0.0.1 must be judged by its mapped IPv4 address.
        self.assert_blocked('browse', 'http://[::ffff:127.0.0.1]/')

    def test_download_private_ip(self):
        self.assert_blocked('download', 'http://10.0.0.1/')

    def test_peer_check_blocks_private_peer(self):
        resp = mock.Mock()
        resp.getpeername.return_value = ('127.0.0.1', 8000)
        with deny_private(), self.assertRaises(ValueError) as ctx:
            scrape.Fetch()._check_peer(resp)
        self.assertIn('private peer', str(ctx.exception).lower())

    def test_peer_check_allows_unknown_peer(self):
        # No getpeername anywhere in the chain -> silently allowed.
        with deny_private():
            scrape.Fetch()._check_peer(object())


class TestProxyPeerCheck(unittest.TestCase):
    """Proxy trust model: with a user-configured proxy the connected peer is
    the proxy itself (a user-chosen intermediary), so the SSRF peer check is
    skipped; the target host was already validated by validate_url."""

    def test_proxy_configured_skips_peer_check(self):
        resp = mock.Mock()
        resp.getpeername.return_value = ('127.0.0.1', 8888)
        env = _env_without_proxies(http_proxy='http://127.0.0.1:8888')
        with deny_private(), mock.patch.dict(os.environ, env, clear=True):
            # Must not raise: the loopback peer is the user's own proxy.
            scrape.Fetch()._check_peer(resp, 'http://example.com/')

    def test_no_proxy_still_blocks_private_peer(self):
        resp = mock.Mock()
        resp.getpeername.return_value = ('127.0.0.1', 8000)
        with deny_private(), \
                mock.patch.dict(os.environ, _env_without_proxies(), clear=True):
            with self.assertRaises(ValueError) as ctx:
                scrape.Fetch()._check_peer(resp, 'http://example.com/')
        self.assertIn('private peer', str(ctx.exception).lower())

    def test_no_proxy_bypass_reenables_peer_check(self):
        # Host listed in no_proxy connects directly -> peer check applies.
        resp = mock.Mock()
        resp.getpeername.return_value = ('127.0.0.1', 8000)
        env = _env_without_proxies(http_proxy='http://127.0.0.1:8888',
                                   no_proxy='example.com')
        with deny_private(), mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ValueError):
                scrape.Fetch()._check_peer(resp, 'http://example.com/')


class TestRedirectSSRF(unittest.TestCase):
    def test_redirect_to_private_ip(self):
        with deny_private(), self.assertRaises(ValueError) as ctx:
            scrape.Fetch._validate_redirect('http://10.0.0.1/')
        self.assertIn('private', str(ctx.exception).lower())


# ── Scheme validation ──────────────────────────────────────────────────
class TestSchemeValidation(unittest.TestCase):
    def assert_scheme_error(self, *args):
        r = run_cli(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('scheme', data['error'].lower())

    def test_browse_ftp_scheme(self):
        self.assert_scheme_error('browse', 'ftp://example.com/file')

    def test_download_ftp_scheme(self):
        self.assert_scheme_error('download', 'ftp://example.com/file')

    def test_browse_file_scheme(self):
        self.assert_scheme_error('browse', 'file:///etc/passwd')


# ── Fetch internals with mocked opener ─────────────────────────────────
class TestHTTPHeaderCaseInsensitive(unittest.TestCase):
    def test_case_insensitive_content_encoding(self):
        original = b'Hello case-insensitive headers!'
        compressed = gzip_mod.compress(original)

        class MockResp:
            status = 200
            headers = {'Content-Encoding': 'gzip',
                       'Content-Type': 'text/plain; charset=utf-8'}

            def read(self, amt=-1):
                return compressed

            def close(self):
                pass

        f = scrape.Fetch()
        orig_open = f._opener.open
        try:
            f._opener.open = lambda *a, **kw: MockResp()
            result = f.fetch('https://example.com/')
        finally:
            f._opener.open = orig_open
        self.assertIn('case-insensitive', result['content'])


# ── Content extraction contract (in-process, no network) ───────────────
class FakeFetch:
    """FakeFetch with the same signature as Fetch.fetch."""

    def __init__(self, payload: dict):
        self._payload = payload

    def fetch(self, url, headers=None, ua=None, max_bytes=None):
        return dict(self._payload, url=url)


class TestBrowseNonHTML(unittest.TestCase):
    def test_browse_json(self):
        payload = '{"slideshow": {"title": "Sample"}}'
        fake = FakeFetch({
            'status': 200,
            'content': payload,
            'raw': payload.encode('utf-8'),
            'content_type': 'application/json',
            'headers_dict': {},
            'warnings': [],
        })
        bw = scrape.BrowseWeb()
        bw._fetch = fake
        data = bw.browse('https://example.com/data.json')
        self.assertEqual(data['status'], 200)
        self.assertIn('application/json', data['content_type'].lower())
        self.assertIn('{', data['markdown'])
        self.assertIn('}', data['markdown'])


class TestBinaryResourceMetadata(unittest.TestCase):
    def test_binary_resource_has_size_and_content_type(self):
        raw = b'\x89PNG\r\n\x1a\nabc'
        fake = FakeFetch({
            'status': 200,
            'content': raw.decode('utf-8', errors='replace'),
            'raw': raw,
            'content_type': 'image/png',
            'headers_dict': {},
            'warnings': [],
        })
        bw = scrape.BrowseWeb()
        bw._fetch = fake
        data = bw.browse('https://example.com/image.png')
        resources = data.get('resources', [])
        self.assertGreaterEqual(len(resources), 1)
        res = resources[0]
        self.assertIn('size', res)
        self.assertIn('content_type', res)
        self.assertIsInstance(res['size'], int)
        self.assertGreater(res['size'], 0)


class TestContentExtractionContract(unittest.TestCase):
    def setUp(self):
        self.ContentExtractor = scrape.ContentExtractor
        self._orig_trafilatura = scrape.trafilatura
        self._orig_document = scrape.Document
        self._orig_markdownify = scrape.markdownify_md
        scrape.trafilatura = None
        scrape.Document = None
        scrape.markdownify_md = None

    def tearDown(self):
        scrape.trafilatura = self._orig_trafilatura
        scrape.Document = self._orig_document
        scrape.markdownify_md = self._orig_markdownify

    def test_heuristic_extracts_article_before_template_noise(self):
        article_text = ' '.join(['正文段落提供足够长的可读内容, 用来验证正文抽取会避开导航和页脚噪声.'] * 12)
        html = f'''<html><head><title>文章标题</title><meta name="author" content="作者A"></head><body>
<nav><a href="/home">首页</a><a href="/about">关于</a></nav>
<article><h1>文章标题</h1><p>{article_text}</p><img src="pic.png" alt="配图"></article>
<footer>版权和友情链接</footer>
</body></html>'''
        result = self.ContentExtractor().extract(html, url='https://example.com/post')
        self.assertTrue(result['ok'])
        self.assertEqual(result['method'], 'heuristic')
        self.assertIn('正文段落', result['markdown'])
        self.assertNotIn('首页', result['markdown'])
        self.assertEqual(result['title'], '文章标题')
        self.assertEqual(result['author'], '作者A')
        self.assertGreaterEqual(len(result['resources']), 1)

    def test_full_mode_uses_full_html_converter(self):
        html = '<html><head><title>T</title></head><body><nav>Nav</nav><main><p>Main content long enough ' + ('x ' * 80) + '</p></main></body></html>'
        result = self.ContentExtractor().extract(html, url='https://example.com', mode='full')
        self.assertEqual(result['method'], 'full_html')
        self.assertTrue(result['ok'])
        self.assertIn('Main content', result['markdown'])

    def test_raw_mode_returns_original_html(self):
        html = '<html><body><div id="app"></div><script src="app.js"></script></body></html>'
        result = self.ContentExtractor().extract(html, mode='raw')
        self.assertEqual(result['method'], 'raw_html')
        self.assertEqual(result['markdown'], html)

    def test_no_fallback_marks_spa_as_low_confidence(self):
        html = '<html><body><div id="app"></div><script src="app.js"></script></body></html>'
        result = self.ContentExtractor().extract(html, mode='extract', no_fallback=True)
        self.assertFalse(result['ok'])
        self.assertEqual(result['method'], 'none')
        self.assertEqual(result['confidence'], 'low')
        self.assertTrue(any('JavaScript' in w for w in result['warnings']))

    def test_browse_payload_contains_extraction_contract(self):
        html = '<html><head><title>T</title></head><body><article><p>' + ('正文内容 ' * 80) + '</p></article></body></html>'
        fake = FakeFetch({
            'status': 200,
            'content': html,
            'raw': html.encode('utf-8'),
            'content_type': 'text/html; charset=utf-8',
            'headers_dict': {},
            'warnings': [],
        })
        bw = scrape.BrowseWeb()
        bw._fetch = fake
        data = bw.browse('https://example.com/post', mode='extract')
        self.assertIn('extraction', data)
        self.assertIn('metadata', data)
        self.assertEqual(data['extraction']['mode'], 'extract')
        self.assertIn(data['extraction']['confidence'], ('high', 'medium', 'low'))
        self.assertTrue(data['markdown'].strip())

    def test_trafilatura_metadata_does_not_duplicate_full_text(self):
        html = '<html><body><article><p>' + ('正文内容 ' * 120) + '</p></article></body></html>'

        class FakeTrafilatura:
            def extract(self, html, **kwargs):
                if kwargs.get('output_format') == 'json':
                    return json.dumps({
                        'title': 'T',
                        'text': 'x' * 5000,
                        'raw_text': 'y' * 5000,
                        'description': 'desc',
                        'source': 'https://example.com/post',
                    })
                return '正文内容 ' * 120

        scrape.trafilatura = FakeTrafilatura()
        result = self.ContentExtractor().extract(html, url='https://example.com/post')
        self.assertTrue(result['ok'])
        self.assertEqual(result['method'], 'trafilatura')
        self.assertNotIn('text', result['metadata'])
        self.assertNotIn('raw_text', result['metadata'])
        self.assertEqual(result['metadata']['description'], 'desc')
        self.assertEqual(result['metadata']['source'], 'https://example.com/post')


class TestPythonVersionSmoke(unittest.TestCase):
    def test_version_check_passes_on_current_python(self):
        r = run_cli('--help')
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == '__main__':
    unittest.main()
