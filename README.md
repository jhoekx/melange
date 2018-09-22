Melange
=======

[![Build Status](https://travis-ci.org/jhoekx/melange.svg?branch=master)](https://travis-ci.org/jhoekx/melange)

A simple Configuration Management Database.

Getting Started
---------------

Melange runs in development mode using SQLite by default.

Start the development version:

```bash
$ git clone https://github.com/jhoekx/melange.git
$ cd melange/
$ python -m venv env
$ source env/bin/activate
(env) $ pip install -r requirements.txt
(env) $ nosetests tests/
(env) $ python runserver.py --initdb
(env) $ python runserver.py &
```

Melange is now listening on http://localhost:5000/ .
Username: 'admin', password 'admin'.

Optionally import example data:

```bash
(env) $ pip install requests
(env) $ python scripts/json_import.py --dest=http://localhost:5000/api/ --user=admin --password=admin < examples/example-data.json
```

Melange contains information about systems. Systems are grouped in tags. Both
systems and tags can define variables. System variables override tag variables.
Tag variables of tags with longer names win in case of duplication.

There is no tag hierarchy. That is by design. There is, however, a system (or
item) hierarchy. Child items don't inherit variables from parent items.

Browsing to the Melange server will initially show a blank screen with a menu
bar. Add a new tag by clicking on 'Tags' in the menu bar. You can create systems
directly from the tag by adding them as a child.

Deploying
---------

Melange can be deployed in a docker container.
The default configuration uses SQLite.
The docker container expects a volume mount at `/var/lib/melange` to store the database.

```bash
$ docker build -t melange .
$ docker run --rm -p 8000:8000 -v $(pwd)/db:/var/lib/melange -it melange
```

When using other databases than SQLite, the container will not initialize the database.

Configuration
-------------

Other databases are supported. A production config looks like this:

```python
SECRET_KEY = '\xe9\xcdEw\xfd/|\xb0|~\x05\xb3\xa8\x18\x16[\xce\x96N)\x91d\x1d\xe6'
DATABASE_URL = 'postgresql://melange:<pass>@localhost/melange'
```

Create an environment variable `MELANGE_CONFIG_FILE` with the location of that
file before starting.
