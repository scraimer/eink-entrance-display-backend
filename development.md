## Design

1. On one hand, have in `hinge-iot` an API that does all the heavy lifting
   and generates red and black images.

2. On the eink RPi, download the red and black images and display them.

I'd like to have each of them nicely packaged - in a docker image made from a
Dockerfile, and in a downloadable package that's easy to install.

## Plan

* ~~Create a git repo for this named something like `eink-entrance-display-backend`~~

* ~~Move all the Shul Zmanim stuff from `eink-entrace-display` to `eink-entrace-display-backend`~~

* ~~Create build script in taskfile to build docker~~

* ~~Add script in taskfile to launch in docker~~

* ~~On the eInk RPi, have a client that downloads the image and displays it periodically~~

* Create some modular layout mechnism.

   * Idea #1: Create HTML files and use the firefox screenshot mechanism to store red and black versions (perhaps set red/black using CSS classes?)

         docker build --tag eink-entrance-display-backend:test-with-firefox --rm=false docker-containers/base/

         docker run --rm --mount type=bind,source=$PWD,target=/src eink-entrance-display-backend:test-with-firefox bash -c "firefox --screenshot /src/out.png \"--window-size=528\" file:///src/layout-test-src.html ; chmod 666 /src/out.png"

   TODO: Build a template to fill with data: shul, weather, smarthome updates (why is AC on, when will it next turn on during shabbat/chag, other changes, report open windows according to temperature sensors, display house diagram, etc)

   * Idea #2: Split the image into sub-images. Have each sub-image copied to different x,y origins to make a single large image. (Might have to also support relative position, depending on size of other sub-images)

* Move to async data collection, rendering and display:

    * Have one "thread" (or process) that collects the data into a DB

    * Have the server render the data into a display image (red and black, for eink)

    * On eInk RPi continue with the same client

* The zmanim data for Efrat is: https://www.efrat.muni.il/he/%D7%96%D7%9E%D7%A0%D7%99-%D7%9B%D7%A0%D7%99%D7%A1%D7%AA-%D7%94%D7%A9%D7%91%D7%AA/

## Notes

* To get the rendered html from the container do this:

   docker cp $(docker ps -q --filter "ancestor=eink-entrance-display-backend"):/tmp/content.html .