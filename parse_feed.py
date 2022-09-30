import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import sqlite3

FEED_SHORT = "SI"
FEED_ID = {"SI": "https://www.si.com/.rss/full"}
FEED_URL = FEED_ID[FEED_SHORT]
DIR_NAME = os.path.expanduser("~/Documents/src/rss_import/")


class feed_story:

    def __init__(self, guid, title, hed, pubdate, subject, byline, content):

        self.guid = guid
        self.title = title
        self.hed = hed
        self.pubdate = pubdate
        self.subject = subject
        self.byline = byline
        self.content = content

    category = 1170


def get_feed(FEED_URL):
    r = requests.get(FEED_URL)
    feed_file_name = FEED_SHORT + datetime.now().strftime('%Y%m%d%H%M%S')
    f = open(DIR_NAME + feed_file_name, 'w')
    f.write(r.text)
    f.close()

def parse_feed(file_name):
    f = open(file_name, 'r')
    root_element = ET.fromstring(f.read())
    items = root_element.find('channel').findall('item')
    url_list = get_guids("feeds.db", "stories")
    for item in items:
        guid = item.find("guid")
        if guid not in url_list:
            title_raw = item.find('title')
            title = ET.fromstring(title_raw)







def get_guids(dbname, table_name):
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    old_stories = cur.execute("SELECT url FROM '%s'" % table_name)
    return old_stories.fetchall()




