#!/usr/bin/env python
import sys
from events_utils import collect_events, prepare_email

sys.path.append('/afs/ir.stanford.edu/users/y/y/yymao/cgi-bin/kipac-teabot')
from email_server import email_server

entries, __, dates_next_week = collect_events()
to, subject, msg = prepare_email(entries, dates_next_week)

if msg:
    email = email_server()
    email.send('KIPAC TeaBot <teabot@kipac.stanford.edu>', to, subject, msg)
    email.close()

