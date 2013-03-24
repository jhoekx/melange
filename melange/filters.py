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
