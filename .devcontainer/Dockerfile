# This is all copied from `deploy/docker-containers/base/Dockerfile`
FROM eink-entrance-display-backend-base:latest

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    sqlite3 \
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

# Install Node.js 20 for openspec CLI
RUN mkdir -p /tmp/node && \
    cd /tmp/node && \
        ARCH="$(dpkg --print-architecture)" && \
        case "$ARCH" in \
            amd64) NODE_ARCH="x64" ;; \
            arm64) NODE_ARCH="arm64" ;; \
            armhf) NODE_ARCH="armv7l" ;; \
            *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
        esac && \
        VERSION="v20.19.0" && \
        wget "https://nodejs.org/dist/${VERSION}/node-${VERSION}-linux-${NODE_ARCH}.tar.xz" && \
        tar -C /usr/local -xJf "node-${VERSION}-linux-${NODE_ARCH}.tar.xz" && \
        ln -fs /usr/local/node-${VERSION}-linux-${NODE_ARCH}/bin/node /usr/local/bin/node && \
        ln -fs /usr/local/node-${VERSION}-linux-${NODE_ARCH}/bin/npm /usr/local/bin/npm && \
        ln -fs /usr/local/node-${VERSION}-linux-${NODE_ARCH}/bin /usr/local/node-bin-dir
ENV PATH="${PATH}:/usr/local/bin"

# Install openspec CLI
RUN npm install -g @fission-ai/openspec@latest && \
    ln -s /usr/local/node-bin-dir/openspec /usr/local/bin/openspec

