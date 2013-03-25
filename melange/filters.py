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

from dateutil import tz

from melange import app

@app.template_filter('localtimeformat')
def localtimeformat(time):
    if not time:
        return ""
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    return time.replace(tzinfo=from_zone).astimezone(to_zone).strftime("%Y/%m/%d %H:%M:%S")

@app.template_filter('localtimeformatdate')
def localtimeformatdate(time):
    if not time:
        return ""
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    return time.replace(tzinfo=from_zone).astimezone(to_zone).strftime("%Y-%m-%d")
