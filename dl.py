#!/usr/bin/env python3

import opml
import feedparser
import youtube_dl
import sys
from pathlib import Path
from glob import glob
from pprint import pprint

if sys.version_info[0] < 3:
    raise Exception('Must be using Python 3')

from time import time, mktime, strptime
from datetime import datetime


if not Path('last.txt').exists():
    with open('last.txt', 'w') as f:
        f.write(str(time()))
        print('Initialized a last.txt file with current timestamp.')
else:
    with open('last.txt', 'r') as f:
        content = f.read()
        # The last run time.
        ptime = datetime.utcfromtimestamp(float(content))

    outline = opml.parse('subs.xml')

    ptime = datetime.utcfromtimestamp(float(content))
    ftime = time()

    urls = []

    for i in range(0,len(outline[0])):
        urls.append(outline[0][i].xmlUrl)

    videos = []
    for i in range(0,len(urls)):
        print('Parsing through channel '+str(i+1)+' out of '+str(len(urls)), end='\r')
        feed = feedparser.parse(urls[i])
        for j in range(0,len(feed['items'])):
            timef = feed['items'][j]['published_parsed']
            dt = datetime.fromtimestamp(mktime(timef))
            if dt > ptime:
                videos.append(feed['items'][j]['link'])

    if len(videos) == 0:
        print('Sorry, no new video found')
    else:
        print(str(len(videos))+' new videos found')

    ydl_opts = {'ignoreerrors': True}

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(videos)

    with open('last.txt', 'w') as f:
        f.write(str(ftime))
