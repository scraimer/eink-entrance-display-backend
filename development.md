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

   * Idea #2: Split the image into sub-images. Have each sub-image copied to different x,y origins to make a single large image. (Might have to also support relative position, depending on size of other sub-images)

* Move to async data collection, rendering and display:

    * Have one "thread" (or process) that collects the data into a DB

    * Have the server render the data into a display image (red and black, for eink)

    * On eInk RPi continue with the same client