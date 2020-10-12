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
from appdirs import AppDirs

if sys.version_info.major < 3 and sys.version_info.minor < 6:
    raise Exception("Must be using Python 3.6 or greater")

if __name__ == "__main__":

    parser = argparse.ArgumentParser("Download YouTube subscriptions.")
    parser.add_argument(
        "--save-directory",
        "-o",
        dest="output",
        default=None,
        help="The directory to which to save the videos.",
    )
    parser.add_argument(
        "--retain",
        "-c",
        dest="retain",
        default=None,
        help="Retain videos up to the given number of days since today.",
    )
    parser.add_argument(
        "--since",
        "-s",
        dest="since",
        default=None,
        help="Only download videos newer than the given number of days.",
    )
    parser.add_argument(
        "--config-directory",
        "-f",
        dest="config",
        default=None,
        help="The directory to which config is saved.",
    )

    args = parser.parse_args()

    # The current run time.
    script_time = time()

    subsPath = "subs.xml"
    if args.config is not None:
        subsPath = f"{args.config}/{subsPath}"
    outlines = opml.parse(subsPath)

    if args.output is not None:
        args.output = Path(args.output).absolute()
        os.chdir(args.output)
    else:
        print("Must specify an ouput directory with -o")

    lastPath = "last.txt"
    if args.config is not None:
        lastPath = f"{args.config}/{lastPath}"

    if not Path(lastPath).exists():
        with open(lastPath, "w") as f:
            f.write(str(time()))
            print("Initialized a last.txt file with current timestamp.")
    else:
        with open(lastPath, "r") as f:
            # The last run time.
            threshold_time = datetime.utcfromtimestamp(float(f.read()))

        # Overrule the time from which to download video if we've been asked to
        # keep videos since a certain number of days ago.
        if args.since is not None:
            threshold_time = datetime.fromtimestamp(script_time) - relativedelta(
                days=float(args.since)
            )

        if args.retain is not None:
            # Find the videos in this directory which are older than the time
            # stamp since the last run and remove them.
            keep_time = datetime.fromtimestamp(script_time) - relativedelta(
                days=float(args.retain)
            )
            for video in Path(".").glob("**/*.*"):
                if "last.txt" in str(video):
                    continue
                modified_time = datetime.utcfromtimestamp(os.path.getmtime(video))
                if modified_time < keep_time:
                    print(f"Removing {str(video)}.")
                    video.unlink()

        urls = [outline.xmlUrl for outline in outlines[0]]

        videos = []
        for i, url in enumerate(urls):
            print(f"Parsing through channel {i + 1} of {len(urls)}", end="\r")
            feed = feedparser.parse(url)
            for item in feed["items"]:
                video_time = datetime.fromtimestamp(mktime(item["published_parsed"]))
                if video_time > threshold_time:
                    videos.append(item["link"])

        print(" " * 100, end="\r")
        if len(videos) == 0:
            print("Sorry, no new video found")
            quit()
        else:
            print(f"{len(videos)} new videos found")

        ydl_opts = {
            "ignoreerrors": True,
            "quiet": True,
            "outtmpl": (
                args.output / Path("%(uploader)s", "%(title)s.%(ext)s")
            ).as_posix(),
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(videos)

        with open(lastPath, "w") as f:
            f.write(str(script_time))
