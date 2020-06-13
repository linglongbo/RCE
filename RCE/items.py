# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import datetime
from scrapy.loader import ItemLoader  # 以定义自己的ItemLoader【避免多次使用output_processor=TakeFirst（获取数组第一个值）】
from scrapy.loader.processors import MapCompose, TakeFirst, Join  # 【MapCompose】为ItemLoader传递函数/【TakeFirst】在ItemLoader的数组取出值


class RceItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


# 定义ItemLoader的处理函数
def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, '%Y/%m/%d %H:%M:%S')
    except Exception as e:
        create_date = datetime.datetime.now()
    return create_date


def get_pertain(value):
    # 取出【类别】
    if "分类" in value:
        test = value.strip().replace('分类：', '').strip()
        return test
    else:
        return ""


def return_value(value):
    return value


# 定义ItemLoader
class ArticleItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class ZyysslItem(scrapy.Item):
    title = scrapy.Field()
    create_date = scrapy.Field(input_processor=MapCompose(date_convert))  # 函数处理
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(output_processor=return_value)
    # 为下载图片做准备
    front_image_path = scrapy.Field()
    pertain_to = scrapy.Field(input_processor=MapCompose(get_pertain), output_processor=Join(''))
    content = scrapy.Field()
