FROM python:3.7-slim-buster

RUN apt-get update
RUN apt-get install -y wget

#RUN cd /tmp && \
#    wget https://go.dev/dl/go1.17.5.linux-armv6l.tar.gz && \
#    tar xf go1.17.5.linux-armv6l.tar.gz && \
#    mv /tmp/go /usr/local && \
#    /usr/local/go/bin/go version && \
#    rm /tmp/go1.17.5.linux-armv6l.tar.gz  && \
#    echo export PATH=\$PATH:/usr/local/go/bin >> ~/.bashrc && \
#    echo export GOPATH=\$HOME/go >> ~/.bashrc
#
#ENV PATH=${PATH}:/usr/local/go/bin

# TODO: The ENV and the steps below can be re-ordered for better clarity
RUN apt-get -y install build-essential

# RUN go install github.com/go-task/task/v3/cmd/task@latest

#RUN cd /app && ~/go/bin/task setup

RUN apt-get -y install zlib1g-dev

RUN pip3 uninstall PIL
RUN pip3 install --upgrade pip
RUN pip3 install fastapi
RUN pip3 install "uvicorn[standard]"
RUN apt-get install -y libjpeg-dev libopenjp2-7 libtiff5
RUN pip3 install pillow
RUN pip3 install pytest
RUN pip3 install bs4
RUN pip3 install requests

COPY . /app

ENTRYPOINT bash -c "cd /app ; /usr/local/bin/uvicorn main:app --host 0.0.0.0 --port 8321"
EXPOSE  8321
