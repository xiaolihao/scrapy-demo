# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import pybloomfilter
import os
import user_settings
from .. import items
from datetime import datetime  
from .. import xutil

class Board:
    def __init__(self, base_url):
        self.base_url = base_url['url']
        self.type = base_url['type']
        self.cur_page = 1
        self.state = 1
        self.stack = []
        self.page = 1

    def add_url(self, url):
        self.stack.append(url)

    def get_url(self):
        url = ''
        subtype = ''
        if len(self.stack) == 0 and self.page == 1:
            url = self.base_url + str(self.cur_page)
            self.cur_page += 1
            subtype = 'p_'
        elif len(self.stack) == 0 and self.page != 1:
            return None
        else:
            url = self.stack.pop(0)
            subtype = 'i_'
        return {'url': url, 'type': subtype + self.type}

    def stop(self):
        self.state = 0

    def stop_page(self):
        self.page = 0

class TaskSchedule:
    boards = []
    cur_board = 0

    def __init__(self, base_urls):
        for base_url in base_urls:
            TaskSchedule.boards.append(Board(base_url))

    def get_url(self):
        b = TaskSchedule.boards[TaskSchedule.cur_board]
        url = b.get_url()
        if b.state != 1 or url == None:
            del TaskSchedule.boards[TaskSchedule.cur_board]
            if len(TaskSchedule.boards) == 0:
                return None

            TaskSchedule.cur_board = 0
            b = TaskSchedule.boards[TaskSchedule.cur_board]
            url = b.get_url()

        TaskSchedule.cur_board += 1
        if TaskSchedule.cur_board >= len(TaskSchedule.boards):
            TaskSchedule.cur_board = 0

        return url

    def get_board(self, board_type):
        for board in TaskSchedule.boards:
            if board.type == board_type:
                return board
        return None

    def add_url(self, url, board_type):
        b = self.get_board(board_type)
        b.add_url(url)

