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


class FeedStory:

    def __init__(self, guid, item): #, title, hed, pubdate, subject, byline, content

        self.guid = guid
        self.item = item
        self.title = self.item.find('title').text
        self.byline = self.item.find('dc:creator', ns).text

    category = 1170

    def new_or_repeat(self):
        con = sqlite3.connect("feeds.db")
        cur = con.cursor()
        old_stories = cur.execute("SELECT url FROM stories")
        old_guids = old_stories.fetchall()
        if self.guid not in old_guids:
            self.status = 'unpublished'
        else:
            self.status = 'published'

    '''def get_title(self):
        return self.item.find('title').text

    def get_byline(self):
        self.byline = self.item.find('dc:creator', ns).text'''

    def process_pubdate(self):
        pubdate_raw = self.item.find('pubDate').text
        td = timedelta(hours=-6)
        pubdate_object = datetime.strptime(pubdate_raw, "%a, %d %b %Y %H:%M:%S %Z")
        pubdate_local = pubdate_object + td
        pubdate_clean = pubdate_local.strftime("%Y%m%d")
        pubtime_clean = pubdate_local.strftime("%H%M")
        pubtime_string = pubdate_clean + pubtime_clean
        self.pubdate = pubtime_string

    def get_abstract(self):
        abstract_raw = self.item.find('description').text
        self.abstract = html.unescape(abstract_raw)

    def main_content(self):
        content_raw = self.item.find('content:encoded', ns)
        content_escaped = html.unescape(content_raw.text)
        abstract_start = content_escaped.find(self.abstract)
        if abstract_start != -1:
            abstract_end = len(self.abstract) + 4
            return content_escaped[abstract_end:]
        else:
            return content_escaped

    def capture_photo(self):
        lede_photo_raw = self.item.find('enclosure')
        if lede_photo_raw.attrib['type'] == 'image/jpeg':
            lede_photo_image_raw = requests.get(lede_photo_raw.attrib['url'], stream=True)
            if lede_photo_image_raw.status_code == 200:
                file_name = lede_photo_raw.attrib['url'].split('/')[-1:]
                file_name = self.pubdate + file_name[0]
                file_loc = '/Users/aidianholder/src/rss_import/' + file_name
                with open(file_loc, 'wb') as lede_photo_image_file:
                    for chunk in lede_photo_image_raw:
                        lede_photo_image_file.write(chunk)
                    lede_photo_image_file.close()
                #get dimensions for photo via pil.image
                lede_photo = Image.open(file_loc)
                lede_photo_width = lede_photo.width
                lede_photo_height = lede_photo.height
                lede_photo.close()
                #directory/location where img will be uploaded
                import_directory = "/imports/adg/photos/"
                photo_loc = import_directory + file_name
                #info to return for use in story file
                self.lede_photo = [file_name, photo_loc, lede_photo_width, lede_photo_height]
                #todo - ftp photos to import directory on ftp
            else:
                pass


def get_feed(FEED_URL):
    r = requests.get(FEED_URL)
    feed_file_name = FEED_SHORT + datetime.now().strftime('%Y%m%d%H%M%S')
    f = open(DIR_NAME + feed_file_name, 'w')
    f.write(r.text)
    f.close()

'''def parse_feed(file_name):
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
            abstract_raw = item.find('description').text
            abstract_clean = html.unescape(abstract_raw)
            content_raw = item.find('content:encoded', ns)
            if content_raw.text.find(abstract_raw) != -1:
                s = content_raw.text.find(abstract_raw)
                l = len(abstract_raw)
                slice = s + l + 4
                content_trimmed = content_raw.text[slice:]
            else:
                content_trimmed = content_raw.text
            content_trimmed = html.unescape(content_trimmed)
            lede_photo = capture_photo(item, pubdate)
            write_guid('feeds.db', 'stories', 'url', guid)'''

def write_xml(story):
    pass


f = open('/Users/aidianholder/src/rss_import/feed.xml', 'r')
tree = ET.fromstring(f.read())
items = tree.findall('./channel/item')
item = items[0]
guid = item.find('guid').text
story = FeedStory(guid, item)
story.process_pubdate()
story.get_abstract()
story.main_content()
story.capture_photo()
print(dir(story))






'''def capture_photo(story_to_process, date_string_filename):
    lede_photo_raw = story_to_process.find('enclosure')
    if lede_photo_raw.attrib['type'] == 'image/jpeg':
        lede_photo_image_raw = requests.get(lede_photo_raw.attrib['url'], stream=True)
        if lede_photo_image_raw.status_code == 200:
            file_name = lede_photo_raw.attrib['url'].split('/')[-1:]
            file_name = date_string_filename + file_name[0]
            with open(file_name, 'wb') as lede_photo_image_file:
                for chunk in lede_photo_image_raw:
                    lede_photo_image_file.write(chunk)
            lede_photo_image_file.close()
            #get dimensions for photo via pil.image
            lede_photo = Image.open(file_name)
            lede_photo_width = lede_photo.width
            lede_photo_height = lede_photo.height
            lede_photo.close()
            #directory/location where img will be uploaded
            import_directory = "/imports/adg/photos/"
            photo_loc = import_directory + file_name
            #info to return for use in story file
            photo_deets = [photo_loc, lede_photo_width, lede_photo_height]
            #todo - ftp photos to import directory on ftp
    else:
        pass'''








'''def process_pubdate(string_to_convert):
    td = timedelta(hours=-6)
    pubdate_object = datetime.strptime(string_to_convert, "%a, %d %b %Y %H:%M:%S %Z")
    pubdate_local = pubdate_object + td
    pubdate_clean = pubdate_local.strftime("%Y%m%d")
    pubtime_clean = pubdate_local.strftime("%H%M")
    pubtime_string = pubdate_clean + pubtime_clean
    return pubtime_string'''






'''def get_guids(dbname, table_name):
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    old_stories = cur.execute("SELECT url FROM '%s'" % table_name)
    return old_stories.fetchall()'''

def write_guid(dbname, table_name, field_name, guid):
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    sql = " INSERT INTO " + table_name + "(" + field_name + ") VALUES(?)"
    cur.execute(sql, guid)
    con.commit()

# write_guid('feeds.db', 'stories', 'url', guid)

