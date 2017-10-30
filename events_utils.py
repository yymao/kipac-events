from __future__ import unicode_literals
__all__ = ['collect_events', 'format_week', 'prepare_email', 'header_web', 'footer_web']

import re
from datetime import datetime, timedelta
from urllib import urlopen
import xml.etree.cElementTree as ET

_base_url = 'https://live-kipac.pantheonsite.io'
_feed_url = _base_url + '/events/feed.xml'

_tea_menu_url = 'https://docs.google.com/document/d/11u2iHGiyqSbNUSM37rFDIPmQ1X79hhagoNMjxRId6Ds/edit'

xml_parser = ET.XMLParser(encoding='utf-8')

def parse_event(item):
    out = {}
    for element in item:
        tag = element.tag

        if not element.text:
            continue
        text = element.text.strip()
        if not isinstance(text, unicode):
            text = unicode(element.text, 'utf-8')
        if not text or text == '---':
            continue

        if tag == 'field_date_temp':
            out['dtstart'] = datetime.strptime(text, '%Y-%m-%dT%H:%M:%S')
        elif tag == 'field_event_series':
            out['series'] = text
        elif tag == 'field_event_speaker':
            out['speaker'] = text
        elif tag == 'title':
            out['description'] = text
        elif tag == 'field_stanford_event_location':
            out['location'] = text.rpartition('<p>')[-1].partition('</p>')[0]
        elif tag == 'path':
            out['url'] = _base_url + text

        if 'series' in out or 'speaker' in out:
            sep = ': ' if ('series' in out and 'speaker' in out) else ''
            menu = ''
            if out.get('series') == 'KIPAC Tea Talk':
                menu = ' [<a href="{0}">menu</a>]'.format(_tea_menu_url)
            if 'series' in out and 'url' in out:
                out['series'] = '<a href="{1}">{0}</a>'.format(out['series'], out['url'])
            out['summary'] = out.get('series', '') + menu + sep + out.get('speaker', '')
        elif 'description' in out:
            out['summary'] = out['description']
            del out['description']

    return out


def iter_events(feed_url):
    for item in reversed(ET.parse(urlopen(feed_url)).getroot()):
        event = parse_event(item)
        if event.get('dtstart') and event.get('summary'):
            yield event


def format_entry(entry):
    s = '<li>'
    s += '<b>{0}</b> <br>'.format(entry['summary'])
    if entry['dtstart'].hour or entry['dtstart'].minute:
        s += '{0}'.format(entry['dtstart'].strftime('%-I:%M %P'))
    if entry.get('location'):
        s += ' -- {0} <br>'.format(entry['location'])
    if entry.get('description') and entry['description'] != 'TBD':
        s += '<i>{0}</i> <br>'.format(entry['description'])
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

    for entry in iter_events(_feed_url):
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
This {{0}} is automatically generated with the information on the <a href="{0}/events">KIPAC website</a>.{{1}}<br>
If you find the event information not accurate or missing, please contact <a href="mailto:martha@slac.stanford.edu">Martha Siegel</a>.<br>
If you find the content not properly displayed, please contact <a href="mailto:yymao.astro@gmail.com">Yao-Yuan Mao</a>.</p>'''.format(_base_url)


def prepare_email(entries, dates_next_week):
    today, today_weekday, coming_monday, monday_after = calc_dates()

    if coming_monday.month == 12 and coming_monday.day >= 22 or coming_monday.day <= 28:
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
  <link rel="stylesheet" href="https://unpkg.com/purecss@1.0.0/build/pure-min.css">
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
