#!../../../env/bin/python
'''
This script will query all messages new as of yesterday and ensure
that they exist in the archive
'''

# Standalone broilerplate -------------------------------------------------------------
from django_setup import do_setup
do_setup()
# -------------------------------------------------------------------------------------

import argparse
import datetime
import os
from django.conf import settings
# from haystack.query import SearchQuerySet
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from mlarchive.archive.models import Message

import logging
logpath = os.path.join(settings.DATA_ROOT, 'log/check_index24.log')
logging.basicConfig(filename=logpath, level=logging.DEBUG)


def main():
    parser = argparse.ArgumentParser(description='Check that messages are indexed')
    parser.add_argument('--age', type=int, default=24, help="Check messages this many hours old.  Default is 24.")
    parser.add_argument('-f', '--fix', help="perform fix", action='store_true')
    args = parser.parse_args()
    now = datetime.datetime.now(datetime.timezone.utc)
    start = now - datetime.timedelta(hours=args.age)
    end = now - datetime.timedelta(minutes=1)
    count = 0
    stat = {}
    client = Elasticsearch()
    messages = Message.objects.filter(updated__gte=start, updated__lt=end)
    for message in messages:
        s = Search(using=client, index=settings.ELASTICSEARCH_INDEX_NAME)
        s = s.query('match', msgid=message.msgid)
        s = s.query('match', email_list=message.email_list.name)
        if s.count() != 1:
            print("Message not indexed.  {list}: {msgid}".format(
                list=message.email_list,
                msgid=message.msgid))
            count = count + 1
            logging.warning(message.msgid + '\n')
            stat[message.email_list.name] = stat.get(message.email_list.name, 0) + 1
            if args.fix:
                message.save()
            
    print("Index Check {date}".format(date=start.strftime('%Y-%m-%d')))
    print("Checked {count}".format(count=messages.count()))
    print("Missing {count}".format(count=count))
    for k, v in list(stat.items()):
        print("{}:{}".format(k, v))

    
if __name__ == "__main__":
    main()
