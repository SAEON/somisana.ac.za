"""Read the public eNews issue archive when its RSS feed is empty."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
import re

from lxml import html

BASE = "https://enews.saeon.ac.za/"
ISSUE_PATH = re.compile(r"/issue-(\d{2})-(\d{4})(?:-\d+)?/?$")


def get_page(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"})
    with urlopen(request, timeout=20) as response:
        return html.fromstring(response.read(3_000_000), base_url=response.url)


def norm(element):
    return " ".join(element.text_content().split())


def issue_links(document):
    issues = {}
    for link in document.xpath("//a/@href"):
        url = urljoin(BASE, link)
        parsed = urlsplit(url)
        match = ISSUE_PATH.fullmatch(parsed.path)
        if parsed.scheme == "https" and parsed.netloc == urlsplit(BASE).netloc and match:
            number, year = map(int, match.groups())
            issues[(year, number)] = url
    return sorted(issues.items(), reverse=True)[:2]


def fetch_candidates(known_urls, canonical):
    issues = issue_links(get_page(urljoin(BASE, "previous-issues/")))
    if not issues:
        raise ValueError("SAEON eNews archive exposed no issue links")
    pending = {}
    found = set()
    for (year, issue), issue_url in issues:
        document = get_page(issue_url)
        links = document.xpath('//a[contains(concat(" ",normalize-space(@class)," ")," av-screen-reader-only ") and starts-with(normalize-space(.),"Link to:")]/@href')
        if not links:
            raise ValueError(f"No article links found on {issue_url}")
        for link in links:
            url = canonical(urljoin(issue_url, link))
            if url and url not in known_urls and not ISSUE_PATH.fullmatch(urlsplit(url).path):
                pending.setdefault(url, (year, issue))
            if url in known_urls:
                found.add(url)
    yield None, f"Archive checked {len(pending)} candidate articles and skipped {len(found)} existing links."

    def read_article(entry):
        url, (year, issue) = entry
        try:
            document = get_page(url)
        except URLError as error:
            return None, f"Could not read {url}: {error}"
        bylines = document.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," av-subheading_below ")]')
        for byline in bylines:
            headings = byline.getparent().xpath('./h1|./h2|./h3')
            if not headings or norm(byline).startswith("#"):
                continue
            title = norm(headings[0])
            paragraphs = [norm(p) for p in byline.xpath('following::p[ancestor::*[@id="main"]]')]
            summary = next((p for p in paragraphs if len(p) >= 65), "")
            if title and summary:
                sort_date = datetime(year, issue, 1, tzinfo=timezone.utc)
                return (sort_date, title, url, norm(byline), summary, f"Issue {issue:02d}, {year}"), None
        return None, f"Review byline or summary: {url}"

    with ThreadPoolExecutor(max_workers=5) as pool:
        yield from pool.map(read_article, pending.items())
