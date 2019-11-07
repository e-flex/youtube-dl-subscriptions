#!/usr/bin/env sh

docker run --rm \
    -v <video-output>:/youtube  -v <configs>:/config \
    youtube-dl-subscriptions \
    --save-directory /youtube --config-directory /config --retain 14
