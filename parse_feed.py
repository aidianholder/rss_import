import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import sqlite3
import html
from PIL import Image
import re
from ftplib import FTP

FEED_SHORT = "BETS"
FEED_ID = {"SI": "https://www.si.com/.rss/full", "BETS": "https://www.si.com/.rss/full/betting"}
FEED_URL = FEED_ID[FEED_SHORT]
DIR_NAME = os.getcwd()
DBNAME = 'feeds.db'
TABLE_NAME = "stories"
PUNCTUATION = re.compile("[:&',/]")


ns = {
        'dc': "http://purl.org/dc/elements/1.1/",
        'media': 'http://search.yahoo.com/mrss/',
        'content': 'http://purl.org/rss/1.0/modules/content/'
    }


class FeedStory:

    def __init__(self, guid, item):  # , title, hed, pubdate, subject, byline, content

        self.guid = guid
        self.published = None
        self.item = item
        self.title = self.item.find('title').text
        self.byline = None
        self.pubdate = None
        self.lede_photo = None
        self.status = 'unpublished'
        self.abstract = None
        self.content = None
        self.lede_photo = None
        self.filename = None
        self.given = None
        self.family = None

    category = 1170

    def get_byline(self):
        byline_element = self.item.find('dc:creator', ns)
        if byline_element is not None:
            self.byline = byline_element.text
        else:
            self.byline = None

    def new_or_repeat(self):
        old_guids = old_guid_list
        if self.guid not in old_guids:
            self.status = 'unpublished'
        else:
            self.status = 'published'

    def process_pubdate(self):
        pubdate_raw = self.item.find('pubDate').text
        td = timedelta(hours=-6)
        pubdate_object = datetime.strptime(pubdate_raw, "%a, %d %b %Y %H:%M:%S %Z")
        pubdate_local = pubdate_object + td
        pubdate_clean = pubdate_local.strftime("%Y%m%d") + 'T' + pubdate_local.strftime("%H%M")
        self.pubdate = pubdate_clean

    def get_abstract(self):
        abstract_raw = self.item.find('description').text
        self.abstract = html.unescape(abstract_raw)

    def main_content(self):
        content = html.unescape(self.item.find('content:encoded', ns).text)
        if self.lede_photo is not None:
            m = '<media media-type="image">\n'
            mr = '<media-reference mime-type="image/jpeg" source=' + self.lede_photo["location"] + ' height=' \
                 + str(self.lede_photo["height"]) + ' width=' + str(self.lede_photo["width"]) + ' />\n'
            mc = '</media>\n'
            content = content + m + mr + mc
        abstract_start = content.find(self.abstract)
        if abstract_start != -1:
            abstract_end = len(self.abstract) + 24
            self.content = content[abstract_end:]
        else:
            self.content = content

    def set_filename(self):
        file_name = self.title.replace(" ", "_")
        file_name = PUNCTUATION.sub("", file_name, count=0)
        file_name = file_name + ".xml"
        self.filename = file_name

    def capture_photo(self):
        # if there's a lede photo in enclosure element, download it and stash it in photos directory
        lede_photo_raw = self.item.find('enclosure')
        if lede_photo_raw.attrib['type'] == 'image/jpeg':
            lede_photo_image_raw = requests.get(lede_photo_raw.attrib['url'], stream=True)
            if lede_photo_image_raw.status_code == 200:
                file_name = lede_photo_raw.attrib['url'].split('/')[-1:]
                file_name = self.pubdate + file_name[0] + '.jpg'
                file_loc = os.getcwd() + '/photos/' + file_name
                # download it a chunk at a time
                with open(file_loc, 'wb') as lede_photo_image_file:
                    for chunk in lede_photo_image_raw:
                        lede_photo_image_file.write(chunk)
                    lede_photo_image_file.close()
                # get dimensions for photo via pil.image
                lede_photo = Image.open(file_loc)
                lede_photo_width = lede_photo.width
                lede_photo_height = lede_photo.height
                lede_photo.close()
                # directory/location where img will be uploaded on ellington ftp
                import_directory = "/imports/adg/photos/"
                photo_loc = import_directory + file_name
                # info to return for use in story file
                self.lede_photo = {'file': file_name, 'location': photo_loc, 'width': lede_photo_width,
                                   'height': lede_photo_height}
            else:
                pass

    def write_xml(self):
        out = open('stories/' + self.filename, 'w')
        out.write('<?xml version="1.0"?>\n')
        out.write('<nitf>\n\t<head>\n\t\t<title>' + self.title + '</title>\n')
        out.write('<meta name="robots" content="noindex" />')
        out.write('<meta name="canonical" content="' + self.guid + '" />')
        out.write('\t\t<docdata>\n')
        out.write('\t\t\t<date.release norm="' + self.pubdate + '" />\n\t\t</docdata>\n')
        out.write('\t\t<tobject tobject.type="news">\n\t\t\t<tobject.subject tobject.subject.type="' + str(self.category) + '" />\n')
        out.write('\t\t</tobject>\n\t\t\t<pubdata date.publication="' + self.pubdate + '" name="Arkansas Democrat-Gazette" position.section="A" />\n')
        out.write('\t\t<a rel="canonical" href="' + self.guid + '" />\n')
        out.write('\t</head>\n\t<body>\n\t\t<body.head>\n\t\t\t<hedline>\n')
        out.write('\t\t\t\t<hl1>' + self.title + '</hl1>\n')
        out.write('\t\t\t\t<hl2><![CDATA[]]></hl2>\n')
        out.write('\t\t\t</hedline>\n')
        if self.byline is not None:
            out.write('\t\t\t<byline>\n')
            out.write('\t\t\t\t<byttl>' + self.byline + '</byttl>\n')
            out.write('\t\t\t</byline>\n')
        out.write('\t\t\t<abstract><![CDATA[' + self.abstract + ']]></abstract>\n')
        out.write('\t\t\t</body.head>\n')
        out.write('\t\t\t<body.content>\n\t\t\t\t<![CDATA[' + str(self.content) + ']]>\n\t\t\t</body.content>\n')
        out.write('\t\t</body>\n')
        out.write('</nitf>')
        out.close()


