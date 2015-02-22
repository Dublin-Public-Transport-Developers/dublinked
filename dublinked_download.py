#! /usr/bin/python
from __future__ import print_function
from mechanize import Browser
import logging
from collections import defaultdict
from datetime import timedelta
from time import time
import json

logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

log = logging.getLogger("dublinked.realtime")

def clean_route_desc(route_desc):
    return ' '.join(word for word in route_desc.split(' ') if word not in ['line'])

def clean_stop(stop_desc):
    return ' '.join(word for word in stop_desc.split(' ') if word not in ['LUAS'])

def to_timedelta(datetime_str):
    return timedelta(*(map(int, datetime_str.split(' ', 1)[1].split(':'))))

"""
Sample output for Dublin Bus (bac), stop 1713 (stoneybatter)
You need to provide your own username and password supplied by dublinked.com
>>> get_times('your_username', 'your_password', 'bac', '1713')
defaultdict(<type 'list'>, {u'39a': [(datetime.timedelta(15, 26), datetime.timedelta(15, 26, 11), False), (datetime.timedelta(15, 44), datetime.timedelta(15, 45, 22), False), (datetime.timedelta(16, 4), datetime.timedelta(16, 3, 55), False)], u'37': [(datetime.timedelta(15, 25), datetime.timedelta(15, 25, 20), False)], u'39': [(datetime.timedelta(15, 43), datetime.timedelta(15, 41, 38), False), (datetime.timedelta(16, 10), datetime.timedelta(16, 10, 28), False)]})
"""

def get_times(dublinked_username, dublinked_password, operator_id, realtime_id, realtime_results=None):
    predicted_times = defaultdict(list)
    br = Browser()
    br.set_handle_robots(False)
    br.addheaders = [
        ("User-agent", 'Python script, run by %s' % (dublinked_username)),
        ("Referer", 'https://github.com/Dublin-Public-Transport-Developers')]
    url = 'http://www.dublinked.ie/cgi-bin/rtpi/realtimebusinformation?stopid=%s&format=json' % (realtime_id)

    br.add_password(url, dublinked_username, dublinked_password)
    stime = time()
    br.open(url)
    request_time_ms = int(1000 * (time() - stime))
    log.debug("### Downloaded dublinked %s, stop id %s in %dms" % (operator_id, realtime_id, request_time_ms))
    json_contents = json.loads(br.response().read())
    predicted_times = defaultdict(list)
    if json_contents['errorcode'] != '0':
        if json_contents['errorcode'] != '1':
            error_warning = "dublinked error %s [%s]: (%s)" % (json_contents['errorcode'], realtime_id, json_contents.get('errormessage', ''))
            log.warning(error_warning)
    else:
        for result_row in json_contents['results']:
            warn = ''
            route_desc = clean_route_desc(result_row['route']).lower()
            real_t = to_timedelta(result_row['departuredatetime'])
            sched_t = to_timedelta(result_row['scheduleddeparturedatetime'])
            predicted_times[route_desc].append((sched_t, real_t, bool(warn)))
    if realtime_results:
        realtime_results.put(predicted_times)
    log.debug("### Put results %s %s" % (realtime_id, time() - stime))
    return predicted_times

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print('Usage: %s <your dublinked username> <your dublinked password>' % sys.argv[0])
        print('http://dublinked.com/ requires an account username/password.')
    elif len(sys.argv) != 5:
        print('Usage: %s username password <dublinked operator id> <dublinked stop id>' % sys.argv[0])
        print('(downloading sample stop)')
        print(get_times(sys.argv[1], sys.argv[2], 'bac', '1713'))
    else:
        print(get_times(*sys.argv[1:4]))
