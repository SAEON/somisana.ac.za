"""Draft SOMISANA News cards from SAEON eNews RSS."""
import argparse
from email.utils import parsedate_to_datetime
from html import escape
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FEED = "https://enews.saeon.ac.za/feed/"
HOST = "enews.saeon.ac.za"
MARKER = "          <!-- Add the new story cards here, newest first. -->"
ROSTER = {
    "Jennifer Veitch": ("Jennifer Veitch", "Jenny Veitch"),
    "Giles Fearon": ("Giles Fearon",),
    "Nkululeko Memela": ("Nkululeko Memela", "Nkuleleko Memela", "Nkuleleko Charles Memela"),
    "Gustav Rautenbach": ("Gustav Rautenbach",),
    "Philile Mvula": ("Philile Mvula",),
}
BLOCKS = {"p", "h1", "h2", "h3", "h4", "div", "section", "li", "br"}
NAME = r"[A-Z][^\W\d_]*(?:[’'\-][^\W\d_]+)*"
PERSON = re.compile(rf"(?:{NAME}|[dDvV][’']?{NAME}|van|der|de)(?:\s+(?:{NAME}|[dDvV][’']?{NAME}|van|der|de))+")


class Blocks(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.blocks = []
        self.parts = []
        self.images = []
        self.feed(markup)
        self.flush()

    def flush(self):
        text = " ".join("".join(self.parts).split())
        if text:
            self.blocks.append(text)
        self.parts.clear()

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            attrs = dict(attrs)
            url = attrs.get("src") or ""
            if urlsplit(url).scheme == "https":
                self.images.append(url)
        if tag in BLOCKS:
            self.flush()

    def handle_endtag(self, tag):
        if tag in BLOCKS:
            self.flush()

    def handle_data(self, data):
        self.parts.append(data)


def canonical(url):
    parsed = urlsplit(url.strip())
    if parsed.scheme == "https" and parsed.netloc.lower() == HOST and parsed.path.strip("/"):
        return f"https://{HOST}/{parsed.path.strip('/')}/"
    return ""


def byline_names(text):
    text = re.sub(r"^(?:written by|by)\s+", "", text, flags=re.I)
    names = []
    for part in re.split(r"\s*(?:[,;]|\band\b|&)\s*", text):
        part = re.sub(r"^(?:(?:Dr|Prof|Mr|Ms|Mrs|Professor)\.?\s+)+", "", part)
        if not PERSON.fullmatch(part):
            break
        names.append(part)
    return names


def matching_authors(names):
    return [
        name for name, aliases in ROSTER.items()
        if any(author.casefold() == alias.casefold() for alias in aliases for author in names)
    ]


def read_feed(location):
    if location:
        return Path(location).read_bytes()
    with urlopen(Request(FEED, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as response:
        return response.read()


def find_stories(feed, homepage):
    channel = ET.fromstring(feed).find("channel")
    if channel is None or not channel.findall("item"):
        raise ValueError("RSS response contained no article items")
    existing = {canonical(url) for url in re.findall(r'href="([^"]+)"', homepage)}
    seen = set()
    drafts = []
    report = []
    for item in channel.findall("item"):
        url = canonical(item.findtext("link", ""))
        title = item.findtext("title", "").strip()
        if not url or not title or url in seen:
            continue
        seen.add(url)
        content = Blocks(item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded", ""))
        body = content.blocks
        if body and body[0].casefold() == title.casefold():
            body = body[1:]
        # A WordPress feed creator can be the editor account. Use the article's
        # opening byline, before the body text, as the evidence for a match.
        opening = body[0] if body else ""
        marked = bool(re.match(r"^(?:written by|by)\s+", opening, re.I))
        names = byline_names(opening)
        if not marked and len(names) < 2:
            names = []
        authors = matching_authors(names)
        if url in existing:
            report.append(f"Already on site: {title}" + (f" ({', '.join(authors)})" if authors else ""))
            continue
        if not authors:
            if not names:
                report.append(f"Review byline: {title}")
            continue
        try:
            published = parsedate_to_datetime(item.findtext("pubDate", ""))
            if published.tzinfo is None:
                raise ValueError("Missing timezone")
        except (TypeError, ValueError):
            report.append(f"Review publication date: {title}")
            continue
        description = Blocks(item.findtext("description", "")).blocks
        paragraphs = [text for text in (*description, *body[1:]) if len(text) >= 65]
        if not paragraphs:
            report.append(f"Review summary: {title}")
            continue
        summary = paragraphs[0].split(" The post ", 1)[0].removesuffix(" […]")
        if len(summary) > 225:
            summary = summary[:222].rsplit(" ", 1)[0] + "…"
        drafts.append((published, title, url, names, summary, f"{published.day} {published:%B %Y}"))
        report.append(f"Drafted: {title} ({', '.join(authors)})")
        for image in dict.fromkeys(content.images):
            report.append(f"  Article image to review: {image}")
    return sorted(drafts, key=lambda draft: draft[0], reverse=True), report


def find_archive_stories(homepage):
    from enews_archive import fetch_candidates

    urls = {canonical(url) for url in re.findall(r'href="([^"]+)"', homepage)}
    drafts, report = [], []
    for article, note in fetch_candidates(urls, canonical):
        if note:
            report.append(note)
            continue
        sort_date, title, url, byline, summary, issue = article
        names = byline_names(byline)
        if matching_authors(names):
            excerpt = summary if len(summary) <= 225 else summary[:222].rsplit(" ", 1)[0] + "…"
            drafts.append((sort_date, title, url, names, excerpt, issue))
            report.append(f"Drafted: {title}")
    return sorted(drafts, key=lambda draft: draft[0], reverse=True), report


def render_card(draft, photos):
    _, title, url, authors, summary, date = draft
    photo = photos.get(url)
    image = ""
    if photo:
        path = Path(photo["path"])
        if path.is_absolute() or path.parts[:2] != ("public", "news") or ".." in path.parts:
            raise ValueError("Approved article photos must be stored under public/news")
        credit = photo["credit"].strip()
        if not credit or not (ROOT / path).is_file():
            raise ValueError(f"Missing approved article photo or credit: {path}")
        image = (
            f'<img class="news-article-photo" src="{escape(path.as_posix())}" alt="" />'
            f'<small class="news-photo-credit">{escape(credit)}</small>'
        )
    title, url, summary = map(escape, (title, url, summary))
    matched = {alias.casefold() for name in matching_authors(authors) for alias in ROSTER[name]}
    byline = ", ".join(
        f"<strong>{escape(author)}</strong>" if author.casefold() in matched else escape(author)
        for author in authors
    )
    return f'''          <article class="home-testimonial-card">{image}
            <div class="home-card-heading">
              <div class="home-name-and-position">
                <a href="{url}" target="_blank" rel="noopener noreferrer"
                  class="home-name"><strong>{title}</strong></a>
                <span class="home-position">{date}</span>
              </div>
            </div>
            <p class="home-text77">{summary}</p>
            <footer class="news-card-footer">
              <p class="news-byline">By {byline}</p>
              <strong class="news-read-more">Read more on SAEON eNews ↗</strong>
            </footer>
          </article>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed-file", help="Use saved RSS XML instead of requesting the live feed")
    parser.add_argument("--preview", type=Path, help="Write a separate HTML preview with draft cards")
    parser.add_argument("--manifest", type=Path, help="Write draft titles and links as JSON")
    parser.add_argument("--photos", type=Path, help="JSON mapping article URLs to approved photo paths and credits")
    args = parser.parse_args()
    homepage = ROOT / "index.html"
    source = homepage.read_text(encoding="utf-8")
    try:
        try:
            drafts, report = find_stories(read_feed(args.feed_file), source)
        except (URLError, ET.ParseError, ValueError) as error:
            if args.feed_file:
                raise
            print(f"Trying the eNews issue archive: {error}", file=sys.stderr)
            drafts, report = find_archive_stories(source)
        if args.manifest:
            args.manifest.write_text(json.dumps([
                {"title": draft[1], "url": draft[2]} for draft in drafts
            ], ensure_ascii=False), encoding="utf-8")
        if args.preview:
            if source.count(MARKER) != 1:
                raise ValueError("News insertion marker is missing or duplicated")
            photos = json.loads(args.photos.read_text(encoding="utf-8")) if args.photos else {}
            cards = [render_card(draft, photos) for draft in drafts]
            preview = source.replace(MARKER, "\n".join([MARKER, *cards]), 1)
            with args.preview.open("x", encoding="utf-8") as handle:
                handle.write(preview)
    except (OSError, URLError, ET.ParseError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Could not draft News cards: {error}\n")
    print(*report, sep="\n")
    print(f"{len(drafts)} draft card(s) ready for review.")


if __name__ == "__main__":
    sys.exit(main())
