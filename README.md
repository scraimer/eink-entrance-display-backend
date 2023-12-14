## Installation and Run

Create a file named `.secrets` that looks something like this

    # Do not commit this file! It has private data!
    SECRETS_OPENWEATHERMAP_API_KEY=12345_your_api_key_67890
    SECRETS_GOOGLE_CALENDAR_API_KEY=213131231_your_api_key
    SECRETS_GOOGLE_CALENDAR_CALENDAR_ID=123456789@group.calendar.google.com

After the `.secrets` has been placed in the same directory as `main.py`,
you can launch the daemon.

    go install github.com/go-task/task/v3/cmd/task@latest
    ~/go/bin/task build_docker
    ~/go/bin/task run_docker_daemon
    
### Google Credentials

Read the instruction in `chores.py` to see how to get the Application to have access.

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

### In the devcontainer

VSCode supports the devcontainer, which has been configured for running on ARMv7l
(which is what I have this installed on at home, a Raspberry Pi 4. Migrating to
`aarch64` would be nice, but would take a lot of work.)

To run the server:

    cd $SOURCE_ROOT
    uvicorn src.eink_backend.main:app --host 0.0.0.0 --port 8323 --reload

And then open this link in your browser: http://localhost:8323
(This works since that port is fowarded by VSCode)