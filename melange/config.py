
class Config(object):
    DEBUG = False
    TESTING = False

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_URL = 'sqlite:///melange.db'
    SECRET_KEY = '\xe9\xcdEw\xfd/|\xb0|~\x05\xb3\xa8\x18\x16[\xce\x96N)\x91d\x1d\xe6'
    PLUGINS = [ 
        {
            'module': 'melange.reports',
            'blueprint': 'reports',
            'blueprint_url': '/reports',
        }
    ]

class TestingConfig(Config):
    TESTING = True
    DATABASE_URL = 'sqlite://'
    SECRET_KEY = '\xe9\xcdEw\xfd/|\xb0|~\x05\xb3\xa8\x18\x16[\xce\x96N)\x91d\x1d\xe6'
