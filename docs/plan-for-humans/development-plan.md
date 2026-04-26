## Plan

* Only show shabbat times when relevant
  * If it's before a shabbat / chag, then show the entry time on the day of and the day before.
  * On fast days, show the fast start time and end time.
  * During shabbat/chag, show the exit time.

* Verify that PNG is the right size; force it to the right size by cutting it
  down to size.

## Bugs

* The weather always show the current-time weather, even when "at=" is specified.
* The next person to do chores should only cycle between the four oldest, skipping Aviv for now.
* It's not clear which number is for which ranking. Either add vertical lines to divide the columns,
  or add borders around the pair of "name" and "value" to visually show they are related, and separate
  from the other pairs.
* Add a warning to the developer if there's a file longer than 400 lines
  * Split files that are longer than 400 lines so that the Agent doesn't have to read so much.

## Wishlist / Ideas

* `sync_chores_from_sheets.py` can be deprecated. Its usefulness is at an end. Remove the file from the project and any mentions in the README.md

* Move more stuff to the DB and UI, such as the seating chart.

### Weather

* Check weather - am I showing the correct times? Has the switch to UTC shifted the weather I'm showing? Am I showing for 13:00 the weather for 13:00 or for 10:00? Check by reading from their API and seeing when the first hourly is, that should be for the current hour. I hope.

* Show the temperature for the rest of the day not just in certain hours. Some way to show all the expected temperatures, not just certain hours. Maybe a graph.

* Show Air quality

* Show speed of wind and direction. Maybe only when it's important (like too windy. Don't mention it when it's slow. Unless I'd like to know if there's no wind on a hot day, to make sure I turn on the A/C when we have guests.)

What do I want?

* Show interesting peaks.
  * If it rains at only one point of the day.
    * If it's raining all day, or all the times I'm outside, then just mark it as rain.
* Actually, I also want minumums below a threshold. Like, if the temperature was high and only goes below 28C at 16:00, that's interesting. If it's over 40% rain and that drops to under 10% , that's interesting.
* Maybe I should classify items of interest as "bad weather". And find when we enter such a zone, and when we exit such a zone.
  * Rain
    * under 10% is not interesting
    * over 40% is bad weather
  * Heat
    * Under 15C is interesting if the day is warm (say, over 25C)
    * Under 2C is bad weather.
    * But 8C is not bad weather in a day that's average of 15C. It's just a bit colder.
    * Over 30C is bad weather. Unless the last few days were over 34C. Then it's an improvement.
  * UV
  * Wind

* Use different times for Sun-Thr, Fri, and Saturary.
  Sun-Thr: Show leaving and returning from school, pickup, and maybe evening.
    Must: 07:00-08:00, 14:00, 16:00
    Maybe: 18:00-22:00 in overview
  Fri: School, pickup, Park prayer (note especially the rain, temp, and wind)
    07:00-08:00, 11:00-13:00, 18:00-19:00
  Sat: 08:00-09:00, 11:00, 13:00 (mincha), 16:00-tzet shabbat, every hour, or tell me when it stops raining or stops being hot.

What do I not care about?

* Hours after 22:00 before 07:00 the next day. Don't show for that.

### Zmanim

* Show Rosh Hodesh
* Show fast-days start/end times.

* Don't show when shabbat is coming in, except for on Friday.

* Create some modular layout mechnism.

   * Idea #1: Create HTML files and use the firefox screenshot mechanism to store red and black versions (perhaps set red/black using CSS classes?)

         docker build --tag eink-entrance-display-backend:test-with-firefox --rm=false deploy/docker-containers/base/

         docker run --rm --mount type=bind,source=$PWD,target=/src eink-entrance-display-backend:test-with-firefox bash -c "firefox --screenshot /src/out.png \"--window-size=528\" file:///src/assets/layout-shabbat.html ; chmod 666 /src/out.png"

   TODO: Build a template to fill with data: shul, weather, smarthome updates (why is AC on, when will it next turn on during shabbat/chag, other changes, report open windows according to temperature sensors, display house diagram, etc)

   * Idea #2: Split the image into sub-images. Have each sub-image copied to different x,y origins to make a single large image. (Might have to also support relative position, depending on size of other sub-images)

## Done

* Remove shul times (mincha and shaharit)

* ~~Create a git repo for this named something like `eink-entrance-display-backend`~~

* ~~Move all the Shul Zmanim stuff from `eink-entrace-display` to `eink-entrace-display-backend`~~

* ~~Create build script in taskfile to build docker~~

* ~~Add script in taskfile to launch in docker~~

* ~~On the eInk RPi, have a client that downloads the image and displays it periodically~~

* ~~Move to async data collection, rendering and display:~~

    * ~~Have one "thread" (or process) that collects the data into a DB~~

    * ~~Have the server render the data into a display image (red and black, for eink)~~

    * ~~On eInk RPi continue with the same client~~

* ~~The zmanim data for Efrat is: https://www.efrat.muni.il/he/%D7%96%D7%9E%D7%A0%D7%99-%D7%9B%D7%A0%D7%99%D7%A1%D7%AA-%D7%94%D7%A9%D7%91%D7%AA/~~

* ~~better png icons: translate orange to red, and gray to 50% black~~

* ~~Show events from a Google calendar~~

* ~~Smaller date, remove padding~~
