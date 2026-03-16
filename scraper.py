#code heavily inspired by: https://www.zenrows.com/blog/find-all-urls-on-a-domain#custom-link-extractor

import csv
import time
from collections import deque
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

# set the first page to crawl.
start_url = "https://bcswomenlovelace.bcs.org/"
# set crawl limits.
max_pages = 10000
max_depth = 2
# add a short pause between requests.
delay = 0.1
timeout = 20
# print progress every n fetched pages.
log_every = 10
output_csv = "lovelace_urls.csv"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.46 Safari/537.36"
# keep crawl within the start path when true.
restrict_to_start_path = True


def normalize_link(raw_link: str, page_url: str) -> str | None:
    # skip empty href values.
    if not raw_link:
        return None
    # convert relative links to absolute links.
    parsed = urlparse(urljoin(page_url, raw_link.strip()))
    # keep only http/https links.
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    # drop fragments so one page has one canonical URL.
    parsed = parsed._replace(fragment="")
    # normalize empty paths to root.
    clean_path = parsed.path or "/"
    return urlunparse((parsed.scheme, parsed.netloc, clean_path, parsed.params, parsed.query, ""))


def save_csv(urls: list[str], path: str) -> None:
    # write discovered URLs as one row per URL.
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["url", "status_code"])
        for url, status in urls.items():
            writer.writerow([url, status])


def canonical_host(host: str) -> str:
    # normalize www and non-www hosts to the same form.
    h = (host or "").lower()
    return h[4:] if h.startswith("www.") else h


def is_in_start_scope(url: str, scope_path: str) -> bool:
    # allow full-domain crawl when scope is root.
    if scope_path == "/":
        return True
    # otherwise allow only same path or child paths.
    path = (urlparse(url).path or "/").rstrip("/")
    base = scope_path.rstrip("/")
    return path == base or path.startswith(base + "/")


def main() -> None:
    # build canonical domain once for same-domain checks.
    domain = canonical_host(urlparse(start_url).hostname or "")
    # reuse one session for faster repeated requests.
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})

    # normalize the seed URL before enqueuing.
    seed_url = normalize_link(start_url, start_url)
    if not seed_url:
        raise ValueError(f"Invalid start_url: {start_url}")
    # compute scope path once for optional path restriction.
    scope_path = (urlparse(seed_url).path or "/").rstrip("/") or "/"

    # store items as (url, depth) for breadth-first crawl.
    queue: deque[tuple[str, int]] = deque([(seed_url, 0)])
    # prevent duplicate queue entries.
    seen_or_queued: set[str] = {seed_url}
    # track all accepted URLs for output.
    discovered: dict[str, int] = {seed_url: 0}
    pages_fetched = 0
    started_at = time.time()

    print(f"Domain: {domain}")
    print(f"Limits: max_pages={max_pages}, max_depth={max_depth}, delay={delay}s")

    while queue and pages_fetched < max_pages:
        # pop oldest queued URL (breadth-first order).
        current_url, depth = queue.popleft()
        if depth > max_depth:
            continue

        if pages_fetched % log_every == 0:
            elapsed = time.time() - started_at
            rate = pages_fetched / elapsed if elapsed > 0 else 0.0
            print(f"Progress: fetched={pages_fetched}, queued={len(queue)}, discovered={len(discovered)}, rate={rate:.2f} pages/s")

        print(f"GET depth={depth} {current_url}")
        try:
            # follow redirects so extracted links come from final page.
            response = session.get(current_url, timeout=timeout, allow_redirects=True)
        except requests.RequestException as exc:
            pages_fetched += 1
            print(f"ERROR request failed: {current_url} ({type(exc).__name__}: {exc})")
            if delay > 0:
                time.sleep(delay)
            continue

        pages_fetched += 1
        status_code = response.status_code
        content_type = (response.headers.get("Content-Type") or "").lower()
        discovered[current_url] = status_code
        final_url = str(response.url)

        # log redirect target so URL flow is visible.
        if final_url != current_url:
            print(f"Redirected to: {final_url}")
        # skip non-success and non-HTML pages.

        if not ("text/html" in content_type or "application/xhtml+xml" in content_type or content_type == ""):
            print(f"SKIP status={status_code} content-type={content_type}")
            if delay > 0:
                time.sleep(delay)
            continue

        # parse HTML and collect normalized anchor links.
        soup = BeautifulSoup(response.text, "html.parser")
        page_links: set[str] = set()
        base_for_links = final_url or current_url
        for anchor in soup.select("a[href]"):
            normalized = normalize_link(anchor.get("href"), base_for_links)
            if normalized:
                page_links.add(normalized)

        same_domain_links = 0
        newly_queued_links = 0
        # next links from this page move one level deeper.
        next_depth = depth + 1
        for link in page_links:
            host = canonical_host(urlparse(link).hostname or "")
            # keep only links on the same domain.
            is_domain_match = host == domain or host.endswith("." + domain)
            if not is_domain_match:
                continue
            
            # apply path scoping when enabled.
            if restrict_to_start_path and not is_in_start_scope(link, scope_path):
                continue

            same_domain_links += 1
            if link in discovered:
                continue

            discovered[link] = 0
            if link not in seen_or_queued and next_depth <= max_depth:
                seen_or_queued.add(link)
                queue.append((link, next_depth))
                newly_queued_links += 1

        print(f"Found links={len(page_links)} kept_same_domain={same_domain_links} new_queued={newly_queued_links} total_urls={len(discovered)}")
        if delay > 0:
            time.sleep(delay)

    elapsed = time.time() - started_at
    # sort output for stable CSV diffs.
    save_csv(discovered, output_csv)

if __name__ == "__main__":
    main()
