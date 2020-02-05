#!/usr/bin/env python
import os
import sys
from events_utils import collect_events, prepare_email

sys.path.insert(0, '/afs/ir.stanford.edu/users/y/y/yymao/cgi-bin/kipac-teabot')

if 'REQUEST_METHOD' in os.environ:
    print 'Content-Type: text/html'
    print
    import time
    import cgi
    import cgitb
    cgitb.enable()
    form = cgi.FieldStorage()
    if form.getfirst("send") == time.strftime("%Y%m%d"):
        from email_server import email_server
    else:
        from email_server import email_server_dummy as email_server
else:
    from email_server import email_server

del sys.path[0]

entries, _, dates_next_week = collect_events()
to, subject, msg = prepare_email(entries, dates_next_week)

if msg:
    email = email_server()
    email.send('KIPAC TeaBot <teabot@kipac.stanford.edu>', to, subject, msg)
    email.close()

