import os
import requests
# from lxml import etree as ET
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import sqlite3
import html
from PIL import Image
# from xml.dom import minidom
import re
from ftplib import FTP

FEED_SHORT = "BETS"
FEED_ID = {"SI": "https://www.si.com/.rss/full", "BETS": "https://www.si.com/.rss/full/betting"}
FEED_URL = FEED_ID[FEED_SHORT]
DIR_NAME = os.getcwd()  # path.expanduser("~/src/rss_import/")
DBNAME = 'feeds.db'
TABLE_NAME = "stories"
PUNCTUATION = re.compile("[:&',/]")


ns = {
        'dc': "http://purl.org/dc/elements/1.1/",
        'media': 'http://search.yahoo.com/mrss/',
        'content': 'http://purl.org/rss/1.0/modules/content/'
    }


class FeedStory:

    def __init__(self, guid, item): # , title, hed, pubdate, subject, byline, content

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
            '''try:
                split_byline = self.byline.split(" ")
                self.given = split_byline[0]
                self.family = split_byline[1]
            except:
                pass'''
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
                # file_loc = '/Users/aidianholder/src/rss_import/photos' + file_name
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
                # directory/location where img will be uploaded
                import_directory = "/imports/adg/photos/"
                photo_loc = import_directory + file_name
                # info to return for use in story file
                self.lede_photo = {'file': file_name, 'location': photo_loc, 'width': lede_photo_width,
                                   'height': lede_photo_height}
            else:
                pass

    def write_xml(self):
        out = open('stories/' +  self.filename, 'w')
        out.write('<?xml version="1.0"?>\n')
        out.write('<nitf>\n\t<head>\n\t\t<title>' + self.title + '</title>\n')
        out.write('<meta name="robots" content="noindex" />')
        out.write('<meta name="canonical" content' + self.guid + ' />')
        out.write('\t\t<docdata>\n')
        out.write('\t\t\t<date.release norm="' + self.pubdate + '" />\n\t\t</docdata>\n')
        out.write('\t\t<tobject tobject.type="news">\n\t\t\t<tobject.subject tobject.subject.type="' + str(self.category) + '" />\n')
        out.write('\t\t</tobject>\n\t\t\t<pubdata date.publication="' + self.pubdate + '" name="Arkansas Democrat-Gazette" position.section="A" />\n')
        out.write('\t\t<a rel="canonical" href="' + self.guid + '" />\n')
        out.write('\t</head>\n\t<body>\n\t\t<body.head>\n\t\t\t<hedline>\n')
        out.write('\t\t\t\t<hl1>' + self.title + '</hl1>\n')
        out.write('\t\t\t\t<hl2><![CDATA[]]></hl2>\n')
        # out.write('\t\t\t\t<hl3><![CDATA[]]></hl3>\n')
        # out.write('\t\t\t\t<hl4><![CDATA[]]></hl4>\n')
        out.write('\t\t\t</hedline>\n')
        if self.byline is not None:
            out.write('\t\t\t<byline>\n')
            out.write('\t\t\t\t<byttl>' + self.byline + '</byttl>\n')
            # out.write('\t\t\t\t<person><name.given>' + self.given + '</name.given><name.family>' + self.family + ' </name.family></person>\n')
            out.write('\t\t\t</byline>\n')
        out.write('\t\t\t<abstract><![CDATA[' + self.abstract + ']]></abstract>\n')
        out.write('\t\t\t</body.head>\n')
        out.write('\t\t\t<body.content>\n\t\t\t\t<![CDATA[' + str(self.content) + ']]>\n\t\t\t</body.content>\n')
        out.write('\t\t</body>\n')
        out.write('</nitf>')
        out.close()
        '''p = open('out_test.xml', 'r')
        print(p.read())
        p.close()'''


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

    '''def write_xml(self):
        out_root = ET.Element('nitf')
        out_head = ET.Element('head')
        out_root.append(out_head)
        ET.SubElement(out_head, 'title', {'text': self.title})
        ET.SubElement(out_head, 'docdata')
        ET.SubElement(out_head, 'date.release', {'norm':self.pubdate})
        # out_date_release = ET.SubElement(out_docdata, 'date.release')
        # out_date_release.norm = self.pubdate
        out_tobject = ET.SubElement(out_head, 'tobject', {'tobject.type':'news'})
        # out_tobject.set('tobject.type', 'news')
        ET.SubElement(out_tobject, 'tobject.subject', {'toobject.subject.type': str(self.category)})
        ET.SubElement(out_head, 'pubdata', {'type':'print', 'date.publication':self.pubdate, 'name': 'Arkansas Democrat Gazette', 'position.section':'A Section'})
        out_body = ET.Element('body')
        out_root.append(out_body)
        out_body_head = ET.SubElement(out_body, 'body.head')
        out_headline = ET.SubElement(out_body_head, 'headline')
        ET.SubElement(out_headline, 'h11', {'text':  self.title  })
        ET.SubElement(out_headline, 'hl2', {'text':  self.abstract })
        out_byline = ET.SubElement(out_body, 'byline')
        ET.SubElement(out_byline, 'person')
        ET.SubElement(out_byline, 'byttl', {'text':  self.byline })
        ET.SubElement(out_body_head, 'abstract', {'text':  self.abstract })
        if self.lede_photo:
            m = '<media media-type="image">\n'
            mr = '<media-reference mime-type="image/jpeg" source=' + self.lede_photo["location"] + ' height=' + str(self.lede_photo["height"]) + ' width=' + str(self.lede_photo["width"]) + '/>\n'
            mc = '</media>\n'
            self.content = self.content + m + mr + mc
        ET.SubElement(out_body, "body.content", {'text': self.content })
        tree = ET.ElementTree(out_root)
        # ce = tree.find('./body/body.content')
        # print(ce.attrib['text'])
        tree.write('/Users/aidianholder/src/rss_import/out_test_7.xml', encoding="utf-8", xml_declaration=True)
        xsr = minidom.parse('/Users/aidianholder/src/rss_import/out_test_7.xml')
        xsrp = xsr.toprettyxml(indent="  ")
        print(xsrp)
        # xsr = minidom.parseString(xs)
        # xsrp = xsr.toprettyxml(indent="  ")
        # r = re.compile('&lt;')
        # print(r.findall(xsrp))
        # xsrp.replace("&lt;!", "<!")
        # print(type(xsrp))
        # print(xsrp)'''


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
    with FTP('upload.ellingtoncms.com') as ftp:
        ftp.login(user='wehco@wehco', passwd='kninQuetHo')
        ftp.cwd('/imports/adg/photos')
        os.chdir(dir_photos)
        photos = os.listdir(os.getcwd())
        for photo in photos:
            ftp.storbinary('STOR ' + photo, open(photo, 'rb'))
            os.remove(photo)
        ftp.cwd('/imports/adg')
        os.chdir(dir_stories)
        stories = os.listdir(os.getcwd())
        for story in stories:
            ftp.storbinary('STOR ' + story, open(story, 'rb'))
            os.remove(story)
        ftp.quit()
        os.chdir(dir_base)


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


# f = open('/Users/aidianholder/src/rss_import/feed.xml', 'r')
# tree = ET.fromstring(f.read())
tree = ET.parse(get_feed(FEED_URL))
# tree = ET.parse('BETS20221010112149.xml')
old_guid_list = get_guids(DBNAME)
items = tree.findall('./channel/item')
for item in items:
    guid = item.find('guid').text
    story = FeedStory(guid, item)
    story.new_or_repeat()
    if story.status == 'unpublished':
        story.set_filename()
        story.process_pubdate()
        story.get_abstract()
        story.capture_photo()
        story.main_content()
        story.write_xml()
        write_guid('feeds.db', story.guid)
sendfiles()












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




