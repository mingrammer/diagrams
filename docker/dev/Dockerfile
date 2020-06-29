# use latest python alphine image.
FROM python:rc-alpine3.12

# install system dependencies.
RUN apk update && apk add --no-cache \
  gcc libc-dev g++ graphviz git bash go imagemagick inkscape

# install go package.
RUN go get github.com/mingrammer/round

# add go bin to path.
ENV PATH "$PATH:/root/go/bin"

# project directory.
WORKDIR /usr/src/diagrams

# Copy the rest of your app's source code from your host to your image filesystem.
COPY . .

# install python requirements.
RUN pip install black