class ItjiziSpider(scrapy.Spider):
    name = 'itjizi'

    def __init__(self, *args, **kwargs):
        super(ItjiziSpider, self).__init__(*args, **kwargs)
        self.schedule = TaskSchedule(user_settings.BASE_URLS)
        self.func_dic = {
            'p_demostic_ivst': self.parase_p_demostic_ivst,
            'i_demostic_ivst': self.parase_i_demostic_ivst,
            'p_demostic_merger': self.parase_p_demostic_merger,
            'i_demostic_merger': self.parase_i_demostic_merger,
            'p_foreign_ivst': self.parase_p_foreign_ivst,
            'i_foreign_ivst': self.parase_i_foreign_ivst,
            'p_foreign_merger': self.parase_p_foreign_merger,
            'i_foreign_merger': self.parase_i_foreign_merger,
            'p_demostic_comp': self.parase_p_demostic_comp,
            'i_demostic_comp': self.parase_i_demostic_comp,
            'i_unknow': self.parase_unknow,
            'p_unknow': self.parase_unknow
        }
        if os.path.exists('itjizi.bloom'):
            self.filter = pybloomfilter.BloomFilter.open('itjizi.bloom')
        else:
            self.filter = pybloomfilter.BloomFilter(user_settings.FILTER_SIZE,user_settings.FILTER_ERROR_RATE,'itjizi.bloom')

    def start_requests(self):
        return [scrapy.FormRequest(user_settings.LOGIN_URL,
                                   formdata=user_settings.FORM_INFO,
                                   callback=self.logged_in)]

    def err_process(self, response):
        if isinstance(failure.value, HttpError):
            response = failure.value.response
            self.logger.error('error %s %d', response.url, response.status)
            xutil.Util.send_mail(user_settings.NOTIFY_MAIL['HOST'],
                user_settings.NOTIFY_MAIL['FROM']['MAIL'],
                user_settings.NOTIFY_MAIL['FROM']['PASSWORD'],
                user_settings.NOTIFY_MAIL['TO_LIST'],
                str(response))

    def parase_p_demostic_ivst(self, response):
        self.logger.info('crawled %s %d', response.url, response.status)
        urls = response.css('ul.list-main-eventset:last-child').xpath('./li/i[2]/a/@href').extract()

        if len(urls) == 0:
            self.schedule.get_board('demostic_ivst').stop()
        else:
            num = 0
            for url in urls:
                # MUST use str(url) to translate
                if str(url) in self.filter:

                    # python DO NOT support ++
                    num += 1
                    self.logger.info('dup page %s', url)
                else:
                    self.schedule.add_url(url, 'demostic_ivst')
            if num > user_settings.MAX_DUP_URL:
                self.schedule.get_board('demostic_ivst').stop_page()

        dic = self.schedule.get_url()
        if dic is not None:
            yield Request(url=dic['url'], dont_filter=True, callback=self.func_dic[dic['type']], errback=self.err_process)

    def parase_i_demostic_ivst(self, response):
        self.logger.info('crawled %s %d', response.url, response.status)

        # parase info
        info_block = response.css('div.block')
        title_block = info_block.css('div.titlebar-center').xpath('./p/span[1]/text()').extract()
        title = title_block[0]
        time = title_block[1]

        summary = ''
        _summary = info_block.xpath('//div[2]/p/text()').extract()
        if len(_summary) > 0:
            summary = _summary[0]
        
        detail_info = info_block.css('div.block-inc-fina')

        # crc32&url to db
        company_url = detail_info.xpath('//td[1]/a/@href').extract()[0]
        tround = detail_info.xpath('//td[3]/span/text()').extract()[1]
        tamount = detail_info.xpath('//td[4]/span/text()').extract()[1]
        tper = detail_info.xpath('//td[5]/span/text()').extract()[1].lstrip().rstrip()
        org_urls = response.css('ul.list-prodcase').xpath('//li/div/div[1]/a/@href').extract()

        # add to bloomfilter
        self.filter.add(response.url)
        dic = self.schedule.get_url()
        if dic is not None:
            yield Request(url=dic['url'], dont_filter=True, callback=self.func_dic[dic['type']], errback=self.err_process)

        item = items.FinaceEventItem()
        item['src'] = 'itjizi'
        item['src_url'] = response.url
        item['ttype'] = 'finance_event'
        item['demostic'] = 1
        item['title'] = title
        item['time'] = time
        item['summary'] = summary
        item['company_url'] = company_url
        item['tround'] = tround
        item['tamount'] = tamount
        item['tper'] = tper
        item['org_urls'] = org_urls
        item['html_raw'] = response.body
        item['crawl_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        yield item

    def parase_p_demostic_comp(self, response):
        self.logger.info('crawled %s %d', response.url, response.status)
        urls = response.css('ul.list-main-icnset:last-child').xpath('./li/i[1]/a/@href').extract()

        if len(urls) == 0:
            self.schedule.get_board('demostic_comp').stop()
        else:
            num = 0
            for url in urls:
                # MUST use str(url) to translate
                if str(url) in self.filter:

                    # python DO NOT support ++
                    num += 1
                    self.logger.info('dup page %s', url)
                else:
                    self.schedule.add_url(url, 'demostic_comp')
            if num > user_settings.MAX_DUP_URL:
                self.schedule.get_board('demostic_comp').stop_page()

        dic = self.schedule.get_url()
        if dic is not None:
            yield Request(url=dic['url'], dont_filter=True, callback=self.func_dic[dic['type']], errback=self.err_process)

    def parase_i_demostic_comp(self, response):
        self.logger.info('crawled %s %d', response.url, response.status)
        info_block = response.css('div.rowhead')
        _logo_url = info_block.css('div.pic').xpath('./img/@src').extract()
        logo_url = ''
        if len(_logo_url) > 0:
            logo_url = _logo_url[0]

        _short_name = info_block.css('div.picinfo div.line-title span.title').xpath('./b/text()').extract()
        short_name = _short_name[0].lstrip().rstrip()

        _classify = info_block.css('div.picinfo div.info-line').xpath('./span[1]/a/text()').extract()
        classify = ''
        if len(_classify) > 1:
            classify = _classify[1]

        _location = info_block.css('div.picinfo div.info-line').xpath('./span[2]/a/text()').extract()
        location = '-'.join(_location)

        main_page_url = ''
        _main_page_url = info_block.css('div.picinfo div.link-line').xpath('./a/@href').extract()
        if len(_main_page_url) > 0:
            main_page_url = _main_page_url[0]

        _summary = response.css('div.main div.sec div.des').xpath('./text()').extract()
        summary = ''
        if len(_summary) > 0:
            summary = _summary[0].lstrip().rstrip()

        _full_name = response.css('div.main div.sec div.des-more').xpath('./div[1]/span/text()').extract()
        full_name = ''
        if len(_full_name) > 0:
            t = _full_name[0].split(u'：')
            if len(t) > 1:
                full_name = t[1].lstrip().rstrip()
            else:
                full_name = t[0].lstrip().rstrip()

        _setup_time = response.css('div.main div.sec div.des-more').xpath('./div[2]/span/text()').extract()
        setup_time = ''
        if len(_setup_time) > 0:
            t = _setup_time[0].split(u'：')
            if len(t) > 1:
                setup_time = t[1]
            else:
                setup_time = t[0]
                
            l=len(setup_time.split('.'))
            if l == 1:
                setup_time += '.01.01'
            elif l == 2:
                setup_time += '.01'

        item = items.CompanyItem()
        item['setup_time'] = setup_time
        item['full_name'] = full_name
        item['summary'] = summary
        item['main_page_url'] = main_page_url
        item['location'] = location
        item['classify'] = classify
        item['short_name'] = short_name

        item['image_urls'] = logo_url.split()

        item['src'] = 'itjizi'
        item['src_url'] = response.url
        item['ttype'] = 'demostic_comp'
        item['demostic'] = 1

        item['html_raw'] = response.body
        item['crawl_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # add to bloomfilter
        self.filter.add(response.url)
        dic = self.schedule.get_url()
        if dic is not None:
            yield Request(url=dic['url'], dont_filter=True, callback=self.func_dic[dic['type']], errback=self.err_process)

        yield item
    def parase_p_demostic_merger(self, response):
        pass

    def parase_i_demostic_merger(self, response):
        pass

    def parase_p_foreign_ivst(self, response):
        pass
    def parase_i_foreign_ivst(self, response):
        pass

    def parase_p_foreign_merger(self, response):
        pass
    def parase_i_foreign_merger(self, response):
        pass

    def parase_unknow(self, response):
        pass

    def logged_in(self, response):
        dic = self.schedule.get_url()
        yield Request(url=dic['url'], dont_filter=True, callback=self.func_dic[dic['type']])





