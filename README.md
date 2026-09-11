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

### To Run in the Background

To restart the container every 2 days at 5:00 AM, add this to your crontab:

```crontab
0 5 * * */2 docker container restart eink_backend_prod
```

To watch the logs:

```shell
docker logs -f eink_backend_prod
```

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

### Chore Management Icon and PWA Assets

The `/chores` page uses the following browser and installable-app assets:

- `assets/icons/icon-192.png`: 192x192 app icon and Apple touch icon
- `assets/icons/icon-512.png`: 512x512 installable PWA icon
- `assets/favicon.ico`: ICO fallback for browser tabs and older clients
- `assets/manifest.webmanifest`: PWA name, display settings, and icon references
- `assets/chores_ui.html`: links to the manifest, favicon, theme color, and Apple touch icon

To update the broom artwork:

1. Replace both PNG files with square 192x192 and 512x512 versions of the new artwork. Keep the artwork consistent between the two sizes.
2. Regenerate the ICO fallback from the 512px PNG with Pillow:

    ```shell
    python -c "from PIL import Image; image = Image.open('assets/icons/icon-512.png'); image.save('assets/favicon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])"
    ```

3. If the asset paths change, update them in both `assets/manifest.webmanifest` and the metadata in `assets/chores_ui.html`. Keep the manifest `start_url` set to `/chores` and `display` set to `standalone` for PWA installation.
4. Run the focused validation tests:

    ```shell
    pytest -q test_chore_favicon.py
    ```

    These tests verify the PNG dimensions, ICO format, manifest JSON, HTML metadata, response media types, and served bytes.

Browsers cache favicons and manifests. After deploying an update, use a hard refresh or remove and reinstall the `/chores` app to see changed artwork. PWA installation also requires a secure browser context, such as HTTPS or localhost.

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