__all__ = ['collect_events', 'format_week', 'prepare_email', 'header_web', 'footer_web']

import re
import cgi
from datetime import datetime, timedelta
from urllib import urlopen

_ics_url = 'https://kipac-web.stanford.edu/events/{0.year}-{0.month:02d}/ical.ics'

_tea_menu_url = 'https://docs.google.com/document/d/11u2iHGiyqSbNUSM37rFDIPmQ1X79hhagoNMjxRId6Ds/edit'


def unescape_ical(s):
    return cgi.escape(re.sub(r'\\([\,;:])', r'\1', s).replace(r'\n','\n').replace('\xc2\xa0', ' '))


def extract_time(s):
    return datetime.strptime(s, ('%Y%m%dT%H%M%S' if 'T' in s else '%Y%m%d'))


def extract_description(s):
    return s.partition('\n\nBody: \n\n')[2].partition('\n\nLocation: \n\n')[0].partition('\n\n\n\n')[0].strip()


def iter_ics(ics_url):
    lines = [l[:-2] for l in urlopen(ics_url)]
    lines.append('')
    d = None
    line = lines.pop(0)
    for l in lines:
        if l.startswith(' '):
            line += l[1:]
            continue
        if d is None:
            if line == 'BEGIN:VEVENT':
                d = {}
        else:
            if line == 'END:VEVENT':
                if 'summary' in d and 'dtstart' in d:
                    d['dtstart'] = extract_time(d['dtstart'])
                    yield d
                d = None
            else:
                k, __, v = line.partition(':')
                k = k.partition(';')[0]
                if k in ('DTSTART', 'SUMMARY', 'DESCRIPTION', 'LOCATION'):
                    d[k.lower()] = v
        line = l


def format_entry(entry):
    s = '<li>'
    summary = re.sub(r'(kipac\s+tea(?:\s+talks?)?)', \
            r'<a href="{0}">\1</a>'.format(_tea_menu_url),\
            unescape_ical(entry['summary']), flags=re.I)
    s += '<b>{0}</b><br>'.format(summary)
    if entry['dtstart'].hour or entry['dtstart'].minute:
        s += '{0} -- '.format(entry['dtstart'].strftime('%-I:%M %P'))
    s += '{0}<br>'.format(unescape_ical(entry['location']) if 'location' in entry else 'Location TBA')
    desc = extract_description(unescape_ical(entry['description'])) if 'description' in entry else ''
    if desc:
        s += '<i>{0}</i><br>'.format(desc.replace('\n', '<br>'))
    s += '<br></li>'
    return entry['dtstart'].strftime('%A, %-m/%-d'), s


def format_week(dates, entries, header=None):
    s = '' if header is None else '<h2>{0}</h2>'.format(header)
    if dates:
        for date in dates:
            entry = entries[date]
            if entry:
                s += '<h3>{0}</h3><ul>{1}</ul>'.format(date, ''.join(entry))
    else:
        s += '<h3>No event scheduled</h3>'
    return s


def calc_dates():
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    today_weekday = today.weekday()
    coming_monday = today + timedelta(days=7-today_weekday)
    monday_after = coming_monday + timedelta(days=7)
    return today, today_weekday, coming_monday, monday_after


def collect_events():
    today, today_weekday, coming_monday, monday_after = calc_dates()

    entries = {}
    dates_this_week = []
    dates_next_week = []
    
    for entry in iter_ics(_ics_url.format(today)):
        if entry['dtstart'] < today:
            continue
        if entry['dtstart'] >= monday_after:
            break
        date, s = format_entry(entry)
        if date not in entries:
            entries[date] = []
            if entry['dtstart'] < coming_monday:
                dates_this_week.append(date)
            else:
                dates_next_week.append(date)
        entries[date].append(s)
    
    return entries, dates_this_week, dates_next_week


_footer = '''<b>See also the <a href="https://physics.stanford.edu/applied-physicsphysics-colloquium-schedule">physics colloquium schedule</a> and the <a href="https://sitp.stanford.edu/seminar-schedule">SITP seminar schedule</a>.</b>
<br><br><hr><p>
This {0} is automatically generated with the information on the <a href="https://kipac-web.stanford.edu/events">KIPAC website</a>.{1}<br>
If you find the event information not accurate or missing, please contact <a href="mailto:martha@slac.stanford.edu">Martha Siegel</a>.<br>
If you find the content not properly displayed, please contact <a href="mailto:yymao@stanford.edu">Yao-Yuan Mao</a>.</p>'''


_holidays = {datetime(2015, 12, 21), datetime(2015, 12, 28)}

def prepare_email(entries, dates_next_week):
    today, today_weekday, coming_monday, monday_after = calc_dates()

    if coming_monday in _holidays:
        return '', '', ''
    
    if today_weekday == 4: #Friday
        to = ['i-life@kipac.stanford.edu', 'Martha Siegel <martha@slac.stanford.edu>']
        preview = True
    elif today_weekday == 6: #Sunday
        to = 'everyone@kipac.stanford.edu'
        preview = False
    else:
        return '', '', ''

    week = '{0}-{1}'.format(coming_monday.strftime('%-m/%-d'), \
            (monday_after-timedelta(days=1)).strftime('%-m/%-d'))

    subject = 'KIPAC Weekly Schedule {0}{1}'.format(week, \
            ' (preview)' if preview else '')
    
    msg = ''

    if preview:
        msg += '''<p>This is a <em>preview</em> of the KIPAC weekly schedule for the coming week ({0}).<br>
If you know events that are not listed or need updates, please ask <a href="mailto:martha@slac.stanford.edu">Martha Siegel</a> to do so. 
Also, if a regular event will not take place, it's always good to say so <em>explictly</em> on the calender.</p><hr>
'''.format(week)
    
    msg += format_week(dates_next_week, entries)

    msg += _footer.format('message', ' <br>To view this email on a mobile-friendly webpage, <a href="https://web.stanford.edu/~yymao/cgi-bin/kipac-events">click here</a>.')

    return to, subject, msg


header_web = '''<!DOCTYPE html>
<html>
<head>
  <title>KIPAC Events</title>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <meta name="robots" content="noindex, nofollow">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="//cdn.jsdelivr.net/pure/0.6.0/pure-min.css">
  <style>
  .layout {
    margin-left: auto;
    margin-right: auto;
    max-width: 760px;
    padding: 0.5em 1em 5em 1em;
  }
  p {
    line-height: 1.5em;
    font-size:small;
  }
  </style>
</head>
<body>
  <div class="layout">
    <h1>KIPAC Events</h1>
    <hr>
'''


footer_web = _footer.format('page', '') + '''
  </div>
</body>
</html>
'''

