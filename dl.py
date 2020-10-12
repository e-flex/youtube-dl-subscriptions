#!/usr/bin/env python3

import opml
import feedparser
import youtube_dl
import sys
from pathlib import Path
import argparse
from time import time, mktime
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as dateparse
from appdirs import AppDirs
from icecream import ic

ic.disable()

if sys.version_info.major < 3 and sys.version_info.minor < 6:
    raise Exception("Must be using Python 3.6 or greater")

xdgDirs = AppDirs("yt-dl-subs")

if __name__ == "__main__":

    parser = argparse.ArgumentParser("Download YouTube subscriptions.")
    parser.add_argument(
        "--output-path",
        "-o",
        default=Path().home() / "Videos" / "YT Subs",
        help="The directory to which to save the videos.  Default $HOME/Videos/YT Subs",
        type=Path
    )
    parser.add_argument(
        "--retain",
        "-r",
        default=15,
        help="Retain videos up to the given number of days since today. Default: 15",
        type=int
    )
    parser.add_argument(
        "--since",
        "-s",
        default=14,
        help="Only download videos newer than the given number of days. Default: 14",
        type=int
    )
    parser.add_argument(
        "--config-path",
        "-c",
        default=Path(xdgDirs.user_config_dir),
        help="The directory to which config is saved. Default: $XDG_CONFIG_HOME/yt-dl-subs",
        type=Path
    )
    parser.add_argument(
        "--create-directories",
        default=False,
        help="Create all directories if they do not exist. Default: False",
        action="store_true"
    )
    parser.add_argument(
        "--debug",
        "-d",
        default=False,
        help="Print some more verbose debugging info.",
        action="store_true"
    )

    args = parser.parse_args()
    if args.debug:
        ic.enable()

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

    # Overrule the time from which to download video if we've been asked to
    # keep videos since a certain number of days ago.
    if args.since is not None:
        sinceTimestamp = datetime.now() - relativedelta(days=int(args.since))
    elif not lastFile.exists():
        lastFile.write_text(str(time()))
        sinceTimestamp = datetime.now() - relativedelta(days=7)
    else:
        sinceTimestamp = dateparse(lastFile.read_text())
        ic(sinceTimestamp)

    if args.retain is not None:
        # Find the videos in this directory which are older than the time
        # stamp since the last run and remove them.
        retainTimestamp = datetime.now() - relativedelta(
            days=int(args.retain)
        )
        ic(retainTimestamp)
        for video in outputPath.glob("**/*.*"):
            modifiedTime = datetime.fromtimestamp(video.stat().st_mtime)
            ic(modifiedTime)
            if modifiedTime < retainTimestamp:
                print(f"Removing {str(video)}.")
                video.unlink()
                ic(sinceTimestamp)

    videoURLs = [outline.xmlUrl for outline in outlines[0]]

    ic(videoURLs[:10])

    videos = []
    for i, url in enumerate(videoURLs):
        print(f"Parsing through channel {i + 1} of {len(videoURLs)}")
        ic(i, url)
        feed = feedparser.parse(url)
        for item in feed["items"]:
            video_time = datetime.fromtimestamp(mktime(item["published_parsed"]))
            ic(video_time)
            if video_time > sinceTimestamp:
                ic(item["link"])
                videos.append(item["link"])

    if len(videos) == 0:
        print("Sorry, no new video found")
        quit()
    else:
        print(f"{len(videos)} new videos found")

    ydl_opts = {
        "ignoreerrors": True,
        "quiet": args.debug,
        "outtmpl": (
            outputPath / "%(uploader)s - %(title)s.%(ext)s").as_posix(),
        "format": "best"
    }
    ic(ydl_opts)

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(videos)

    lastFile.write_text(str(datetime.now()))
