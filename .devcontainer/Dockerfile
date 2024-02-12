# This is all copied from `deploy/docker-containers/base/Dockerfile`
FROM eink-entrance-display-backend-base:latest

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git

# Install go, to install the `task` command
RUN mkdir -p /tmp/for-docker && \
    cd /tmp/for-docker && \
    wget https://go.dev/dl/go1.21.6.linux-armv6l.tar.gz &&  \
    tar -C /usr/local -xzf go1.21.6.linux-armv6l.tar.gz
ENV PATH="${PATH}:/usr/local/go/bin"
ENV GOPATH=/root/go
RUN env GOBIN=/bin go install github.com/go-task/task/v3/cmd/task@latest
