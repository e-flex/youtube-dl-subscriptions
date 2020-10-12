# youtube-dl-subscriptions

Downloads all new videos from your YouTube subscription feeds.


## Requirements

This script requires Python 3. Additional dependencies can be found in the `requirements.txt` file.


## Usage

### Docker

```
git clone https://github.com/tgrosinger/youtube-dl-subscriptions

./build.sh
cp run.example.sh run.sh

# Make necessary changes in run.sh

./run.sh
```

### Running Locally

If you do not want to use Docker, you can instead setup the dependencies to run
this script from your locally installed python.

Clone the repository

    git clone https://github.com/e-flex/youtube-dl-subscriptions.git

Install the requirements

    pip install -r requirements.txt
	
Set up the directories to be used

	dl.py --create-directories
	
Alternatively

	dl.py --output-path='your/downloads' --config-path='~/.your/config/dir' --create-directories

Download your YouTube's subscriptions OPML file by visiting [this URL](https://www.youtube.com/subscription_manager?action_takeout=1). Save the file as `subs.xml` to either the default conf path, `$XDG_CONFIG_HOME/yt-dl-subs/`, or the one set by the `-c` flag.

You can then run the script

    $ dl.py

A `last.time` file will be created in order to avoid downloading the same videos on the next run, if you have already removed them, this means that the program will remember the last time it was run and as it is alwasy downloading videos up until the day it is being run, this timestamp will suffice.

## Credits

Based on the work from: [mewfree](https://github.com/mewfree/youtube-dl-subscriptions/) and [pwcazenave](https://github.com/pwcazenave/youtube-dl-subscriptions) and [tgrosinger](https://github.com/tgrosinger/youtube-dl-subscriptions).
