import unittest
import subprocess
import sys
import os
import json

SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'browse_web.py')


def run_cli(*args, timeout=30, cwd=None):
    r = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, timeout=timeout, cwd=cwd
    )
    # Decode as UTF-8 (script forces UTF-8 on stdout/stderr)
    try:
        r.stdout = r.stdout.decode('utf-8') if isinstance(r.stdout, bytes) else (r.stdout or '')
    except UnicodeDecodeError:
        r.stdout = r.stdout.decode('utf-8', errors='replace') if isinstance(r.stdout, bytes) else ''
    try:
        r.stderr = r.stderr.decode('utf-8') if isinstance(r.stderr, bytes) else (r.stderr or '')
    except UnicodeDecodeError:
        r.stderr = r.stderr.decode('utf-8', errors='replace') if isinstance(r.stderr, bytes) else ''
    return r


class TestBrowseHTML(unittest.TestCase):
    def test_browse_example_com(self):
        r = run_cli('browse', 'https://example.com')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 200)
        self.assertTrue(data['markdown'].strip(), 'markdown should not be empty')
        self.assertTrue(data.get('title'), 'title should not be empty')
        self.assertIn('text/html', data['content_type'])


class TestBrowseNonHTML(unittest.TestCase):
    def test_browse_json(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from browse_web import BrowseWeb

        payload = '{"slideshow": {"title": "Sample"}}'

        class FakeFetch:
            def fetch(self, url, max_bytes=None):
                return {
                    'status': 200,
                    'content': payload,
                    'raw': payload.encode('utf-8'),
                    'content_type': 'application/json',
                    'url': url,
                    'headers_dict': {},
                    'warnings': [],
                }

        bw = BrowseWeb()
        bw._fetch = FakeFetch()
        data = bw.browse('https://example.com/data.json')
        self.assertEqual(data['status'], 200)
        self.assertIn('application/json', data['content_type'].lower())
        # markdown should contain the original JSON payload
        self.assertIn('{', data['markdown'])
        self.assertIn('}', data['markdown'])


class TestBrowseResources(unittest.TestCase):
    def test_resources_is_array(self):
        r = run_cli('browse', 'https://en.wikipedia.org/wiki/Main_Page')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIsInstance(data.get('resources'), list)


class TestContentExtractionContract(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        import browse_web
        self.browse_web = browse_web
        self.ContentExtractor = browse_web.ContentExtractor
        self._orig_trafilatura = browse_web.trafilatura
        self._orig_document = browse_web.Document
        self._orig_markdownify = browse_web.markdownify_md
        browse_web.trafilatura = None
        browse_web.Document = None
        browse_web.markdownify_md = None

    def tearDown(self):
        self.browse_web.trafilatura = self._orig_trafilatura
        self.browse_web.Document = self._orig_document
        self.browse_web.markdownify_md = self._orig_markdownify

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

        class FakeFetch:
            def fetch(self, url):
                return {
                    'status': 200,
                    'content': html,
                    'raw': html.encode('utf-8'),
                    'content_type': 'text/html; charset=utf-8',
                    'url': url,
                    'headers_dict': {},
                    'warnings': [],
                }

        bw = self.browse_web.BrowseWeb()
        bw._fetch = FakeFetch()
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

        self.browse_web.trafilatura = FakeTrafilatura()
        result = self.ContentExtractor().extract(html, url='https://example.com/post')
        self.assertTrue(result['ok'])
        self.assertEqual(result['method'], 'trafilatura')
        self.assertNotIn('text', result['metadata'])
        self.assertNotIn('raw_text', result['metadata'])
        self.assertEqual(result['metadata']['description'], 'desc')
        self.assertEqual(result['metadata']['source'], 'https://example.com/post')


class TestBrowseGzip(unittest.TestCase):
    def test_browse_gzip(self):
        r = run_cli('browse', 'https://example.com')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data['markdown'].strip(), 'gzip decompression failed')


class TestSearch(unittest.TestCase):
    def test_search_returns_results(self):
        r = run_cli('search', 'python standard library', '-n', '5')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1, 'search returned 0 results')
        self.assertLessEqual(len(data), 5)
        for item in data:
            self.assertIn('title', item)
            self.assertIn('url', item)
            self.assertIn('snippet', item)
            self.assertTrue(item['url'].startswith(('http://', 'https://')))
            self.assertNotIn('duckduckgo.com/l/', item['url'])

    def test_ddg_redirect_url_is_decoded(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from browse_web import _normalize_search_url
        url = '//duckduckgo.com/l/?uddg=https%3A%2F%2Fdocs.python.org%2F3%2F&rut=abc'
        self.assertEqual(_normalize_search_url(url), 'https://docs.python.org/3/')

    def test_search_clean_results_filters_ads_and_decodes_targets(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from browse_web import SearchEngine
        results = [
            {
                'title': 'Ad',
                'url': '//duckduckgo.com/l/?uddg=https%3A%2F%2Fduckduckgo.com%2Fy.js%3Fad_domain%3Dudemy.com',
                'snippet': 'ad snippet',
            },
            {
                'title': 'Docs',
                'url': '//duckduckgo.com/l/?uddg=https%3A%2F%2Fdocs.python.org%2F&rut=abc',
                'snippet': 'docs snippet',
            },
        ]
        cleaned = SearchEngine()._clean_results(results, 'ddg', 5)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0]['url'], 'https://docs.python.org/')
        self.assertEqual(cleaned[0]['source'], 'ddg')


