
# -*- coding: utf-8 -*-
import scrapy
import datetime
from scrapy.http import Request
from scrapy.loader import ItemLoader

# 定义好item.py后进行引入
from RCE.items import ZyysslItem, ArticleItemLoader
# 引入自定义的md5函数
from RCE.utils.common import get_md5


class DiySpider(scrapy.Spider):
    name = 'recpt'
    allowed_domains = ['www.zyyssl.com']
    start_urls = ['http://www.zyyssl.com/cookbook/85.html']

    def parse(self, response):
        """
        1. 获取菜谱列表页当中的url并交给scrapy下载解析
        2. 获取下一页的url并交给scrapy进行下载，下载完成之后交给parse
        （meta可以在Request中传递参数）
        """
        # 1
        for data in response.css('.wh_list a'):
            image_url = response.urljoin(data.css("img::attr(src)").get())
            next_url = data.xpath('@href').get()
            detail_url = response.urljoin(next_url)
            # meta
            yield Request(url=detail_url, meta={"front_image_url": image_url}, callback=self.parse_detail)
        next_page = response.urljoin(response.css('.flickr').xpath(".//a[contains(., '下一页»')]").attrib['href'])
        if next_page:
            yield Request(url=next_page, callback=self.parse)

    #  页面解析函数
    def parse_detail(self, response):
        # 实例化中国药膳食疗网item
        # article_item = ZyysslItem()
        #
        # front_image_url = response.meta.get("front_image_url", "")
        # title = response.xpath("//h1[@class='meta-tit']/text()").get()
        # create_date = response.xpath("//span[@class='time']/text()").get()  # 现在是字符串
        # try:
        #     create_date = datetime.datetime.strptime(create_date, '%Y/%m/%d %H:%M:%S')
        # except Exception as e:
        #     create_date = datetime.datetime.now()
        # pertain_to = response.xpath("//p[@class='meta-info']/text()")  # .getall()[3].strip().replace('分类：', '').strip()
        # content = response.xpath("//div[@class='entry']").get()
        #
        # article_item["title"] = title
        # article_item["create_date"] = create_date
        # article_item["url"] = response.url
        # article_item["url_object_id"] = get_md5(response.url)
        # article_item["front_image_url"] = [front_image_url]  # 由于不是数组报错：ValueError('Missing scheme in request url: %s' % self._url)
        # article_item["pertain_to"] = pertain_to
        # article_item["content"] = content
        # 通过ItemLoader加载item
        front_image_url = response.meta.get("front_image_url", "")
        item_loader = ArticleItemLoader(item=ZyysslItem(), response=response)
        item_loader.add_xpath('title', "//h1[@class='meta-tit']/text()")
        item_loader.add_value('url', response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_value("front_image_url", [front_image_url])
        item_loader.add_xpath("create_date", "//span[@class='time']/text()")
        item_loader.add_xpath("content", "//div[@class='entry']")
        item_loader.add_xpath("pertain_to", "//p[@class='meta-info']/text()")
        article_item = item_loader.load_item()


        yield article_item  # 传递至pipeline(应注意将setting.py里的ITEM_PIPELINES的注释去掉)
