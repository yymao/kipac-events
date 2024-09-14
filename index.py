#!/usr/bin/env python
print 'Content-Type: text/html'
print

# For debugging
#import cgitb
#cgitb.enable()

from events_utils import collect_events, format_week, header_web, footer_web

entries, dates_this_week, dates_next_week = collect_events()

print header_web
if dates_this_week:
    print format_week(dates_this_week, entries, 'This week').encode('utf-8')
    print '<hr>'
print format_week(dates_next_week, entries, 'The coming week').encode('utf-8')
print footer_web
