# use latest python 3 alpine image.
FROM python:3-alpine

# install system dependencies.
RUN apk update && apk add --no-cache \
  gcc libc-dev g++ graphviz git bash go imagemagick inkscape ttf-opensans curl fontconfig xdg-utils

# install go package.
RUN go install github.com/mingrammer/round@latest

# install fonts
RUN curl -O https://noto-website.storage.googleapis.com/pkgs/NotoSansCJKjp-hinted.zip \
&& mkdir -p /usr/share/fonts/NotoSansCJKjp \
&& unzip NotoSansCJKjp-hinted.zip -d /usr/share/fonts/NotoSansCJKjp/ \
&& rm NotoSansCJKjp-hinted.zip \
&& fc-cache -fv

# add go bin to path.
ENV PATH "$PATH:/root/go/bin"

# project directory.
WORKDIR /usr/src/diagrams

# Copy the rest of your app's source code from your host to your image filesystem.
COPY . .

# install python requirements.
RUN pip install black graphviz jinja2
