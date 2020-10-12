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
        default=None,
        help="Retain videos up to the given number of days since today. Default: None",
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
    parser.add_argument(
        "--no-download",
        default=False,
        help="Set this to not download any videos.",
        action="store_true"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        default=False,
        help="Reduce the output.",
        action="store_true"
    )

    args = parser.parse_args()
    if args.debug:
        ic.enable()

    ic(args)

    if args.retain < args.since:
        print("It is not a good idea to remove newer files than what you want to download.")
        if input("Continue y/[n]: ").lower() != "y":
            quit()

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
    feedURLs = [outline.xmlUrl for outline in outlines[0]]
    if args.debug:
        feedURLs = feedURLs[:12]
    ic(feedURLs[:10])

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

    # Nothing is purged by default
    if args.retain is not None:
        # Create a timestamp that points to a time a couple of days ago
        # using the retain option.
        retainTimestamp = datetime.now() - relativedelta(days=int(args.retain))
        # Loop over all the files in the output directory and
        # remove all that are older that the retainTimestamp
        for video in outputPath.glob("**/*.*"):
            modifiedTime = datetime.fromtimestamp(video.stat().st_mtime)
            ic(modifiedTime)
            ic(retainTimestamp)
            if modifiedTime < retainTimestamp:
                if not args.quiet:
                    print(f"Removing {str(video)}.")
                video.unlink()

    # Loop over the feed URLs and get the latest uploads
    videoURLs = []
    for i, url in enumerate(feedURLs):
        if not args.quiet:
            print(f"Parsing through channel {i + 1} of {len(feedURLs)}")
        ic("Feed URL:", url)
        feed = feedparser.parse(url)
        for item in feed["items"]:
            publishedDate = datetime.fromtimestamp(mktime(item["published_parsed"]))
            ic(publishedDate)
            if publishedDate > sinceTimestamp:
                ic(item["link"])
                videoURLs.append(item["link"])

    if len(videoURLs) == 0:
        print("No new video found")
        quit()
    elif not args.quiet:
        print(f"{len(videoURLs)} new videos found")

    ydl_opts = {
        "ignoreerrors": True,
        "quiet": args.quiet,
        "outtmpl": (
            outputPath / "%(uploader)s - %(title)s.%(ext)s").as_posix(),
        "format": "best"
    }
    ic(ydl_opts)

    if not args.debug and not args.quiet:
        print("Downloading the videos now...")

    if not args.no_download:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(videoURLs)
    elif not args.quiet:
        ic(videoURLs)
        print("This is a dry run, nothing is downloaded.")

    lastFile.write_text(str(datetime.now()))
    if not args.quiet:
        print("Finished downloading videos.")
