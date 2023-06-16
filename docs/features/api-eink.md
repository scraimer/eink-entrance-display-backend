You can do time travel in the the `joined` URL with an `at` query parameter.
Set the `at` to a date string of the format `YYYYMMDD-hhmmss`, and it will think that
"now" is that time, and create a result as if it's now.

Example, pretend we're in 2023-06-17 18:30:00:

    http://hinge-iot:8322/eink/joined?at=20230617-183000
