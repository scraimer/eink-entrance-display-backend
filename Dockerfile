FROM python:3.7-slim-buster

RUN apt-get update
RUN apt-get install -y wget

# TODO: The ENV and the steps below can be re-ordered for better clarity
RUN apt-get -y install build-essential

RUN apt-get -y install zlib1g-dev

RUN pip3 uninstall PIL
RUN pip3 install --upgrade pip
RUN pip3 install fastapi
RUN pip3 install "uvicorn[standard]"
RUN pip3 install pytest
RUN pip3 install bs4
RUN pip3 install requests
RUN apt-get install -y libjpeg-dev libopenjp2-7 libtiff5 libfreetype6-dev
RUN pip3 install pillow

COPY . /app

ENTRYPOINT bash -c "cd /app ; /usr/local/bin/uvicorn main:app --host 0.0.0.0 --port 8321"
EXPOSE 8321
