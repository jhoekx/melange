# (c) 2013, Jeroen Hoekx <jeroen.hoekx@dsquare.be>
#
# This file is part of Melange.
#
# Melange is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Melange is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Melange.  If not, see <http://www.gnu.org/licenses/>.

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from melange import app

engine = create_engine(app.config['DATABASE_URL'])
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import melange.models
    Base.metadata.create_all(bind=engine)

def drop_db():
    import melange.models
    Base.metadata.drop_all(bind=engine)

def check_db():
    from melange.models import User, Tag
    try:
        users = User.query.all()
        tags = Tag.query.all()
        if len(users) + len(tags) > 1:
            return True
    except:
        pass
    return False
