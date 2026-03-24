# This is all copied from `deploy/docker-containers/base/Dockerfile`
FROM eink-entrance-display-backend-base:latest

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git

# Install go, to install the `task` command
RUN mkdir -p /tmp/for-docker && \
    cd /tmp/for-docker && \
        ARCH="$(dpkg --print-architecture)" && \
        case "$ARCH" in \
            amd64) GO_ARCH="amd64" ;; \
            arm64) GO_ARCH="arm64" ;; \
            armhf) GO_ARCH="armv6l" ;; \
            *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
        esac && \
        wget "https://go.dev/dl/go1.21.6.linux-${GO_ARCH}.tar.gz" && \
        tar -C /usr/local -xzf "go1.21.6.linux-${GO_ARCH}.tar.gz"
ENV PATH="${PATH}:/usr/local/go/bin"
ENV GOPATH=/root/go
RUN env GOBIN=/bin go install github.com/go-task/task/v3/cmd/task@latest
