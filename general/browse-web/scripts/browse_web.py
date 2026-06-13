"""browse_web.py -- zero-dependency web browsing / search / download tool."""

import sys

# ── Version check ──────────────────────────────────────────────────────
if sys.version_info < (3, 9):
    sys.stderr.write("Python >= 3.9 required\n")
    sys.exit(1)

import argparse
import gzip
import io
import json
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zlib
from html.parser import HTMLParser


# ── Constants ──────────────────────────────────────────────────────────
UA = "Mozilla/5.0 (compatible; AgentBrowser/1.0)"
SEARCH_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
)
TIMEOUT = 15
DDG_URL = "https://html.duckduckgo.com/html/?q={q}"
BRAVE_URL = "https://search.brave.com/search?q={q}"


# ── Helpers ────────────────────────────────────────────────────────────
def is_private_host(hostname: str) -> bool:
    """Return True if hostname is a private/reserved IP literal."""
    if not hostname:
        return False
    if hostname.startswith("[") and hostname.endswith("]"):
        hostname = hostname[1:-1]
    if hostname in ("::1", "::") or hostname.lower().startswith("fe80"):
        return True
    parts = hostname.split(".")
    if len(parts) != 4:
        return False
    try:
        octets = [int(p) for p in parts]
    except ValueError:
        return False
    if octets[0] == 10:
        return True
    if octets[0] == 172 and 16 <= octets[1] <= 31:
        return True
    if octets[0] == 192 and octets[1] == 168:
        return True
    if octets[0] == 127:
        return True
    if octets[0] == 0:
        return True
    return False