class TestDownload(unittest.TestCase):
    def test_download_file_exists(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'favicon.ico')
            r = run_cli('download', 'https://example.com/favicon.ico', path)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertTrue(os.path.exists(data['path']))
            self.assertGreater(data['size'], 0)


class TestHTMLTable(unittest.TestCase):
    def test_table_to_markdown(self):
        html = '''<html><body>
<table>
<tr><th>Name</th><th>Value</th></tr>
<tr><td>A</td><td>1</td></tr>
<tr><td>B</td><td>2</td></tr>
</table>
</body></html>'''
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from browse_web import HTMLToMarkdown
        result = HTMLToMarkdown().convert(html, base_url='https://example.com')
        md = result['markdown']
        self.assertIn('Name', md)
        self.assertIn('---', md)
        self.assertIn('| A | 1 |', md)


class TestCodeBlock(unittest.TestCase):
    def test_pre_code_preserves_whitespace(self):
        html = '''<html><body>
<pre><code>def foo():
    x = 1
    return x</code></pre>
</body></html>'''
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from browse_web import HTMLToMarkdown
        result = HTMLToMarkdown().convert(html, base_url='https://example.com')
        md = result['markdown']
        # Preserve 4-space indent and newlines inside code block
        self.assertIn('    x = 1', md)
        self.assertIn('    return x', md)


class TestSSRF(unittest.TestCase):
    def test_browse_private_ip_10(self):
        r = run_cli('browse', 'http://10.0.0.1/')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('private', data['error'].lower())

    def test_browse_private_ip_192_168(self):
        r = run_cli('browse', 'http://192.168.1.1/')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('private', data['error'].lower())

    def test_browse_private_ip_127(self):
        r = run_cli('browse', 'https://127.0.0.1/')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('private', data['error'].lower())

    def test_browse_private_ip_0_0_0_0(self):
        r = run_cli('browse', 'http://0.0.0.0/')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('private', data['error'].lower())

    def test_browse_private_ipv6_loopback(self):
        r = run_cli('browse', 'http://[::1]/')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('private', data['error'].lower())


