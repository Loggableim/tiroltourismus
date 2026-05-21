
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin
import requests

DIST_DIR = r"F:\tiroltourismus\dist"
SITE_BASE = "https://tiroltourismus.com"

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []  # (page, url, type, line_approx)
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == "a":
            href = attrs_dict.get("href")
            if href and href.strip() and not href.startswith("#") and not href.startswith("javascript:"):
                self.links.append(("a_href", href.strip()))
        
        if tag == "link":
            rel = attrs_dict.get("rel", "")
            href = attrs_dict.get("href")
            if href and rel == "canonical":
                self.links.append(("link_canonical", href.strip()))
        
        if tag == "img":
            src = attrs_dict.get("src")
            if src:
                self.links.append(("img_src", src.strip()))
        
        if tag == "script":
            src = attrs_dict.get("src")
            if src:
                self.links.append(("script_src", src.strip()))
        
        if tag == "link":
            rel = attrs_dict.get("rel", "")
            href = attrs_dict.get("href")
            if href and rel in ("stylesheet", "icon", "apple-touch-icon", "preload", "prefetch", "dns-prefetch", "alternate"):
                self.links.append(("link_" + rel, href.strip()))

def is_internal(url):
    """Check if URL points to the same site (relative or absolute with our domain)"""
    if url.startswith("/") or url.startswith("./") or url.startswith("../"):
        return True
    parsed = urlparse(url)
    if parsed.netloc in ("tiroltourismus.com", "www.tiroltourismus.com"):
        return True
    if not parsed.netloc:
        return True  # protocol-relative or absolute path
    return False

def is_mailto(url):
    return url.startswith("mailto:") or url.startswith("tel:")

def check_local_path(path, dist_dir):
    """Check if a local path exists in the dist directory"""
    # Clean the path
    if path.startswith("/"):
        path = path[1:]
    elif path.startswith("./"):
        path = path[2:]
    
    # Remove query strings and fragments
    if "?" in path:
        path = path.split("?")[0]
    if "#" in path:
        path = path.split("#")[0]
    
    # If path ends with /, try /index.html
    full_path = os.path.join(dist_dir, path)
    
    if os.path.exists(full_path):
        return True, None
    
    # Try adding index.html
    if full_path.endswith("/"):
        index_path = os.path.join(full_path, "index.html")
        if os.path.exists(index_path):
            return True, None
    
    # If no extension, try .html
    if not os.path.splitext(full_path)[1]:
        html_path = full_path + ".html"
        if os.path.exists(html_path):
            return True, None
        html_index = os.path.join(full_path, "index.html")
        if os.path.exists(html_index):
            return True, None
    
    return False, f"File not found: {full_path}"