def get_guids(dbname):
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    old_stories = cur.execute("SELECT url FROM stories")
    old_guids = old_stories.fetchall()
    old_guid_list = []
    for guid in old_guids:
        guid_string = guid[0]
        old_guid_list.append(guid_string)
    if len(old_guid_list) > 200:
        clear_guid(dbname)
    return old_guid_list


def write_guid(dbname, uid):
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    cur.execute("INSERT INTO stories VALUES(?)", (uid,))
    con.commit()


def clear_guid(dbname):
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    cur.execute("DELETE FROM stories")


def get_feed(feed_url):
    r = requests.get(feed_url)
    feed_file_name = FEED_SHORT + datetime.now().strftime('%Y%m%d%H%M%S')
    feed_path = DIR_NAME + feed_file_name + '.xml'
    f = open(feed_path, 'w')
    f.write(r.text)
    f.close()
    return feed_path


def sendfiles():
    dir_base = os.getcwd()
    dir_photos = dir_base + '/photos/'
    dir_stories = dir_base + '/stories/'
    FTP_address = os.getenv("FTPADDRESS")
    FTP_user = os.getenv('FTPUSER')
    FTP_password = os.getenv('FTPPASSWORD')
    with FTP(FTP_address) as ftp:
        ftp.login(user=FTP_user, passwd=FTP_password)
        ftp.cwd('/imports/adg/photos')
        os.chdir(dir_photos)
        photos = os.listdir(os.getcwd())
        for photo in photos:
            ftp.storbinary('STOR ' + photo, open(photo, 'rb'))
            os.remove(photo)
        ftp.cwd('/imports/adg')
        os.chdir(dir_stories)
        stories = os.listdir(os.getcwd())
        for tale in stories:
            ftp.storbinary('STOR ' + tale, open(tale, 'rb'))
            os.remove(tale)
        ftp.quit()
        os.chdir(dir_base)


tree = ET.parse(get_feed(FEED_URL))
old_guid_list = get_guids(DBNAME)
items = tree.findall('./channel/item')
for item in items:
    guid = item.find('guid').text
    story = FeedStory(guid, item)
    story.new_or_repeat()
    if story.status == 'unpublished':
        story.set_filename()
        story.process_pubdate()
        story.get_byline()
        story.get_abstract()
        story.capture_photo()
        story.main_content()
        story.write_xml()
        write_guid('feeds.db', story.guid)
sendfiles()