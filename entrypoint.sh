#!/bin/sh

set -e

python <<INITDB

import os
import sys
from urllib.parse import urlparse

db_url = os.environ.get('DATABASE_URL')
if db_url is not None:
    url = urlparse(db_url)
    if url.scheme == 'sqlite':
        if os.path.exists(url.path):
            print(f'Database {url.path} already exists')
            sys.exit(0)
        print(f'Will initialize database at {url.path}')
    else:
        ### assume external management when not SQLite
        sys.exit(0)

from melange.database import init_db
print('Initializing database')
init_db()
from melange import User
admin = User('admin')
admin.password = 'admin'
admin.save()
INITDB

export SECRET_KEY=$(python -c 'import os; print(os.urandom(16))')

exec "$@"