def check_external_url(url, timeout=10):
    """Make a HEAD request to check if URL is reachable"""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; HermesLinkChecker/1.0)"
    }
    try:
        resp = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code < 400:
            return True, None
        # Some servers don't support HEAD, try GET
        resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
        if resp.status_code < 400:
            return True, None
        return False, f"HTTP {resp.status_code}: {url}"
    except requests.exceptions.SSLError as e:
        return False, f"SSL Error: {e}"
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection Error: {e}"
    except requests.exceptions.Timeout:
        return False, f"Timeout: {url}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    # Find all HTML files
    html_files = []
    for root, dirs, files in os.walk(DIST_DIR):
        for f in files:
            if f.endswith(".html"):
                html_files.append(os.path.join(root, f))
    
    print(f"Found {len(html_files)} HTML files to check\n")
    
    all_links = {}  # url -> [(page, type)]
    
    for filepath in sorted(html_files):
        rel_path = os.path.relpath(filepath, DIST_DIR).replace("\\", "/")
        page_url = "/" + rel_path.replace("/index.html", "/").lstrip("/")
        if page_url == "/":
            page_url = "/"
        
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        extractor = LinkExtractor()
        extractor.feed(content)
        
        for link_type, url in extractor.links:
            if is_mailto(url):
                continue
            if url not in all_links:
                all_links[url] = []
            all_links[url].append((page_url, link_type))
    
    print(f"Found {len(all_links)} unique URLs across all pages\n")
    
    # Categorize and check
    internal_links = {k: v for k, v in all_links.items() if is_internal(k) and not is_mailto(k)}
    external_links = {k: v for k, v in all_links.items() if not is_internal(k) and not is_mailto(k)}
    
    print(f"Internal links: {len(internal_links)}")
    print(f"External links: {len(external_links)}\n")
    
    # Check internal links
    broken_internal = []
    ok_internal = 0
    for url, sources in sorted(internal_links.items()):
        exists, error = check_local_path(url, DIST_DIR)
        if exists:
            ok_internal += 1
        else:
            broken_internal.append((url, error, sources))
    
    print(f"Internal: {ok_internal} OK, {len(broken_internal)} BROKEN\n")
    
    if broken_internal:
        print("=" * 70)
        print("BROKEN INTERNAL LINKS")
        print("=" * 70)
        for url, error, sources in broken_internal:
            print(f"\n  URL: {url}")
            print(f"  Error: {error}")
            for page, link_type in sources[:5]:
                print(f"    From: {page} ({link_type})")
    
    # Check external links
    broken_external = []
    skipped_external = 0
    ok_external = 0
    for url, sources in sorted(external_links.items()):
        # Skip certain domains that are known to block bots
        known_blockers = ["facebook.com", "instagram.com", "linkedin.com", "twitter.com", 
                         "x.com", "tiktok.com", "youtube.com", "pinterest.com",
                         "wa.me", "api.whatsapp.com"]
        if any(domain in url.lower() for domain in known_blockers):
            skipped_external += 1
            continue
        
        ok, error = check_external_url(url)
        if ok:
            ok_external += 1
        else:
            broken_external.append((url, error, sources))
    
    print(f"\nExternal: {ok_external} OK, {len(broken_external)} BROKEN, {skipped_external} SKIPPED (social/known-blockers)\n")
    
    if broken_external:
        print("=" * 70)
        print("BROKEN EXTERNAL LINKS")
        print("=" * 70)
        for url, error, sources in broken_external:
            print(f"\n  URL: {url}")
            print(f"  Error: {error}")
            for page, link_type in sources[:3]:
                print(f"    From: {page} ({link_type})")
    
    # Also check canonical links specifically
    print("\n" + "=" * 70)
    print("CANONICAL LINKS SUMMARY")
    print("=" * 70)
    canonical_links = [(url, sources) for url, sources in all_links.items() 
                       if any(t == "link_canonical" for _, t in sources)]
    for url, sources in canonical_links:
        pages = [p for p, t in sources if t == "link_canonical"]
        print(f"  {url}")
        for p in pages:
            print(f"    -> {p}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total HTML files: {len(html_files)}")
    print(f"Total unique URLs: {len(all_links)}")
    print(f"Internal OK: {ok_internal}")
    print(f"Internal BROKEN: {len(broken_internal)}")
    print(f"External OK: {ok_external}")
    print(f"External BROKEN: {len(broken_external)}")
    print(f"External SKIPPED: {skipped_external}")
    
    # Return structured data for further processing
    return {
        "total_pages": len(html_files),
        "total_urls": len(all_links),
        "internal_ok": ok_internal,
        "internal_broken": [(url, err) for url, err, _ in broken_internal],
        "external_ok": ok_external, 
        "external_broken": [(url, err) for url, err, _ in broken_external],
        "skipped": skipped_external,
    }

if __name__ == "__main__":
    result = main()
    # Save result for inspection
    with open(r"E:\HermesPortable\home\spaces\tirol-tourismus\kanban\boards\wordstructor-polish\workspaces\t_a3b45a97\linkcheck_result.json", "w") as f:
        import json
        json.dump(result, f, indent=2, ensure_ascii=False)
