FROM python:3.7-slim-buster

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
