
import os

from optparse import OptionParser

parser = OptionParser()
parser.add_option('-i', '--initdb', default=None, action='store_true', dest='initdb')
parser.add_option('-d', '--dropdb', default=None, action='store_true', dest='dropdb')
options, args = parser.parse_args()

if options.initdb:
    from melange.database import init_db
    print('Initializing database')
    init_db()
    from melange import User
    admin = User('admin')
    admin.password = 'admin'
    admin.save()
elif options.dropdb:
    from melange.database import drop_db
    print('Dropping database')
    drop_db()
else:
    from melange import app
    app.run()
