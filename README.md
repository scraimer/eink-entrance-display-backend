## Installation and Run

Create a file named `.secrets` that looks something like this

    # Do not commit this file! It has private data!
    SECRETS_OPENWEATHERMAP_API_KEY=12345_your_api_key_67890
    SECRETS_GOOGLE_CALENDAR_API_KEY=213131231_your_api_key
    SECRETS_GOOGLE_CALENDAR_CALENDAR_ID=123456789@group.calendar.google.com

After the `.secrets` has been placed in the same directory as `main.py`,
you can launch the daemon.

    go install github.com/go-task/task/v3/cmd/task@latest
    ~/go/bin/task docker_build
    ~/go/bin/task daemon_run

### Google Credentials

Read the instruction in `chores.py` to see how to get the Application to have access.

### Chores DB

#### Periodically: Export a backup of the Chores Database

```shell
# change directory to the folder containing this README.md file
sqlite3 chores.sqlite .dump > deploy/chores_dump.sql
```

##### To Restore it

```shell
sqlite3 chores_new.sqlite < deploy/chores_dump.sql
```

#### Initial: Sync the chore data from Google Sheets

Run this inside the container:

```shell
cd /app
python -c "
from src.eink_backend.chores_db import ChoresDatabase
from src.eink_backend.sync_chores_from_sheets import sync_chores_from_sheets
db = ChoresDatabase('sqlite:///chores.sqlite')
db.init_db()
sync_chores_from_sheets(db)
"
```

## Developement Mode

### In the devcontainer

VSCode supports the devcontainer, which has been configured for running on ARMv7l
(which is what I have this installed on at home, a Raspberry Pi 4. Migrating to
`aarch64` would be nice, but would take a lot of work.)

To run the server:

    cd $SOURCE_ROOT
    task dev_debug_run

And then open this link in your browser: http://localhost:8323
(This works since that port is fowarded by VSCode)

## Deprecated: Connecting to container in remote server

On VSCode computer:

```shell
docker context create entrance-display --docker "host=ssh://pi@10.5.1.20"
docker context use remote-context-label
```

In VSCode, install [Docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker) and "Remote Development" (ms-vscode-remote.vscode-remote-extensionpack)

You should already see the containers.