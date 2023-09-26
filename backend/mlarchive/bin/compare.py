#!../../../env/bin/python
'''
Compare legacy archive with new archive and report descrepencies

Example:
./compare.py --start=2018-01-15T00:00:00

'''

# Standalone broilerplate -------------------------------------------------------------
from django_setup import do_setup
do_setup()
# -------------------------------------------------------------------------------------

import argparse
import datetime
import mailbox
import os

from dateutil.parser import *
from mlarchive.bin.scan_utils import all_mboxs
from mlarchive.archive.models import Message
from mlarchive.archive.mail import archive_message, MessageWrapper
from zoneinfo import ZoneInfo

TOTAL = 0 
MISSING = 0
IMPORTED = 0

pacific = ZoneInfo('US/Pacific')


def check_message(message, listname, load):
    global TOTAL, MISSING, IMPORTED
    TOTAL += 1
    
    try:
        msgid = message.get('Message-ID').strip('<>')
    except AttributeError:
        return
    
    try:
        _ = Message.objects.get(msgid=msgid, email_list__name=listname)
    except Message.DoesNotExist:
        MISSING += 1
        if load:
            status = archive_message(message.as_string(),
                                     listname,
                                     save_failed=False)
            if status == 0:
                status_message = 'imported'
                IMPORTED += 1
            else:
                status_message = 'import failed'
        else:
            status_message = ''
        print("%s, %s, %s, %s" % (listname, str(message['subject'])[:20], message['date'], status_message))

    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start', 
                        required=True,
                        help="enter the date to start comparison YYYY-MM-DDTHH:MM (UTC)")
    parser.add_argument('-e', '--end', help="enter the date to end comparison YYYY-MM-DDTHH:MM (UTC)")
    parser.add_argument('--list', help='restrict comparison to specified list')
    parser.add_argument('-l', '--load', action='store_true', help='import missing messages')
    args = parser.parse_args()
    
    start_date = parse(args.start).astimezone(datetime.timezone.utc)
    if args.end:
        end_date = parse(args.end).astimesone(datetime.timezone.utc)
    else:
        # if not passed in just set to future to capture everything
        end_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    compstring = start_date.strftime('%Y-%m')
    
    if args.list:
        listnames = [args.list]
    else:
        listnames = None

    for file in all_mboxs(listnames):
        basename = os.path.basename(file)
        if basename[:7] >= compstring:
            statinfo = os.stat(file)
            modified = datetime.datetime.fromtimestamp(statinfo.st_mtime, tz=datetime.timezone.utc)
            if modified > start_date:
                mbox = mailbox.mbox(file)
                for message in mbox:
                    if not message:
                        continue
                    listname = os.path.basename(os.path.dirname(file))
                    mw = MessageWrapper.from_message(message, listname)
                    msg_date = mw.get_date()
                    if start_date <= msg_date <= end_date:
                        check_message(message, listname, args.load)

    print("Total: %d\nMissing: %d\nImported: %d" % (TOTAL, MISSING, IMPORTED))


if __name__ == "__main__":
    main()
