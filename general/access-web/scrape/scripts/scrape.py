"""scrape.py -- zero-dependency web scraping / search / download tool."""

import sys

# ── Version check ──────────────────────────────────────────────────────
if sys.version_info < (3, 9):
    sys.stderr.write("Python >= 3.9 required\n")
    sys.exit(1)

import argparse
import gzip
import ipaddress
import io
import json
import os
import re
import socket
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zlib
from html.parser import HTMLParser

try:
    import trafilatura
except ImportError:  # optional enhanced extractor
    trafilatura = None

try:
    from readability import Document
except ImportError:  # optional enhanced extractor
    Document = None

try:
    from markdownify import markdownify as markdownify_md
except ImportError:  # optional enhanced converter
    markdownify_md = None


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
def _is_blocked_ip(value: str) -> bool:
    """Return True for private, loopback, link-local, reserved or unsafe IPs."""
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(
        (
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_reserved,
            ip.is_unspecified,
            ip.is_multicast,
        )
    )


def is_private_host(hostname: str) -> bool:
    """Return True if hostname is an unsafe IP literal."""
    if not hostname:
        return False
    if hostname.startswith("[") and hostname.endswith("]"):
        hostname = hostname[1:-1]
    return _is_blocked_ip(hostname)


def _resolves_to_private_host(hostname: str) -> bool:
    """Return True if DNS resolution yields an unsafe IP address."""
    if not hostname or is_private_host(hostname):
        return is_private_host(hostname)
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    for info in infos:
        address = info[4][0]
        if _is_blocked_ip(address):
            return True
    return False


