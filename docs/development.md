## Design

1. On one hand, have in `hinge-iot` an API that does all the heavy lifting
   and generates red and black images.

2. On the eink RPi, download the red and black images and display them.

I'd like to have each of them nicely packaged - in a docker image made from a
Dockerfile, and in a downloadable package that's easy to install.

## Plan

See `development-plan.md`

## Notes

* To get the rendered html from the container do this:

   docker cp $(docker ps -q --filter "ancestor=eink-entrance-display-backend"):/tmp/content.html .

### Running a single pythong file's `__main__` a module

   cd src
   python3 -m eink_backend.chores
