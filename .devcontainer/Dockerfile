# This is all copied from `deploy/docker-containers/base/Dockerfile`
FROM python:3.12-slim-bullseye

RUN apt-get update && \
    apt-get install -y \
    wget \
    build-essential \
    zlib1g-dev

RUN pip3 uninstall PIL
RUN pip3 install --upgrade pip
RUN pip3 install fastapi
RUN pip3 install "uvicorn[standard]"
RUN pip3 install pytest
RUN pip3 install bs4
RUN pip3 install requests
RUN apt-get install -y libjpeg-dev libopenjp2-7 libtiff5 libfreetype6-dev
RUN pip3 install pillow
RUN pip3 install pyluach 

RUN apt-get -y install firefox-esr

RUN ln -fs /usr/share/zoneinfo/Israel /etc/localtime
ENV TZ="Israel"

RUN pip3 install zmanim
RUN pip3 install pyowm
RUN pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
RUN pip3 install pygsheets

# From this point onward are the things added for the devcontainer

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git

# # TODO: Use a temporary container (named "builder") to install `go` and build `task`,
# #       and then copy over the `task` executable to this container.
# # Install go, to install `task`
# RUN cd /tmp \
#     wget https://go.dev/dl/go1.21.6.linux-armv6l.tar.gz &&  \
#     tar -C /usr/local -xzf go1.21.6.linux-armv6l.tar.gz
# ENV PATH="${PATH}:/usr/local/go/bin"
# ENV GOPATH=/root/go
# RUN env GOBIN=/bin go install github.com/go-task/task/v3/cmd/task@latest

# TODO: Move this up to be with the rest of the pip3
