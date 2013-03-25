= Melange

A simple Configuration Management Database with plugin framework to show your
favourite tools in one central place.

== Getting Started

Melange runs in development mode using SQLite by default.

Start the development version:

```bash
$ git clone ...
$ virtualenv2 .
$ source bin/activate
$ pip install < requirements.txt
$ nosetests tests/
$ python runserver.py --initdb
$ python runserver.py &
```

Melange is now listening on http://localhost:5000/ .
Username: 'admin', password 'admin'.

== Configuration
Other databases are supported. A production config looks like this:

```python
SECRET_KEY = '\xe9\xcdEw\xfd/|\xb0|~\x05\xb3\xa8\x18\x16[\xce\x96N)\x91d\x1d\xe6'
DATABASE_URL = 'postgresql://melange:<pass>@localhost/melange'
PLUGINS = [ 
    {
        'module': 'melange.reports',
        'blueprint': 'reports',
        'blueprint_url': '/reports',
    }
]
```

Create an environment variable `MELANGE_CONFIG_FILE` with the location of that 
file before starting.
