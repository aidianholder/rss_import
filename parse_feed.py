import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import sqlite3
import html
from PIL import Image


FEED_SHORT = "SI"
FEED_ID = {"SI": "https://www.si.com/.rss/full"}
FEED_URL = FEED_ID[FEED_SHORT]
DIR_NAME = os.path.expanduser("~/Documents/src/rss_import/")

ns = {
        'dc': "http://purl.org/dc/elements/1.1/",
        'media': 'http://search.yahoo.com/mrss/',
        'content': 'http://purl.org/rss/1.0/modules/content/'
    }


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
            title = title_raw.text
            byline = item.find('dc:creator', ns).text
            pubdate_raw = item.find('pubDate').text
            pubdate = process_pubdate(pubdate_raw)
            abstract_raw = item.find('abstract').text
            abstract_clean = html.unescape(abstract_raw)
            content_raw = item.find('content:encoded')
            if content_raw.text.find(abstract_raw) != -1:
                s = content_raw.text.find(abstract_raw)
                l = len(abstract_raw)
                slice = s + l + 4
                content_trimmed = content_raw.text[slice:]
            else:
                content_trimmed = content_raw.text
            content_trimmed = html.unescape(content_trimmed)
            capture_photos(item, pubdate)

def capture_photos(story_to_process, date_string_filename):
    lede_photo_raw = story_to_process.find('enclosure')
    if lede_photo_raw.attrib['type'] == 'image/jpeg':
        lede_photo_image_raw = requests.get(lede_photo_raw.attrib['url'], stream=True)
        if lede_photo_image_raw.status_code == 200:
            file_name = lede_photo_raw.attrib['url'].split('/')[-1:]
            file_name = date_string_filename + file_name[0]
            with open(file_name, 'wb') as lede_photo_image_file:
                for chunk in lede_photo_image_raw:
                    file_name.write(chunk)
            lede_photo = Image.open(file_name)
            lede_photo_width = lede_photo.width
            lede_photo_height = lede_photo.height
            import_directory = "/imports/adg/photos/"
            photo_string = import_directory + file_name
            #todo - ftp photos to import directory on ftp









def process_pubdate(string_to_convert):
    td = timedelta(hours=-6)
    pubdate_object = datetime.strptime(string_to_convert, "%a, %d %b %Y %H:%M:%S %Z")
    pubdate_local = pubdate_object + td
    pubdate_clean = pubdate_local.strftime("%Y%m%d")
    pubtime_clean = pubdate_local.strftime("%H%M")
    pubtime_string = pubdate_clean + pubtime_clean
    return pubtime_string






def get_guids(dbname, table_name):
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    old_stories = cur.execute("SELECT url FROM '%s'" % table_name)
    return old_stories.fetchall()




