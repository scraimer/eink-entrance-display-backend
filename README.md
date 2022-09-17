## Installation and Run

    go install github.com/go-task/task/v3/cmd/task@latest
    ~/go/bin/task build_docker
    ~/go/bin/task run_docker_daemon

## Developement Mode

### Outside a container

This will automatically update when you modify the file.

    go install github.com/go-task/task/v3/cmd/task@latest
    # Stop the installed docker, if one is running
    docker stop `docker container list --filter "expose=8321" -q`    
    ~/go/bin/task debug_run

### In a container

If you're developing this, you can run the container in debug mode so that
you can see the output from the runnings daemon.

It won't auto-update when you modify files, though.
You'll have to press CTRL-C and restart the container to load changes.

    go install github.com/go-task/task/v3/cmd/task@latest
    # Stop the installed docker, if one is running
    docker stop `docker container list --filter "expose=8321" -q`
    ~/go/bin/task debug_build_docker
    ~/go/bin/task debug_run_docker

For the plan, see `development.md`
