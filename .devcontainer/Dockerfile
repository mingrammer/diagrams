# use latest python 3 alpine image.
FROM python:3-alpine

# install system dependencies.
RUN apk update && apk add --no-cache \
  gcc libc-dev g++ graphviz git bash go imagemagick inkscape ttf-opensans curl fontconfig xdg-utils \
  nodejs npm

# install go package.
RUN go install github.com/mingrammer/round@latest

# install fonts
RUN curl -L -O https://github.com/notofonts/noto-cjk/releases/download/Sans2.004/06_NotoSansCJKjp.zip \
&& mkdir -p /usr/share/fonts/NotoSansCJKjp \
&& unzip 06_NotoSansCJKjp.zip -d /usr/share/fonts/NotoSansCJKjp/ \
&& rm 06_NotoSansCJKjp.zip \
&& fc-cache -fv

# add go bin to path.
ENV PATH "$PATH:/root/go/bin"

# project directory.
WORKDIR /usr/src/diagrams

# Copy the rest of your app's source code from your host to your image filesystem.
COPY . .

# install python requirements.
RUN pip install black graphviz jinja2
