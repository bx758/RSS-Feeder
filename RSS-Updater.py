#!/usr/bin/env python3
"""Simple RSS updater that fetches and appends RSS feed items to a structured HTML file every hour."""

import html
import os
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime

OUTPUT_HTML = os.path.expanduser("~/Desktop/rss-updates.html")


def fetch_rss(url, timeout=20):
    request = urllib.request.Request(url, headers={"User-Agent": "RSSUpdater/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def parse_rss(xml_bytes):
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel") or root
    items = []
    for item in channel.findall("item"):
        items.append({
            "title": item.findtext("title", default="(no title)").strip(),
            "link": item.findtext("link", default="").strip(),
            "pubDate": item.findtext("pubDate", default="").strip(),
            "description": item.findtext("description", default="").strip(),
        })
    return items


def ensure_html_file(path):
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as html_file:
            html_file.write(
                "<!DOCTYPE html>\n"
                "<html lang=\"en\">\n"
                "<head>\n"
                "  <meta charset=\"utf-8\">\n"
                "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
                "  <title>RSS Updates</title>\n"
                "  <style>body{font-family:Arial,Helvetica,sans-serif;margin:1rem;}"
                "article{border:1px solid #ddd;padding:1rem;margin-bottom:1rem;border-radius:6px;}"
                "h2{margin-top:0;}li{margin-bottom:.75rem;}" 
                "p.meta{color:#555;font-size:.95rem;margin:0.25rem 0;}" 
                "</style>\n"
                "</head>\n"
                "<body>\n"
                "  <h1>RSS Updates</h1>\n"
                "  <div id=\"updates\"></div>\n"
                "</body>\n"
                "</html>\n"
            )


def append_feed_to_html(url, items, target_path):
    ensure_html_file(target_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_url = html.escape(url)
    article_parts = [
        f"<article>\n",
        f"  <h2>RSS update for <a href=\"{safe_url}\">{safe_url}</a></h2>\n",
        f"  <p class=\"meta\">Generated: {html.escape(now)}</p>\n",
    ]

    if not items:
        article_parts.append("  <p>No items found.</p>\n")
    else:
        article_parts.append("  <ul>\n")
        for item in items:
            title = html.escape(item["title"])
            link = html.escape(item["link"])
            pub_date = html.escape(item["pubDate"])
            description = html.escape(item["description"])
            line = f"    <li>\n"
            if link:
                line += f"      <a href=\"{link}\">{title}</a>\n"
            else:
                line += f"      {title}\n"
            if pub_date:
                line += f"      <p class=\"meta\">Published: {pub_date}</p>\n"
            if description:
                line += f"      <p>{description}</p>\n"
            line += "    </li>\n"
            article_parts.append(line)
        article_parts.append("  </ul>\n")

    article_parts.append("</article>\n")
    article_html = "".join(article_parts)

    with open(target_path, "r+", encoding="utf-8") as html_file:
        content = html_file.read()
        insert_pos = content.rfind("</body>")
        if insert_pos == -1:
            html_file.seek(0, os.SEEK_END)
            html_file.write(article_html)
        else:
            html_file.seek(insert_pos)
            html_file.write(article_html + content[insert_pos:])


def print_feed(url, items):
    print("---")
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} RSS update for {url}")
    if not items:
        print("No items found.")
        return
    for index, item in enumerate(items, start=1):
        print(f"{index}. {item['title']}")
        if item["pubDate"]:
            print(f"   Published: {item['pubDate']}")
        if item["link"]:
            print(f"   Link: {item['link']}")
    print("---\n")


def update_loop(url, interval_seconds=3600, target_path=OUTPUT_HTML):
    while True:
        try:
            xml = fetch_rss(url)
            items = parse_rss(xml)
            print_feed(url, items)
            append_feed_to_html(url, items, target_path)
        except Exception as exc:
            print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Error fetching RSS: {exc}")
        time.sleep(interval_seconds)


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python RSS-Updater.py <rss_feed_url> [output_html_path]")
        sys.exit(1)
    url = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) == 3 else OUTPUT_HTML
    print(f"Starting RSS hourly updater for: {url}")
    print(f"Appending updates to: {output_path}")
    update_loop(url, target_path=output_path)


if __name__ == "__main__":
    main()
