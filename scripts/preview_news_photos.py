"""Make a local preview using the featured image published with each eNews article."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.error import URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from draft_news import HOST, canonical

CARD = re.compile(r'(?ms)^          <(article|div) class="home-testimonial-card\d*">.*?^          </\1>')


class ArticleMetadata(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.images = {}
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag == "img" and fields.get("itemprop") == "thumbnailUrl":
            src = fields.get("src")
            if src and "/wp-content/uploads/" in src:
                self.images.setdefault("article:figure", src)
        if tag != "meta":
            return
        key = fields.get("property") or fields.get("name")
        value = fields.get("content")
        if key in ("og:image", "twitter:image") and value:
            self.images.setdefault(key, value)


def featured_image(url):
    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"})
        with urlopen(request, timeout=8) as response:
            if canonical(response.url) != url:
                return None
            metadata = ArticleMetadata(response.read(2_000_000).decode("utf-8", errors="replace"))
    except (OSError, URLError, ValueError) as error:
        print(f"{url}: {error}")
        return None
    candidate = next((
        metadata.images[key]
        for key in ("article:figure", "og:image", "twitter:image")
        if key in metadata.images
    ), "")
    if candidate:
        image = urljoin(url, candidate)
        parsed = urlsplit(image)
        if parsed.scheme == "https" and parsed.netloc == HOST and not re.search(
            r"logo|placeholder|default", parsed.path, re.I
        ):
            return image
    print(f"{url}: no article image found in the page metadata")
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("preview", type=Path)
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    cards = list(CARD.finditer(source))
    urls = [
        canonical(unescape(re.search(r'href="([^"]+)"', card[0])[1]))
        for card in cards
    ]
    with ThreadPoolExecutor(max_workers=4) as executor:
        images = list(executor.map(featured_image, urls))
    shown = 0
    for card, url, image in reversed(list(zip(cards, urls, images))):
        if not image or images.count(image) != 1 or 'class="news-article-photo"' in card[0]:
            continue
        tag = (
            f'\n            <img class="news-article-photo" src="{escape(image)}" '
            'alt="" referrerpolicy="no-referrer" />'
            '\n            <small class="news-photo-credit">Image from SAEON eNews</small>'
        )
        offset = source.index(">", card.start()) + 1
        source = source[:offset] + tag + source[offset:]
        shown += 1
        print(f"Using article image: {url}")
    with args.preview.open("x", encoding="utf-8") as handle:
        handle.write(source)
    print(f"Preview: {shown} of {len(cards)} cards have an article image.")


if __name__ == "__main__":
    main()
