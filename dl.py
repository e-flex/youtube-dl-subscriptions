#!/usr/bin/env python3

import os
import opml
import feedparser
import youtube_dl
import sys
from pathlib import Path
import argparse
from time import time, mktime, strptime
from datetime import datetime
from dateutil.relativedelta import relativedelta

if sys.version_info.major < 3 and sys.version_info.minor < 6:
    raise Exception('Must be using Python 3.6 or greater')

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Download YouTube subscriptions.')
    parser.add_argument('--save-directory', '-o',
                        dest='output',
                        default=None,
                        help='The directory to which to save the videos.')
    parser.add_argument('--retain', '-c',
                        dest='retain',
                        default=None,
                        help='Retain videos up to the given number of days since today.')
    parser.add_argument('--since', '-s',
                        dest='since',
                        default=None,
                        help='Only download videos newer than the given number of days.')

    args = parser.parse_args()

    # The current run time.
    ftime = time()

    outlines = opml.parse('subs.xml')
    
    if args.output is not None:
        os.chdir(Path(args.output).absolute())

    if not Path('last.txt').exists():
        with open('last.txt', 'w') as f:
            f.write(str(time()))
            print('Initialized a last.txt file with current timestamp.')
    else:
        with open('last.txt', 'r') as f:
            content = f.read()
            # The last run time.
            ptime = datetime.utcfromtimestamp(float(content))
        # Overrule the time from which to download video if we've been asked to
        # keep videos since a certain number of days ago.
        if args.since is not None:
            threshold_time = datetime.fromtimestamp(script_time) - relativedelta(days=float(args.since))

        if args.retain is not None:
            # Find the videos in this directory which are older than the time
            # stamp since the last run and remove them.
            keeptime = datetime.fromtimestamp(ftime) - relativedelta(days=float(args.retain))
            for video in Path('.').glob('*.mp4'):
                mtime = datetime.utcfromtimestamp(os.path.getmtime(video))
                if mtime < keeptime:
                    print(f'Removing {str(video)}.')
                    video.unlink()
    
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
    
        ydl_opts = {'ignoreerrors': True, 'quiet': True}
    
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(videos)
    
        with open('last.txt', 'w') as f:
            f.write(str(ftime))
