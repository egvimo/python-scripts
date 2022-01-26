#!/usr/bin/env python3

from pathlib import Path
import re
import feedparser
import requests


URL = 'https://enny-und-mo.podigee.io/feed/mp3'


def extract_name(entry):
    episode = entry.itunes_episode
    name = re.sub('Enny und Mo: ', '', entry.title)
    filename = "".join([c for c in name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    return f"{episode} - {filename}"

def extract_link(entry):
    for link in entry.links:
        if link.type == 'audio/mpeg':
            return link.href
    return None

def download_file(link, name):
    Path('out/').mkdir(parents=True, exist_ok=True)
    response = requests.get(link)
    with open(f"out/{name}.mp3", 'wb') as file:
        file.write(response.content)

def parse_feed():
    feed = feedparser.parse(URL)

    for entry in feed.entries:
        link = extract_link(entry)
        name = extract_name(entry)
        print(name)
        download_file(link, name)

if __name__ == '__main__':
    parse_feed()
