#!/usr/bin/env python

from events_utils import collect_events, format_week, header_web, footer_web

entries, dates_this_week, dates_next_week = collect_events()

print 'Content-Type: text/html'
print
print header_web
if dates_this_week:
    print format_week(dates_this_week, entries, 'This week')
    print '<hr>'
print format_week(dates_next_week, entries, 'The coming week')
print footer_web