def validate_url(url: str) -> None:
    """Validate URL scheme and host. Raises ValueError on violation."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"unsupported scheme: {parsed.scheme}")
    if is_private_host(parsed.hostname or ""):
        raise ValueError(f"private address: {parsed.hostname}")


def resolve_url(url: str, base_url: str) -> str:
    """Resolve a potentially relative URL against a base URL."""
    return urllib.parse.urljoin(base_url, url)


def parse_content_type(ct_header: str):
    """Parse Content-Type header into (mime, params_dict)."""
    if not ct_header:
        return "", {}
    parts = ct_header.split(";")
    mime = parts[0].strip().lower()
    params = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.strip().lower()] = v.strip().strip('"').lower()
    return mime, params


def detect_charset(headers, html_bytes: bytes = b"") -> str:
    """Detect charset from headers or HTML meta tags."""
    ct = headers.get("content-type", "") if hasattr(headers, "get") else ""
    _, params = parse_content_type(ct)
    if "charset" in params:
        return params["charset"]
    head = html_bytes[:4096].decode("ascii", errors="ignore").lower()
    m = re.search(r'<meta[^>]+charset=["\']?([^"\'\s;>]+)', head)
    if m:
        return m.group(1)
    m = re.search(
        r'<meta[^>]+http-equiv=["\']?content-type["\']?[^>]+content=["\']?[^"\']*charset=([^"\'\s;>]+)',
        head,
    )
    if m:
        return m.group(1)
    return "utf-8"


# ── Fetch ──────────────────────────────────────────────────────────────
class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent urllib from auto-following redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Fetch:
    REDIRECT_LIMIT = 10
    _REDIRECT_CODES = {301, 302, 303, 307, 308}

    def __init__(self):
        self._opener = urllib.request.build_opener(_NoRedirectHandler)

    def fetch(self, url: str, headers: dict = None, ua: str = UA) -> dict:
        hdrs = {"User-Agent": ua, "Accept-Encoding": "gzip, deflate"}
        if headers:
            hdrs.update(headers)

        resp_headers = {}
        status = 0
        raw = b""
        final_url = url

        for _ in range(self.REDIRECT_LIMIT + 1):
            req = urllib.request.Request(url, headers=hdrs)
            try:
                resp = self._opener.open(req, timeout=TIMEOUT)
                raw = resp.read()
                final_url = resp.geturl()
                resp_headers = self._headers_dict(resp.headers)
                status = resp.status
            except urllib.error.HTTPError as e:
                raw = e.read() if hasattr(e, "read") else b""
                final_url = e.url or url
                resp_headers = self._headers_dict(e.headers) if hasattr(e, "headers") else {}
                status = e.code

            # Handle redirects manually with SSRF validation
            if status in self._REDIRECT_CODES:
                loc = resp_headers.get("location", "")
                if loc:
                    new_url = urllib.parse.urljoin(url, loc)
                    self._validate_redirect(new_url)
                    url = new_url
                    continue
            break

        # Decompress
        enc = resp_headers.get("content-encoding", "")
        if enc == "gzip":
            try:
                raw = gzip.decompress(raw)
            except Exception:
                pass
        elif enc == "deflate":
            try:
                raw = zlib.decompress(raw)
            except Exception:
                try:
                    raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                except Exception:
                    pass

        charset = detect_charset(resp_headers, raw)
        try:
            content = raw.decode(charset, errors="replace")
        except (LookupError, UnicodeDecodeError):
            content = raw.decode("utf-8", errors="replace")

        return {
            "status": status,
            "content": content,
            "raw": raw,
            "content_type": resp_headers.get("content-type", ""),
            "url": final_url,
            "headers_dict": resp_headers,
        }

    @staticmethod
    def _validate_redirect(url: str) -> None:
        """Validate redirect target URL (scheme + SSRF)."""
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"redirect to unsupported scheme: {parsed.scheme}")
        if is_private_host(parsed.hostname or ""):
            raise ValueError(f"redirect to private address: {parsed.hostname}")

    @staticmethod
    def _headers_dict(headers) -> dict:
        """Convert HTTP headers to a lowercase-key dict."""
        return {k.lower(): v for k, v in headers.items()}


# ── HTMLToMarkdown ─────────────────────────────────────────────────────
_IGNORE_TAGS = {"script", "style", "nav", "footer", "svg", "noscript"}
_INLINE_WRAP = {"strong": "**", "em": "_", "b": "**", "i": "_", "code": "`"}


class HTMLToMarkdown(HTMLParser):
    def convert(self, html: str, base_url: str = "") -> dict:
        self.reset()
        self._base_url = base_url
        self._buf: list[str] = []
        self._title = ""
        self._resources: list[dict] = []
        self._ignore_depth = 0
        self._href_stack: list[str] = []
        self._list_stack: list[str] = []  # "ul" or "ol"
        self._ol_counters: list[int] = []
        self._pre_depth = 0
        self._in_title = False
        self._title_buf: list[str] = []
        # table state
        self._table_rows: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []
        self._in_cell = False
        try:
            self.feed(html)
        except Exception:
            pass
        md = self._post_process("".join(self._buf))
        return {"title": self._title, "markdown": md, "resources": self._resources}

    # ── parser callbacks ───────────────────────────────────────────────
    def handle_starttag(self, tag: str, attrs):
        attrs_d = dict(attrs)
        low = tag.lower()

        if low in _IGNORE_TAGS:
            self._ignore_depth += 1
            return
        if self._ignore_depth:
            return

        if low == "title" and not self._title:
            self._in_title = True
            self._title_buf = []
        elif low == "base":
            href = attrs_d.get("href", "")
            if href:
                self._base_url = resolve_url(href, self._base_url)
        elif low in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(low[1])
            self._buf.append("\n\n" + "#" * level + " ")
        elif low == "p":
            self._buf.append("\n\n")
        elif low == "br":
            if self._pre_depth:
                self._buf.append("\n")
            else:
                self._buf.append("  \n")
        elif low == "a":
            href = attrs_d.get("href", "")
            if href.lower().startswith("javascript:"):
                href = ""
            elif href:
                href = resolve_url(href, self._base_url)
            self._href_stack.append(href)
            self._buf.append("[")
        elif low == "img":
            src = attrs_d.get("src", "")
            if src:
                src = resolve_url(src, self._base_url)
            alt = attrs_d.get("alt", "")
            if self._in_cell:
                self._current_cell.append(f"![{alt}]({src})")
            else:
                self._buf.append(f"![{alt}]({src})")
            self._resources.append({"type": "image", "url": src, "alt": alt})
        elif low in ("audio", "video"):
            src = attrs_d.get("src", "")
            if src:
                src = resolve_url(src, self._base_url)
                self._resources.append({"type": low, "url": src})
        elif low == "source":
            src = attrs_d.get("src", "")
            if src:
                src = resolve_url(src, self._base_url)
                self._resources.append({"type": "source", "url": src})
        elif low in ("strong", "em", "b", "i"):
            if not self._pre_depth:
                self._buf.append(_INLINE_WRAP[low])
        elif low == "code":
            if self._pre_depth == 0:
                self._buf.append("`")
        elif low == "pre":
            self._pre_depth += 1
            self._buf.append("\n\n```\n")
        elif low == "blockquote":
            self._buf.append("\n\n> ")
        elif low == "ul":
            self._list_stack.append("ul")
            self._buf.append("\n")
        elif low == "ol":
            self._list_stack.append("ol")
            self._ol_counters.append(0)
            self._buf.append("\n")
        elif low == "li":
            indent = "  " * max(0, len(self._list_stack) - 1)
            if self._list_stack and self._list_stack[-1] == "ol":
                if self._ol_counters:
                    self._ol_counters[-1] += 1
                    self._buf.append(f"\n{indent}{self._ol_counters[-1]}. ")
                else:
                    self._buf.append(f"\n{indent}1. ")
            else:
                self._buf.append(f"\n{indent}- ")
        elif low == "table":
            self._table_rows = []
        elif low == "tr":
            self._current_row = []
        elif low in ("td", "th"):
            self._in_cell = True
            self._current_cell = []

    def handle_endtag(self, tag: str):
        low = tag.lower()

        if low in _IGNORE_TAGS:
            self._ignore_depth = max(0, self._ignore_depth - 1)
            return
        if self._ignore_depth:
            return

        if low == "title" and self._in_title:
            self._in_title = False
            self._title = "".join(self._title_buf).strip()
        elif low in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote"):
            self._buf.append("\n")
        elif low == "a":
            href = self._href_stack.pop() if self._href_stack else ""
            self._buf.append(f"]({href})")
        elif low in ("strong", "em", "b", "i"):
            if not self._pre_depth:
                self._buf.append(_INLINE_WRAP[low])
        elif low == "code":
            if self._pre_depth == 0:
                self._buf.append("`")
        elif low == "pre":
            self._pre_depth = max(0, self._pre_depth - 1)
            self._buf.append("\n```\n")
        elif low in ("ul", "ol"):
            if self._list_stack and self._list_stack[-1] == low:
                self._list_stack.pop()
            if low == "ol" and self._ol_counters:
                self._ol_counters.pop()
            self._buf.append("\n")
        elif low in ("td", "th"):
            self._in_cell = False
            self._current_row.append("".join(self._current_cell).strip())
            self._current_cell = []
        elif low == "tr":
            if self._current_row:
                self._table_rows.append(self._current_row)
            self._current_row = []
        elif low == "table":
            self._emit_table()

    def handle_data(self, data: str):
        if self._ignore_depth:
            return
        if self._in_title:
            self._title_buf.append(data)
            return
        if self._in_cell:
            self._current_cell.append(data.replace("|", "\\|").replace("\n", " "))
            return
        if self._pre_depth:
            self._buf.append(data)
        else:
            text = re.sub(r"\s+", " ", data)
            if text:
                self._buf.append(text)

    def handle_entityref(self, name: str):
        self.handle_data(f"&{name};")

    def handle_charref(self, name: str):
        self.handle_data(f"&#{name};")

    # ── helpers ────────────────────────────────────────────────────────
    def _emit_table(self):
        rows = self._table_rows
        if not rows:
            return
        try:
            cols = max(len(r) for r in rows)
            normalized = [r + [""] * (cols - len(r)) for r in rows]
            self._buf.append("\n\n")
            self._buf.append("| " + " | ".join(normalized[0]) + " |\n")
            self._buf.append("| " + " | ".join(["---"] * cols) + " |\n")
            for row in normalized[1:]:
                self._buf.append("| " + " | ".join(row) + " |\n")
        except Exception:
            n_rows = len(rows)
            n_cols = max((len(r) for r in rows), default=0)
            self._buf.append(f"\n\n[Table: {n_rows} rows x {n_cols} cols]\n")

    def _post_process(self, md: str) -> str:
        md = re.sub(r"\n{3,}", "\n\n", md)
        md = re.sub(r"(?m)^[ \t]+$", "", md)
        return md.strip() + "\n" if md.strip() else ""


# ── SearchEngine ───────────────────────────────────────────────────────
class _DDGParser(HTMLParser):
    """Parse DuckDuckGo HTML search results."""

    def __init__(self):
        super().__init__()
        self.results: list[dict] = []
        self._current: dict = {}
        self._capture_title = False
        self._capture_snippet = False
        self._title_buf: list[str] = []
        self._snippet_buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        cls = d.get("class", "")
        if tag == "a" and "result__a" in cls:
            self._current = {"url": d.get("href", ""), "title": "", "snippet": ""}
            self._capture_title = True
            self._title_buf = []
        elif tag == "a" and "result__snippet" in cls:
            self._capture_snippet = True
            self._snippet_buf = []

    def handle_endtag(self, tag):
        if self._capture_title and tag == "a":
            self._current["title"] = "".join(self._title_buf).strip()
            self._capture_title = False
        if self._capture_snippet and tag == "a":
            self._current["snippet"] = "".join(self._snippet_buf).strip()
            self._capture_snippet = False
            if self._current.get("url"):
                self.results.append(self._current)
            self._current = {}

    def handle_data(self, data):
        if self._capture_title:
            self._title_buf.append(data)
        if self._capture_snippet:
            self._snippet_buf.append(data)


class _BraveParser(HTMLParser):
    """Parse Brave search results."""

    def __init__(self):
        super().__init__()
        self.results: list[dict] = []
        self._current: dict = {}
        self._capture_title = False
        self._capture_snippet = False
        self._capture_url = False
        self._title_buf: list[str] = []
        self._snippet_buf: list[str] = []
        self._url_buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        cls = d.get("class", "")
        if tag == "a" and "result-header" in cls:
            self._current = {"url": d.get("href", ""), "title": "", "snippet": ""}
            self._capture_title = True
            self._title_buf = []
        elif tag == "div" and "snippet-description" in cls:
            self._capture_snippet = True
            self._snippet_buf = []
        elif tag == "span" and "snippet-url" in cls:
            self._capture_url = True
            self._url_buf = []

    def handle_endtag(self, tag):
        if self._capture_title and tag == "a":
            self._current["title"] = "".join(self._title_buf).strip()
            self._capture_title = False
        if self._capture_snippet and tag == "div":
            self._current["snippet"] = "".join(self._snippet_buf).strip()
            self._capture_snippet = False
        if self._capture_url and tag == "span":
            if not self._current.get("url"):
                self._current["url"] = "https://" + "".join(self._url_buf).strip()
            self._capture_url = False
        if (
            tag in ("div", "li", "article")
            and self._current.get("title")
            and self._current.get("url")
        ):
            self.results.append(self._current)
            self._current = {}

    def handle_data(self, data):
        if self._capture_title:
            self._title_buf.append(data)
        if self._capture_snippet:
            self._snippet_buf.append(data)
        if self._capture_url:
            self._url_buf.append(data)


class _GenericLinkParser(HTMLParser):
    """Fallback: extract all <a> hrefs from a page."""

    SKIP_DOMAINS = (
        "duckduckgo.com",
        "brave.com",
        "google.com",
        "bing.com",
        "wikipedia.org",
        "about:",
        "javascript:",
    )

    def __init__(self):
        super().__init__()
        self.links: list[dict] = []
        self._capture = False
        self._href = ""
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a":
            href = d.get("href", "")
            if href.startswith(("http://", "https://")):
                low = href.lower()
                if not any(skip in low for skip in self.SKIP_DOMAINS):
                    self._capture = True
                    self._href = href
                    self._buf = []

    def handle_endtag(self, tag):
        if self._capture and tag == "a":
            text = "".join(self._buf).strip()
            if text and self._href:
                self.links.append(
                    {"title": text, "url": self._href, "snippet": ""}
                )
            self._capture = False

    def handle_data(self, data):
        if self._capture:
            self._buf.append(data)


class SearchEngine:
    MAX = 50

    def search(self, query: str, num: int = 10) -> list:
        n = min(max(1, num), self.MAX)
        f = Fetch()

        # 1. DDG
        try:
            r = f.fetch(DDG_URL.format(q=urllib.parse.quote_plus(query)), ua=SEARCH_UA)
            if r["status"] == 200 and r["content"].strip():
                p = _DDGParser()
                try:
                    p.feed(r["content"])
                except Exception:
                    pass
                if p.results:
                    out = p.results[:n]
                    for x in out:
                        x["source"] = "ddg"
                    return out
                # DDG returned HTML but no parsed results -> try generic on DDG
                generic = self._generic_on(r["content"])
                if generic:
                    return generic[:n]
        except Exception:
            pass

        # 2. Brave
        try:
            r = f.fetch(BRAVE_URL.format(q=urllib.parse.quote_plus(query)), ua=SEARCH_UA)
            if r["status"] == 200 and r["content"].strip():
                p = _BraveParser()
                try:
                    p.feed(r["content"])
                except Exception:
                    pass
                if p.results:
                    out = p.results[:n]
                    for x in out:
                        x["source"] = "brave"
                    return out
                generic = self._generic_on(r["content"])
                if generic:
                    return generic[:n]
        except Exception:
            pass

        return []

    def _generic_on(self, html: str) -> list:
        p = _GenericLinkParser()
        try:
            p.feed(html)
        except Exception:
            pass
        out = p.links[: self.MAX]
        for x in out:
            x["source"] = "fallback"
        return out


# ── BrowseWeb ──────────────────────────────────────────────────────────
class BrowseWeb:
    def __init__(self):
        self._fetch = Fetch()
        self._md = HTMLToMarkdown()
        self._search = SearchEngine()

    def browse(self, url: str) -> dict:
        validate_url(url)

        result = self._fetch.fetch(url)
        mime, _ = parse_content_type(result["content_type"])

        if mime == "text/html" or mime.endswith("+html") or mime == "":
            conv = self._md.convert(result["content"], base_url=result["url"])
            return {
                "url": result["url"],
                "title": conv["title"],
                "content_type": result["content_type"],
                "markdown": conv["markdown"],
                "resources": conv["resources"],
                "status": result["status"],
            }

        # Non-HTML text-like content: return raw
        if mime.startswith("text/") or mime in (
            "application/xml", "application/json",
        ) or mime.endswith("+xml") or mime.endswith("+json"):
            return {
                "url": result["url"],
                "title": "",
                "content_type": result["content_type"],
                "markdown": result["content"],
                "resources": [],
                "status": result["status"],
            }

        # Binary / other types: structured description
        size = len(result["raw"])
        return {
            "url": result["url"],
            "title": "",
            "content_type": result["content_type"],
            "markdown": f"[Binary resource: {mime}, size {size} bytes]\nURL: {result['url']}",
            "resources": [{"type": mime.split("/")[0], "url": result["url"],
                           "size": size, "content_type": result["content_type"]}],
            "status": result["status"],
        }

    def search(self, query: str, num: int = 10) -> list:
        return self._search.search(query, num)

    def download(self, url: str, path: str = None) -> dict:
        validate_url(url)

        if path is None:
            suffix = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".bin"
            fd, path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
        else:
            path = os.path.abspath(path)
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        result = self._fetch.fetch(url)
        raw = result["raw"]
        with open(path, "wb") as f:
            f.write(raw)

        return {
            "path": path,
            "url": result["url"],
            "size": len(raw),
            "content_type": result["content_type"],
        }


# ── CLI ────────────────────────────────────────────────────────────────
def main():
    # Force UTF-8 on stdout/stderr (Windows default is GBK/CP936)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(prog="browse_web")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_browse = sub.add_parser("browse")
    p_browse.add_argument("url")

    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("-n", type=int, default=10)

    p_download = sub.add_parser("download")
    p_download.add_argument("url")
    p_download.add_argument("path", nargs="?", default=None)

    args = parser.parse_args()
    bw = BrowseWeb()

    try:
        if args.cmd == "browse":
            result = bw.browse(args.url)
        elif args.cmd == "search":
            result = bw.search(args.query, args.n)
        elif args.cmd == "download":
            result = bw.download(args.url, args.path)
        else:
            parser.error("unknown command")
            return
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, Exception) as e:
        print(json.dumps({"status": 0, "error": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
