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
