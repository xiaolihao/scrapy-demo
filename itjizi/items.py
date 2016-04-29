# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class FinaceEventItem(scrapy.Item):
    # define the fields for your item here like:
    src = scrapy.Field()
    src_url = scrapy.Field()
    ttype = scrapy.Field()
    demostic = scrapy.Field()
    time = scrapy.Field()
    title = scrapy.Field()
    summary = scrapy.Field()
    company_url = scrapy.Field()
    tround = scrapy.Field()
    tamount = scrapy.Field()
    tper = scrapy.Field()
    org_urls = scrapy.Field()
    html_raw = scrapy.Field()
    crawl_time = scrapy.Field()

class CompanyItem(scrapy.Item):
    src = scrapy.Field()
    src_url = scrapy.Field()
    ttype = scrapy.Field()
    demostic = scrapy.Field()
    setup_time = scrapy.Field()
    crawl_time = scrapy.Field()
    short_name = scrapy.Field()
    full_name = scrapy.Field()
    summary = scrapy.Field()
    main_page_url = scrapy.Field()
    location = scrapy.Field()
    classify = scrapy.Field()
    html_raw = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()








