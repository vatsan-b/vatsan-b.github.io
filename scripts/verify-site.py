#!/usr/bin/env python3
"""
Verify site validity: serve docs/, check HTTP status of key pages,
validate search.json refs, check for missing files, and verify all
local links point to existing pages/fragments.

Usage: python3 scripts/verify-site.py
"""

import json
import sys
from html.parser import HTMLParser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, unquote
import threading
import time


class LinkParser(HTMLParser):
    """Extract links and ids from HTML."""

    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'a' and 'href' in attrs_dict:
            self.links.append(attrs_dict['href'])
        if 'id' in attrs_dict:
            self.ids.add(attrs_dict['id'])


def is_ignored_url(url):
    """Check if URL should be ignored (mailto, tel, javascript, data, http(s))."""
    url = url.strip()
    if not url:
        return True
    if url.startswith(('mailto:', 'tel:', 'javascript:', 'data:')):
        return True
    if url.startswith(('http://', 'https://')):
        return True
    return False


def normalize_relative_path(target_file, source_page, docs_dir):
    """
    Normalize a relative path against the source page.
    Returns normalized filename for lookup, or None if path goes outside docs/.
    """
    source_path = docs_dir / source_page
    source_dir = source_path.parent

    if target_file.startswith('/'):
        resolved = docs_dir / target_file.lstrip('/')
    else:
        resolved = (source_dir / target_file).resolve()

    try:
        relative = resolved.relative_to(docs_dir.resolve())
        return str(relative).replace('\\', '/')
    except ValueError:
        return None


def get_port():
    """Find an available port."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start_server(docs_dir, port):
    """Start ThreadingHTTPServer serving docs_dir."""
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=docs_dir, **kwargs)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)
    return server


def main():
    repo_root = Path(__file__).parent.parent
    docs_dir = repo_root / 'docs'

    if not docs_dir.exists():
        print(f"FAIL: docs directory not found at {docs_dir}")
        return 1

    errors = []

    # Check that certain files don't exist
    if (docs_dir / 'connect.html').exists():
        errors.append("docs/connect.html should not exist")
    if (docs_dir / 'publications-parsed.html').exists():
        errors.append("docs/publications-parsed.html should not exist")

    # Check search.json for forbidden refs
    search_json_path = docs_dir / 'search.json'
    if search_json_path.exists():
        try:
            with open(search_json_path) as f:
                search_data = json.load(f)
            for item in search_data:
                href = item.get('href', '')
                if 'publications-parsed.html' in href or 'connect.html' in href:
                    errors.append(f"search.json contains forbidden href: {href}")
        except Exception as e:
            errors.append(f"Failed to parse search.json: {e}")

    # Start server
    port = get_port()
    server = start_server(str(docs_dir), port)

    try:
        import urllib.request

        # Check HTTP status of key pages
        pages = ['index.html', 'about.html', 'research.html', 'publications.html', 'mentoring.html', 'for-fun.html']
        for page in pages:
            try:
                url = f'http://127.0.0.1:{port}/{page}'
                resp = urllib.request.urlopen(url)
                if resp.status != 200:
                    errors.append(f"{page}: HTTP {resp.status}")
            except Exception as e:
                errors.append(f"{page}: {e}")

        # Collect all ids from all pages
        all_ids = {}
        all_links = {}

        for page in pages:
            try:
                url = f'http://127.0.0.1:{port}/{page}'
                with urllib.request.urlopen(url) as resp:
                    html_content = resp.read().decode('utf-8')
                parser = LinkParser()
                parser.feed(html_content)
                all_ids[page] = parser.ids
                all_links[page] = parser.links
            except Exception as e:
                errors.append(f"Failed to parse {page}: {e}")

        # Validate all links
        for page, links in all_links.items():
            for link in links:
                if is_ignored_url(link):
                    continue

                parsed = urlparse(link)
                path_part = parsed.path or ''
                fragment_part = parsed.fragment or ''

                # Remove leading slash
                if path_part.startswith('/'):
                    path_part = path_part[1:]

                # Determine which file/page the link targets
                if not path_part:
                    # Fragment-only link: #section
                    target_file = page
                else:
                    # Link to a specific file - normalize relative paths
                    target_file = normalize_relative_path(path_part, page, docs_dir)
                    if target_file is None:
                        errors.append(f"{page}: link to {link} - path escapes docs/")
                        continue

                # Check file exists (if a path was specified)
                if path_part:
                    file_path = docs_dir / unquote(target_file)
                    if not file_path.exists():
                        errors.append(f"{page}: link to {link} - file not found")
                        continue

                # Check fragment exists (if specified)
                if fragment_part:
                    if target_file in all_ids:
                        if fragment_part not in all_ids[target_file]:
                            errors.append(f"{page}: link to {link} - fragment #{fragment_part} not found in {target_file}")

    finally:
        server.shutdown()

    if errors:
        print("FAIL")
        for error in errors:
            print(f"  {error}")
        return 1
    else:
        print("PASS")
        return 0


if __name__ == '__main__':
    sys.exit(main())