def validate_url(url: str) -> None:
    """Validate URL scheme and host. Raises ValueError on violation."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"unsupported scheme: {parsed.scheme}")
    if _resolves_to_private_host(parsed.hostname or ""):
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

    def fetch(self, url: str, headers: dict = None, ua: str = UA,
              max_bytes: int = None) -> dict:
        hdrs = {"User-Agent": ua, "Accept-Encoding": "gzip, deflate"}
        if headers:
            hdrs.update(headers)

        resp_headers = {}
        status = 0
        raw = b""
        final_url = url
        warnings = []

        for _ in range(self.REDIRECT_LIMIT + 1):
            req = urllib.request.Request(url, headers=hdrs)
            try:
                resp = self._opener.open(req, timeout=TIMEOUT)
                raw, truncated = self._read_limited(resp, max_bytes)
                if truncated:
                    warnings.append("response truncated at max_bytes")
                final_url = resp.geturl()
                resp_headers = self._headers_dict(resp.headers)
                status = resp.status
            except urllib.error.HTTPError as e:
                raw, truncated = self._read_limited(e, max_bytes) if hasattr(e, "read") else (b"", False)
                if truncated:
                    warnings.append("response truncated at max_bytes")
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
        enc = resp_headers.get("content-encoding", "").lower()
        if enc == "gzip":
            try:
                raw = gzip.decompress(raw)
            except Exception:
                warnings.append("gzip decompression failed; returned compressed bytes decoded as text")
        elif enc == "deflate":
            try:
                raw = zlib.decompress(raw)
            except Exception:
                try:
                    raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                except Exception:
                    warnings.append("deflate decompression failed; returned compressed bytes decoded as text")

        charset = detect_charset(resp_headers, raw)
        try:
            content = raw.decode(charset, errors="replace")
        except (LookupError, UnicodeDecodeError):
            content = raw.decode("utf-8", errors="replace")

        if status >= 400:
            warnings.append(f"http status {status}")

        return {
            "status": status,
            "content": content,
            "raw": raw,
            "content_type": resp_headers.get("content-type", ""),
            "url": final_url,
            "headers_dict": resp_headers,
            "warnings": warnings,
        }

    @staticmethod
    def _validate_redirect(url: str) -> None:
        """Validate redirect target URL (scheme + SSRF)."""
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"redirect to unsupported scheme: {parsed.scheme}")
        if _resolves_to_private_host(parsed.hostname or ""):
            raise ValueError(f"redirect to private address: {parsed.hostname}")

    @staticmethod
    def _read_limited(resp, max_bytes: int = None):
        if max_bytes is None or max_bytes <= 0:
            return resp.read(), False
        raw = resp.read(max_bytes + 1)
        if len(raw) > max_bytes:
            return raw[:max_bytes], True
        return raw, False

    @staticmethod
    def _headers_dict(headers) -> dict:
        """Convert HTTP headers to a lowercase-key dict."""
        return {k.lower(): v for k, v in headers.items()}


# ── HTMLToMarkdown ─────────────────────────────────────────────────────
_IGNORE_TAGS = {"script", "style", "nav", "footer", "svg", "noscript"}
_INLINE_WRAP = {"strong": "**", "em": "_", "b": "**", "i": "_", "code": "`"}


class HTMLToMarkdown(HTMLParser):
    def __init__(self, include_links: bool = True, include_images: bool = True,
                 include_tables: bool = True):
        super().__init__()
        self.include_links = include_links
        self.include_images = include_images
        self.include_tables = include_tables

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
            self._href_stack.append(href if self.include_links else None)
            if self.include_links:
                self._buf.append("[")
        elif low == "img":
            src = attrs_d.get("src", "")
            if src:
                src = resolve_url(src, self._base_url)
            alt = attrs_d.get("alt", "")
            if self.include_images:
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
        elif low == "table" and self.include_tables:
            self._table_rows = []
        elif low == "tr" and self.include_tables:
            self._current_row = []
        elif low in ("td", "th") and self.include_tables:
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
            if href is not None:
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
        elif low in ("td", "th") and self.include_tables:
            self._in_cell = False
            self._current_row.append("".join(self._current_cell).strip())
            self._current_cell = []
        elif low == "tr" and self.include_tables:
            if self._current_row:
                self._table_rows.append(self._current_row)
            self._current_row = []
        elif low == "table" and self.include_tables:
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
def _normalize_search_url(url: str) -> str:
    """Normalize search-provider redirect URLs to their target HTTP(S) URL."""
    if not url:
        return ""
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if host in ("duckduckgo.com", "www.duckduckgo.com") and parsed.path.startswith("/l/"):
        qs = urllib.parse.parse_qs(parsed.query)
        target = qs.get("uddg", [""])[0]
        if target:
            if target.startswith("//"):
                target = "https:" + target
            target_parsed = urllib.parse.urlparse(target)
            if target_parsed.scheme in ("http", "https"):
                return target
    return url


def _is_search_result_url(url: str) -> bool:
    """Return True for user-facing HTTP(S) search results, not ads or wrappers."""
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not host:
        return False
    low = url.lower()
    if host in ("duckduckgo.com", "www.duckduckgo.com"):
        if parsed.path.startswith("/y.js") or "ad_domain=" in low:
            return False
        return False
    if host in ("bing.com", "www.bing.com") and parsed.path.startswith("/aclick"):
        return False
    return True


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
                    out = self._clean_results(p.results, "ddg", n)
                    if out:
                        return out
                # DDG returned HTML but no parsed results -> try generic on DDG
                generic = self._clean_results(self._generic_on(r["content"]), "fallback", n)
                if generic:
                    return generic
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
                    out = self._clean_results(p.results, "brave", n)
                    if out:
                        return out
                generic = self._clean_results(self._generic_on(r["content"]), "fallback", n)
                if generic:
                    return generic
        except Exception:
            pass

        return []

    def _generic_on(self, html: str) -> list:
        p = _GenericLinkParser()
        try:
            p.feed(html)
        except Exception:
            pass
        return p.links[: self.MAX]

    def _clean_results(self, results: list, source: str, limit: int) -> list:
        out = []
        seen = set()
        for item in results:
            url = _normalize_search_url(item.get("url", ""))
            if not _is_search_result_url(url):
                continue
            key = url.split("#", 1)[0]
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "title": item.get("title", "").strip(),
                "url": url,
                "snippet": item.get("snippet", "").strip(),
                "source": source,
            })
            if len(out) >= limit:
                break
        return out


# ── Content extraction ─────────────────────────────────────────────────
class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.metadata = {}
        self._in_title = False
        self._title_buf = []

    def handle_starttag(self, tag, attrs):
        d = {k.lower(): v for k, v in attrs}
        low = tag.lower()
        if low == "title":
            self._in_title = True
            self._title_buf = []
        elif low == "meta":
            key = (d.get("name") or d.get("property") or "").lower()
            content = d.get("content", "").strip()
            if key and content:
                self.metadata[key] = content

    def handle_endtag(self, tag):
        if tag.lower() == "title" and self._in_title:
            self._in_title = False
            self.title = "".join(self._title_buf).strip()

    def handle_data(self, data):
        if self._in_title:
            self._title_buf.append(data)


def _extract_metadata(html: str) -> dict:
    parser = _MetaParser()
    try:
        parser.feed(html)
    except Exception:
        pass
    metadata = dict(parser.metadata)
    title = metadata.get("og:title") or metadata.get("twitter:title") or parser.title
    author = metadata.get("author") or metadata.get("article:author") or ""
    date = (
        metadata.get("article:published_time")
        or metadata.get("date")
        or metadata.get("pubdate")
        or ""
    )
    description = metadata.get("description") or metadata.get("og:description") or ""
    sitename = metadata.get("og:site_name") or ""
    compact = {}
    for key, value in metadata.items():
        if key in ("description", "og:description", "og:site_name", "author",
                   "article:author", "article:published_time", "date", "pubdate"):
            compact[key] = value
    if description:
        compact.setdefault("description", description)
    if sitename:
        compact.setdefault("sitename", sitename)
    return {"title": title, "author": author, "date": date, "metadata": compact}


def _plain_text_from_markdown(markdown: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", markdown)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_>#|\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class ContentExtractor:
    POSITIVE_HINTS = re.compile(r"article|post|content|entry|main|body|doc|markdown", re.I)
    NEGATIVE_HINTS = re.compile(
        r"nav|footer|comment|related|sidebar|ad-|advert|promo|cookie|share|menu|login",
        re.I,
    )

    def __init__(self, include_links: bool = True, include_images: bool = True,
                 include_tables: bool = True):
        self.include_links = include_links
        self.include_images = include_images
        self.include_tables = include_tables

    def extract(self, html: str, url: str = "", mode: str = "extract",
                no_fallback: bool = False) -> dict:
        metadata = _extract_metadata(html)
        if mode == "raw":
            return self._raw_html_result(html, metadata)
        if mode == "full":
            return self._full_html_result(html, url, metadata, method="full_html",
                                          ok=True)

        warnings = []
        for extractor in (
            self._extract_with_trafilatura,
            self._extract_with_readability,
            self._extract_with_heuristic,
        ):
            result = extractor(html, url, metadata)
            if result is None:
                continue
            result["warnings"].extend(self._content_warnings(result["markdown"], html))
            result["confidence"] = self._score_confidence(result["markdown"], html,
                                                           result["warnings"])
            if self._is_good_result(result):
                return result
            warnings.extend(result["warnings"])
            warnings.append(f"{result['method']} extraction was low confidence")

        if no_fallback:
            warnings = self._dedupe_warnings(warnings + [
                "main content extraction failed",
                "fallback disabled by --no-fallback",
            ] + self._content_warnings("", html))
            return {
                "ok": False,
                "method": "none",
                "confidence": "low",
                "title": metadata["title"],
                "author": metadata["author"],
                "date": metadata["date"],
                "markdown": "",
                "metadata": metadata["metadata"],
                "resources": self._resources_from_html(html, url),
                "warnings": warnings,
            }

        fallback = self._full_html_result(html, url, metadata,
                                          method="full_html_fallback", ok=False)
        fallback["confidence"] = "low"
        fallback["warnings"] = self._dedupe_warnings(warnings + [
            "main content extraction failed",
            "returned full-page markdown fallback",
            "output may contain navigation, footer, ads, or unrelated links",
        ] + self._content_warnings(fallback["markdown"], html))
        return fallback

    def _extract_with_trafilatura(self, html: str, url: str, metadata: dict):
        if trafilatura is None:
            return None
        try:
            markdown = trafilatura.extract(
                html,
                url=url or None,
                output_format="markdown",
                include_links=self.include_links,
                include_images=self.include_images,
                include_tables=self.include_tables,
                include_comments=False,
                favor_precision=True,
            )
            metadata_json = trafilatura.extract(
                html,
                url=url or None,
                output_format="json",
                with_metadata=True,
                include_comments=False,
                favor_precision=True,
            )
        except Exception:
            return None
        if not markdown or not markdown.strip():
            return None
        rich = self._safe_json_loads(metadata_json) if metadata_json else {}
        merged_meta = self._compact_metadata(metadata["metadata"])
        if isinstance(rich, dict):
            merged_meta.update(self._compact_metadata(rich))
        return {
            "ok": True,
            "method": "trafilatura",
            "confidence": "medium",
            "title": rich.get("title") or metadata["title"],
            "author": rich.get("author") or metadata["author"],
            "date": rich.get("date") or metadata["date"],
            "markdown": markdown.strip() + "\n",
            "metadata": merged_meta,
            "resources": self._resources_from_html(html, url),
            "warnings": [],
        }

    def _extract_with_readability(self, html: str, url: str, metadata: dict):
        if Document is None or markdownify_md is None:
            return None
        try:
            doc = Document(html)
            summary_html = doc.summary()
            title = doc.title()
            markdown = markdownify_md(summary_html, heading_style="ATX")
        except Exception:
            return None
        if not markdown or not markdown.strip():
            return None
        return {
            "ok": True,
            "method": "readability-lxml",
            "confidence": "medium",
            "title": title or metadata["title"],
            "author": metadata["author"],
            "date": metadata["date"],
            "markdown": markdown.strip() + "\n",
            "metadata": metadata["metadata"],
            "resources": self._resources_from_html(html, url),
            "warnings": [],
        }

    def _extract_with_heuristic(self, html: str, url: str, metadata: dict):
        candidates = self._candidate_fragments(html)
        best = None
        for name, attrs, fragment in candidates:
            conv = self._convert_fragment(fragment, url)
            markdown = conv["markdown"]
            score = self._heuristic_score(fragment, markdown, attrs)
            if best is None or score > best["score"]:
                best = {"score": score, "name": name, "conv": conv}
        if not best or not best["conv"]["markdown"].strip() or best["score"] < 20:
            return None
        return {
            "ok": True,
            "method": "heuristic",
            "confidence": "medium",
            "title": best["conv"].get("title") or metadata["title"],
            "author": metadata["author"],
            "date": metadata["date"],
            "markdown": best["conv"]["markdown"],
            "metadata": metadata["metadata"],
            "resources": best["conv"].get("resources", []),
            "warnings": [],
        }

    def _candidate_fragments(self, html: str) -> list:
        candidates = []
        for tag in ("article", "main"):
            for match in re.finditer(
                rf"<({tag})([^>]*)>(.*?)</{tag}>", html, re.I | re.S
            ):
                candidates.append((tag, match.group(2), match.group(0)))
        for match in re.finditer(r"<(div|section)([^>]*)>(.*?)</\1>", html, re.I | re.S):
            attrs = match.group(2)
            if self.POSITIVE_HINTS.search(attrs) or not self.NEGATIVE_HINTS.search(attrs):
                candidates.append((match.group(1).lower(), attrs, match.group(0)))
        body = re.search(r"<body[^>]*>(.*?)</body>", html, re.I | re.S)
        if body:
            candidates.append(("body", "", body.group(0)))
        if not candidates:
            candidates.append(("document", "", html))
        return candidates[:80]

    def _heuristic_score(self, fragment: str, markdown: str, attrs: str) -> float:
        text = _plain_text_from_markdown(markdown)
        text_len = len(text)
        paragraph_count = max(
            len(re.findall(r"</p\s*>", fragment, re.I)),
            len([p for p in markdown.split("\n\n") if len(p.strip()) > 40]),
        )
        punctuation_count = len(re.findall(r"[.!?;:。！？；：]", text))
        link_density = self._link_density(fragment)
        score = 0.0
        score += min(text_len / 25.0, 60.0)
        score += min(paragraph_count * 8.0, 40.0)
        score += min(punctuation_count * 1.5, 30.0)
        score -= link_density * 80.0
        score += 25.0 if self.POSITIVE_HINTS.search(attrs) else 0.0
        score -= 35.0 if self.NEGATIVE_HINTS.search(attrs) else 0.0
        return score

    def _full_html_result(self, html: str, url: str, metadata: dict, method: str,
                          ok: bool) -> dict:
        conv = self._convert_fragment(html, url)
        markdown = conv["markdown"]
        warnings = self._content_warnings(markdown, html)
        confidence = self._score_confidence(markdown, html, warnings)
        return {
            "ok": ok and bool(markdown.strip()),
            "method": method,
            "confidence": confidence,
            "title": conv.get("title") or metadata["title"],
            "author": metadata["author"],
            "date": metadata["date"],
            "markdown": markdown,
            "metadata": metadata["metadata"],
            "resources": conv.get("resources", []),
            "warnings": warnings,
        }

    def _raw_html_result(self, html: str, metadata: dict) -> dict:
        return {
            "ok": True,
            "method": "raw_html",
            "confidence": "high" if html.strip() else "low",
            "title": metadata["title"],
            "author": metadata["author"],
            "date": metadata["date"],
            "markdown": html,
            "metadata": metadata["metadata"],
            "resources": [],
            "warnings": [],
        }

    def _convert_fragment(self, html: str, url: str) -> dict:
        return HTMLToMarkdown(
            include_links=self.include_links,
            include_images=self.include_images,
            include_tables=self.include_tables,
        ).convert(html, base_url=url)

    def _resources_from_html(self, html: str, url: str) -> list:
        if not self.include_images:
            return []
        return HTMLToMarkdown(include_links=False, include_images=True,
                              include_tables=False).convert(html, base_url=url)["resources"]

    def _is_good_result(self, result: dict) -> bool:
        return bool(
            result.get("ok")
            and result.get("markdown", "").strip()
            and result.get("confidence") in ("high", "medium")
        )

    def _score_confidence(self, markdown: str, html: str, warnings: list = None) -> str:
        warnings = warnings or []
        text = _plain_text_from_markdown(markdown)
        text_len = len(text)
        link_density = self._link_density(html)
        if text_len < 120 or link_density > 0.55:
            return "low"
        if any("login" in w or "JavaScript" in w for w in warnings):
            return "low"
        paragraphs = [p for p in markdown.split("\n\n") if len(_plain_text_from_markdown(p)) > 60]
        if text_len > 800 and len(paragraphs) >= 3 and link_density < 0.25:
            return "high"
        return "medium"

    def _content_warnings(self, markdown: str, html: str) -> list:
        warnings = []
        text = _plain_text_from_markdown(markdown)
        html_text = self._strip_tags(html)
        if len(text) < 120:
            warnings.append("extracted content is empty or too short")
        if self._looks_like_spa(html, html_text, text):
            warnings.extend([
                "page may require JavaScript rendering",
                "this tool does not execute JavaScript",
            ])
        if self._looks_like_login(html_text):
            warnings.append("page appears to require login or authentication")
        if self._link_density(html) > 0.55:
            warnings.append("link density is high; page may be navigation, search, or listing content")
        return self._dedupe_warnings(warnings)

    def _link_density(self, html: str) -> float:
        text = self._strip_tags(html)
        if not text:
            return 0.0
        link_text = " ".join(
            self._strip_tags(m.group(1))
            for m in re.finditer(r"<a\b[^>]*>(.*?)</a>", html, re.I | re.S)
        )
        return min(1.0, len(link_text) / max(len(text), 1))

    def _strip_tags(self, html: str) -> str:
        html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.I | re.S)
        html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.I | re.S)
        html = re.sub(r"<[^>]+>", " ", html)
        html = re.sub(r"&nbsp;", " ", html)
        return re.sub(r"\s+", " ", html).strip()

    def _looks_like_spa(self, html: str, html_text: str, extracted_text: str) -> bool:
        script_count = len(re.findall(r"<script\b", html, re.I))
        app_root = re.search(r"id=[\"'](?:app|root|__next|__nuxt)[\"']", html, re.I)
        no_paragraphs = not re.search(r"<(p|article|main|h1|h2)\b", html, re.I)
        return bool((len(extracted_text) < 120 or len(html_text) < 200) and app_root and (script_count >= 1 or no_paragraphs))

    def _looks_like_login(self, text: str) -> bool:
        return bool(re.search(r"\b(sign in|log in|login|password|authentication|required)\b", text, re.I))

    def _safe_json_loads(self, value: str) -> dict:
        try:
            data = json.loads(value)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _compact_metadata(self, metadata: dict) -> dict:
        """Keep metadata useful while preventing full article text duplication."""
        if not isinstance(metadata, dict):
            return {}
        drop_keys = {
            "raw_text", "text", "body", "content", "comments", "commentsbody",
            "maintext", "rawtext", "html", "xml",
        }
        keep = {}
        for key, value in metadata.items():
            if not value:
                continue
            key_s = str(key)
            if key_s.lower() in drop_keys:
                continue
            if isinstance(value, str):
                keep[key_s] = value[:1000]
            elif isinstance(value, (int, float, bool)):
                keep[key_s] = value
            elif isinstance(value, (list, tuple)):
                compact = [str(item)[:200] for item in value[:20] if item]
                if compact:
                    keep[key_s] = compact
        return keep

    def _dedupe_warnings(self, warnings: list) -> list:
        out = []
        seen = set()
        for warning in warnings:
            if warning and warning not in seen:
                seen.add(warning)
                out.append(warning)
        return out


# ── BrowseWeb ──────────────────────────────────────────────────────────
class BrowseWeb:
    def __init__(self):
        self._fetch = Fetch()
        self._search = SearchEngine()

    def browse(self, url: str, mode: str = "extract", output_format: str = "markdown",
               include_links: bool = True, include_images: bool = True,
               include_tables: bool = True, no_fallback: bool = False,
               max_chars: int = None) -> dict:
        validate_url(url)
        if mode not in ("extract", "full", "raw"):
            raise ValueError(f"unsupported mode: {mode}")
        if output_format != "markdown":
            raise ValueError(f"unsupported format: {output_format}")

        result = self._fetch.fetch(url)
        mime, _ = parse_content_type(result["content_type"])
        fetch_warnings = list(result.get("warnings", []))

        if mime == "text/html" or mime.endswith("+html") or mime == "":
            extractor = ContentExtractor(
                include_links=include_links,
                include_images=include_images,
                include_tables=include_tables,
            )
            extracted = extractor.extract(result["content"], url=result["url"],
                                          mode=mode, no_fallback=no_fallback)
            self._append_warnings(extracted, fetch_warnings)
            extracted["markdown"] = self._limit_markdown(extracted["markdown"],
                                                          max_chars, extracted)
            return self._browse_payload(result, extracted, mode)

        # Non-HTML text-like content: return raw text in the compatibility field.
        if mime.startswith("text/") or mime in (
            "application/xml", "application/json",
        ) or mime.endswith("+xml") or mime.endswith("+json"):
            markdown = result["content"]
            extracted = {
                "ok": True,
                "method": "raw_text",
                "mode": mode,
                "confidence": "high" if markdown.strip() else "low",
                "warnings": fetch_warnings,
            }
            markdown = self._limit_markdown(markdown, max_chars, extracted)
            return {
                "url": result["url"],
                "title": "",
                "author": "",
                "date": "",
                "content_type": result["content_type"],
                "markdown": markdown,
                "resources": [],
                "metadata": {},
                "extraction": extracted,
                "status": result["status"],
            }

        # Binary / other types: structured description.
        size = len(result["raw"])
        markdown = f"[Binary resource: {mime}, size {size} bytes]\nURL: {result['url']}"
        extracted = {
            "ok": True,
            "method": "binary_resource",
            "mode": mode,
            "confidence": "high",
            "warnings": fetch_warnings,
        }
        markdown = self._limit_markdown(markdown, max_chars, extracted)
        return {
            "url": result["url"],
            "title": "",
            "author": "",
            "date": "",
            "content_type": result["content_type"],
            "markdown": markdown,
            "resources": [{"type": mime.split("/")[0] if mime else "binary",
                           "url": result["url"], "size": size,
                           "content_type": result["content_type"]}],
            "metadata": {},
            "extraction": extracted,
            "status": result["status"],
        }

    def _browse_payload(self, fetch_result: dict, extracted: dict, mode: str) -> dict:
        return {
            "url": fetch_result["url"],
            "title": extracted.get("title", ""),
            "author": extracted.get("author", ""),
            "date": extracted.get("date", ""),
            "content_type": fetch_result["content_type"],
            "markdown": extracted.get("markdown", ""),
            "resources": extracted.get("resources", []),
            "metadata": extracted.get("metadata", {}),
            "extraction": {
                "ok": extracted.get("ok", False),
                "method": extracted.get("method", "none"),
                "mode": mode,
                "confidence": extracted.get("confidence", "low"),
                "warnings": extracted.get("warnings", []),
            },
            "status": fetch_result["status"],
        }

    def _append_warnings(self, extracted: dict, warnings: list) -> None:
        seen = set(extracted.get("warnings", []))
        for warning in warnings:
            if warning and warning not in seen:
                extracted.setdefault("warnings", []).append(warning)
                seen.add(warning)

    def _limit_markdown(self, markdown: str, max_chars: int, extracted: dict) -> str:
        if max_chars is None or max_chars <= 0 or len(markdown) <= max_chars:
            return markdown
        extracted.setdefault("warnings", []).append("markdown truncated at max_chars")
        suffix = "\n[Truncated at max_chars]\n"
        return markdown[:max(0, max_chars - len(suffix))].rstrip() + suffix

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

    parser = argparse.ArgumentParser(prog="scrape")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_browse = sub.add_parser("browse")
    p_browse.add_argument("url")
    p_browse.add_argument("--mode", choices=("extract", "full", "raw"), default="extract")
    p_browse.add_argument("--format", choices=("markdown",), default="markdown")
    p_browse.add_argument("--include-links", action=argparse.BooleanOptionalAction, default=True)
    p_browse.add_argument("--include-images", action=argparse.BooleanOptionalAction, default=True)
    p_browse.add_argument("--include-tables", action=argparse.BooleanOptionalAction, default=True)
    p_browse.add_argument("--no-fallback", action="store_true")
    p_browse.add_argument("--max-chars", type=int, default=None)

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
            result = bw.browse(
                args.url,
                mode=args.mode,
                output_format=args.format,
                include_links=args.include_links,
                include_images=args.include_images,
                include_tables=args.include_tables,
                no_fallback=args.no_fallback,
                max_chars=args.max_chars,
            )
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
