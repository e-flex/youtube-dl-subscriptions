FROM alpine:3.10

WORKDIR /code

COPY requirements.txt /code/requirements.txt

RUN apk add --no-cache --virtual py-build-deps gcc libc-dev libxslt-dev python3-dev && \
    apk add --no-cache python3 libxslt && \
    pip3 install -r requirements.txt && \
    apk del py-build-deps

# Copy this after installing since it changes the most frequently, to take
# advantage of the image layer caching.
COPY dl.py /code/dl.py

ENTRYPOINT ["python3", "dl.py"]