class TestDownloadRelPath(unittest.TestCase):
    def test_download_relative_path_creates_parents(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            r = run_cli('download', 'https://example.com/favicon.ico', 'nested/dir/file.ico', cwd=tmp)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertTrue(os.path.exists(data['path']))
            self.assertGreater(data['size'], 0)


class TestPythonVersionSmoke(unittest.TestCase):
    def test_version_check_passes_on_current_python(self):
        # Cycle 10 smoke: on Python >= 3.9 the script must not refuse to run.
        r = run_cli('--help')
        # argparse --help exits with 0 on success
        self.assertEqual(r.returncode, 0, r.stderr)


class TestSchemeValidation(unittest.TestCase):
    """Fix 2: browse/download reject non-http/https schemes with JSON error."""

    def test_browse_ftp_scheme(self):
        r = run_cli('browse', 'ftp://example.com/file')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('scheme', data['error'].lower())

    def test_download_ftp_scheme(self):
        r = run_cli('download', 'ftp://example.com/file')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('scheme', data['error'].lower())

    def test_browse_file_scheme(self):
        r = run_cli('browse', 'file:///etc/passwd')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('scheme', data['error'].lower())


class TestRedirectSSRF(unittest.TestCase):
    """Fix 3: redirect to private IP must be blocked."""

    def test_redirect_to_private_ip(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from browse_web import Fetch
        with self.assertRaises(ValueError) as ctx:
            Fetch._validate_redirect('http://10.0.0.1/')
        self.assertIn('private', str(ctx.exception).lower())


class TestHTTPHeaderCaseInsensitive(unittest.TestCase):
    """Fix 4: Content-Encoding read must be case-insensitive."""

    def test_case_insensitive_content_encoding(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from browse_web import Fetch
        from http.client import HTTPMessage
        # Build a gzip payload
        import gzip as gzip_mod
        original = b'Hello case-insensitive headers!'
        compressed = gzip_mod.compress(original)
        # Build HTTPMessage with non-standard lowercase casing
        headers = HTTPMessage()
        headers['content-encoding'] = 'gzip'
        headers['content-type'] = 'text/plain; charset=utf-8'

        class MockResp:
            def read(self):
                return compressed
            def geturl(self):
                return 'https://example.com/'
            @property
            def status(self):
                return 200
            @property
            def headers(self):
                return headers

        f = Fetch()
        orig_open = f._opener.open
        try:
            f._opener.open = lambda *a, **kw: MockResp()
            result = f.fetch('https://example.com/')
        finally:
            f._opener.open = orig_open
        self.assertIn('case-insensitive', result['content'])


class TestBinaryResourceMetadata(unittest.TestCase):
    """Fix 5: binary resource includes size and content_type; size uses len(raw)."""

    def test_binary_resource_has_size_and_content_type(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from browse_web import BrowseWeb

        raw = b'\x89PNG\r\n\x1a\nabc'

        class FakeFetch:
            def fetch(self, url, max_bytes=None):
                return {
                    'status': 200,
                    'content': raw.decode('utf-8', errors='replace'),
                    'raw': raw,
                    'content_type': 'image/png',
                    'url': url,
                    'headers_dict': {},
                    'warnings': [],
                }

        bw = BrowseWeb()
        bw._fetch = FakeFetch()
        data = bw.browse('https://example.com/image.png')
        resources = data.get('resources', [])
        self.assertGreaterEqual(len(resources), 1)
        res = resources[0]
        self.assertIn('size', res)
        self.assertIn('content_type', res)
        self.assertIsInstance(res['size'], int)
        self.assertGreater(res['size'], 0)


class TestBaseHref(unittest.TestCase):
    """Fix 6: <base href> updates the base URL for relative link resolution."""

    def test_base_href_resolves_relative_links(self):
        html = '''<html><head><base href="https://cdn.example.com/assets/"></head>
<body><a href="page.html">Link</a><img src="img.png" alt="pic"></body></html>'''
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from browse_web import HTMLToMarkdown
        result = HTMLToMarkdown().convert(html, base_url='https://example.com/')
        self.assertIn('https://cdn.example.com/assets/page.html', result['markdown'])
        self.assertIn('https://cdn.example.com/assets/img.png', result['markdown'])


class TestTableFallback(unittest.TestCase):
    """Fix 7: table parse failure produces [Table: N rows x M cols] fallback."""

    def test_emit_table_fallback_on_bad_data(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from browse_web import HTMLToMarkdown
        parser = HTMLToMarkdown()
        parser.reset()
        parser._base_url = ''
        parser._buf = []
        parser._resources = []
        parser._title = ''
        parser._ignore_depth = 0
        parser._tag_stack = []
        parser._href_stack = []
        parser._list_stack = []
        parser._ol_counters = []
        parser._pre_depth = 0
        parser._in_title = False
        parser._title_buf = []
        parser._table_rows = []
        parser._current_row = []
        parser._current_cell = []
        parser._in_cell = False
        # Inject non-string cell data to trigger join() TypeError
        parser._table_rows = [['A', 'B'], [None, 'D']]
        parser._emit_table()
        md = ''.join(parser._buf)
        self.assertIn('[Table:', md)
        self.assertIn('2 rows', md)
        self.assertIn('2 cols', md)


class TestUnusedVariablesRemoved(unittest.TestCase):
    """Fix 8: unused variables/constants removed from module and instances."""

    def test_unused_vars_removed(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        import browse_web
        # Module-level constant _BLOCK_TAGS should be removed
        self.assertFalse(hasattr(browse_web, '_BLOCK_TAGS'),
                         '_BLOCK_TAGS should be removed')
        # Instance attributes that are never read should be removed
        parser = browse_web.HTMLToMarkdown()
        parser.convert('<p>hello</p>', base_url='https://example.com')
        self.assertFalse(hasattr(parser, '_tag_stack'),
                         '_tag_stack should be removed')
        self.assertFalse(hasattr(parser, '_li_active'),
                         '_li_active should be removed')
        self.assertFalse(hasattr(parser, '_code_depth'),
                         '_code_depth should be removed')


class TestDownloadSSRF(unittest.TestCase):
    """Fix 1 (extension): download SSRF also returns JSON error on stdout."""

    def test_download_private_ip(self):
        r = run_cli('download', 'http://10.0.0.1/')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('private', data['error'].lower())


if __name__ == '__main__':
    unittest.main()
