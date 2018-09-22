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

class Config(object):
    DEBUG = False
    TESTING = False

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_URL = 'sqlite:///melange.db'
    SECRET_KEY = '\xe9\xcdEw\xfd/|\xb0|~\x05\xb3\xa8\x18\x16[\xce\x96N)\x91d\x1d\xe6'

class TestingConfig(Config):
    TESTING = True
    DATABASE_URL = 'sqlite://'
    SECRET_KEY = '\xe9\xcdEw\xfd/|\xb0|~\x05\xb3\xa8\x18\x16[\xce\x96N)\x91d\x1d\xe6'
