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
        r = run_cli('browse', 'https://httpbin.org/json')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
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
        r = run_cli('browse', 'https://httpbin.org/redirect-to?url=http://10.0.0.1/&status_code=302')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data['status'], 0)
        self.assertIn('private', data['error'].lower())


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
        r = run_cli('browse', 'https://httpbin.org/image/png')
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
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
