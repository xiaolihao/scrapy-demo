# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import MySQLdb

import scrapy
from scrapy.http import Request
from scrapy.exceptions import DropItem
import spiders.user_settings
from datetime import datetime  
import binascii
import sys
import pymongo
import hashlib
from scrapy.pipelines.images import ImagesPipeline
import xutil
import base64
import mimetypes
import settings

class XImagesPipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        if 'image_urls' in item.fields:
            for image_url in item['image_urls']:
                yield scrapy.Request(image_url)

    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]

        for path in image_paths:
            with open(settings.IMAGES_STORE+'/'+path, 'rb') as image_file:
                base64_str = base64.b64encode(image_file.read())
                mime_type = mimetypes.guess_type(path)
                collection = xutil.Util.get_mongodb()[spiders.user_settings.MONGODB['img_collection']]
                url_sha1 = hashlib.sha1(item['src_url']).hexdigest()
                collection.insert({'url_sha1': url_sha1, 'img_raw': base64_str, 'mime_type': mime_type[0]})
        
        return item


class MongoDBPipeline(object):

    def __init__(self):
        self.collection = xutil.Util.get_mongodb()[spiders.user_settings.MONGODB['raw_collection']]

    def process_item(self, item, spider):
        url_sha1 = hashlib.sha1(item['src_url']).hexdigest()
        base64_str = base64.b64encode(item['html_raw'])
        self.collection.insert({'url_sha1':url_sha1, 'html_raw': base64_str})
        
        return item

class MySQLStorePipeline(object):

    def __init__(self):
        self.connection = MySQLdb.connect(spiders.user_settings.MYSQL['host'], 
			spiders.user_settings.MYSQL['username'],
        	spiders.user_settings.MYSQL['password'],
        	spiders.user_settings.MYSQL['database'])
        self.cursor = self.connection.cursor()

    def process_finance_event(self, item):
        _org_url_crc32s = []
        for url in item['org_urls']:
            if sys.version_info[0] == 3:
                _org_url_crc32s.append(binascii.crc32(url))
            else:
                _org_url_crc32s.append(binascii.crc32(url)% (1<<32))


        if len(item['org_urls']) == 0:
            org_url_crc32s = ''
            org_urls = ''
        else:
            org_url_crc32s = ', '.join(str(x) for x in _org_url_crc32s)
            org_urls = ','.join(item['org_urls'])

        snapshot_id = hashlib.sha1(item['src_url']).hexdigest()

        sql = """INSERT INTO tfinance_event(event_time,"""\
                """crawl_time,"""\
                """title,"""\
                """summary,"""\
                """company_url_crc32,"""\
                """company_url,"""\
                """round,"""\
                """amount,"""\
                """per,"""\
                """org_url_crc32s,"""\
                """org_urls,"""\
                """demostic,"""\
                """state,"""\
                """src,"""\
                """src_url,"""\
                """snapshot_id)"""\
                """VALUES ('%s','%s','%s','%s',crc32('%s'),'%s','%s','%s','%s','%s','%s',%d,%d,'%s','%s','%s')""" % (item['time'],
                item['crawl_time'],
                item['title'],
                item['summary'],
                item['company_url'],
                item['company_url'],
                item['tround'],
                item['tamount'],
                item['tper'],
                org_url_crc32s,
                org_urls,
                item['demostic'],
                0,
                item['src'],
                item['src_url'],
                snapshot_id)

        try:
            self.cursor.execute(sql)
            self.connection.commit()
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])

    def process_demostic_company(self, item):
        logo_id = hashlib.sha1(item['src_url']).hexdigest()

        sql = """INSERT INTO company(short_name,"""\
                """full_name,"""\
                """setup_time,"""\
                """crawl_time,"""\
                """location,"""\
                """type,"""\
                """src,"""\
                """src_url,"""\
                """logo_id,"""\
                """main_page_url,"""\
                """summary,"""\
                """demostic)"""\
                """VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%d)""" % (item['short_name'],
                item['full_name'],
                item['setup_time'],
                item['crawl_time'],
                item['location'],
                item['classify'],
                item['src'],
                item['src_url'],
                logo_id,
                item['main_page_url'],
                item['summary'],
                item['demostic'])

        try:
            self.cursor.execute(sql)
            self.connection.commit()
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])

        return item

    def process_item(self, item, spider):
        if item['ttype'] == 'finance_event':
            self.process_finance_event(item)

        if item['ttype'] == 'demostic_comp':
            self.process_demostic_company(item)
        return item


