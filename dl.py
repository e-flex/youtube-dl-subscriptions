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
from icecream import ic

if sys.version_info.major < 3 and sys.version_info.minor < 6:
    raise Exception("Must be using Python 3.6 or greater")

xdgDirs = AppDirs("yt-dl-subs")

if __name__ == "__main__":

    parser = argparse.ArgumentParser("Download YouTube subscriptions.")
    parser.add_argument(
        "--output-path",
        "-o",
        default=Path().home() / "Videos" / "YT Subs",
        help="The directory to which to save the videos. Default $HOME/Videos/YT Subs",
    )
    parser.add_argument(
        "--retain",
        "-r",
        default=None,
        help="Retain videos up to the given number of days since today. Default: None",
    )
    parser.add_argument(
        "--since",
        "-s",
        default=None,
        help="Only download videos newer than the given number of days. Default: None",
    )
    parser.add_argument(
        "--config-path",
        "-f",
        default=Path(xdgDirs.user_config_dir),
        help="The directory to which config is saved. Default: $XDG_CONFIG_HOME/yt-dl-subs",
    )
    parser.add_argument(
        "--create-directories",
        default=False,
        help="Create all directories if they do not exist. Default: False"
    )

    args = parser.parse_args()

    ic(args)

    # The current run time.
    scriptStartTime = time()

    if isinstance(args.config_path, str):
        confDir = Path(args.config_path)
    else:
        confDir = args.config_path

    if isinstance(args.output_path, str):
        outputPath = Path(args.output_path)
    else:
        outputPath = args.output_path

    stateDir = Path(xdgDirs.user_state_dir)

    if args.create_directories:
        ic("Creating directories.")
        if not confDir.exists():
            confDir.mkdir(parents=True)
        if not outputPath.exists():
            outputPath.mkdir(parents=True)
        if not stateDir.exists():
            stateDir.mkdir(parents=True)
        exit()

    lastFile = stateDir / "last.time"
    subsXMLFile = confDir / "subs.xml"
    outlines = opml.parse(subsXMLFile.open())
    # outlines = etree.parse(subsXMLFile.open())
    
    if not lastFile.exists():
        lastFile.write_text(str(time()))
    else:
        # Overrule the time from which to download video if we've been asked to
        # keep videos since a certain number of days ago.
        if args.since is not None:
            sinceTimestamp = datetime.now() - relativedelta(days=int(args.since))
        else:
            sinceTimestamp = datetime.fromtimestamp(float(lastFile.read_text()))

        if args.retain is not None:
            # Find the videos in this directory which are older than the time
            # stamp since the last run and remove them.
            retainTimestamp = datetime.now() - relativedelta(
                days=int(args.retain)
            )
            for video in outputPath.glob("**/*.*"):
                modifiedTime = datetime.fromtimestamp(video.stat().st_mtime)
                ic(modifiedTime)
                if modifiedTime < retainTimestamp:
                    print(f"Removing {str(video)}.")
                    video.unlink()

        videoURLs = [outline.xmlUrl for outline in outlines[0]]

        ic(sinceTimestamp)
        # ic(retainTimestamp)
        ic(videoURLs[:10])
        input("Continue.")

        videos = []
        for i, url in enumerate(videoURLs):
            print(f"Parsing through channel {i + 1} of {len(videoURLs)}")
            ic(i, url)
            feed = feedparser.parse(url)
            # if len(feed["items"]):
            #     ic(feed['items'][0])
            for item in feed["items"]:
                video_time = datetime.fromtimestamp(mktime(item["published_parsed"]))
                ic(video_time)
                if video_time > sinceTimestamp:
                    ic(item["link"])
                    videos.append(item["link"])
            # input("Continue")

        print("---")
        if len(videos) == 0:
            print("Sorry, no new video found")
            quit()
        else:
            print(f"{len(videos)} new videos found")

        ydl_opts = {
            "ignoreerrors": True,
            "quiet": False,
            "outtmpl": (
                outputPath / "%(uploader)s - %(title)s.%(ext)s").as_posix(),
            "format": "best"
        }
        ic(ydl_opts)
        input("Continue")

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(videos)

        lastFile.write_text(str(datetime.now()))
