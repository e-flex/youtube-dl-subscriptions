#!/usr/bin/env python3

import opml
import feedparser
import youtube_dl
import sys
from pathlib import Path

if sys.version_info[0] < 3:
    raise Exception('Must be using Python 3')

from time import time, mktime, strptime
from datetime import datetime

outlines = opml.parse('subs.xml')

if not Path('last.txt').exists():
    with open('last.txt', 'w') as f:
        f.write(str(time()))
        print('Initialized a last.txt file with current timestamp.')
else:
    with open('last.txt', 'r') as f:
        content = f.read()
        # The last run time.
        ptime = datetime.utcfromtimestamp(float(content))



    urls = []

    for outline in outlines[0]:
        urls.append(outline.xmlUrl)

    videos = []
    for i, url in enumerate(urls):
        print(f'Parsing through channel {i + 1} of {len(urls)}', end='\r')
        feed = feedparser.parse(url)
        for item in feed['items']:
            timef = item['published_parsed']
            dt = datetime.fromtimestamp(mktime(timef))
            if dt > ptime:
                videos.append(item['link'])

    if len(videos) == 0:
        print('Sorry, no new video found')
    else:
        print(f'{len(videos)} new videos found')

    ydl_opts = {'ignoreerrors': True}

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(videos)

    with open('last.txt', 'w') as f:
        f.write(str(ftime))
