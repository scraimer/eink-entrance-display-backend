# Secrets

To avoid writing the project's secret to Git, they are all stored in `.secrets` in the
root directory of the project, and added to `.gitignore`.

The format of the file is the same as an .env file. See `README.md` on an example.

## Why?

Pros:

* The `.env` is a known format, and compatible with both `bash` and `docker`.
* The loading of file using python's `dotenv` sets a global value for the process,
  so there's no need to pass that object around. (This can also be a "con", too.)

Cons:

* No typing information. Even JSON has a boolean/integer/string distinction.
