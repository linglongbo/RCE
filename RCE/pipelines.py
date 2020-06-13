# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# 引入scrapy自带的imagepipeline
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter  # scrapy自带的json保存
from twisted.enterprise import adbapi  # 将MySQLDB变为异步操作
from w3lib.html import remove_tags  # 移除content中HTML标签
from RCE.modles.es_types import AtricleType
# 为搜索补全【gen_suggests】函数做准备
from elasticsearch_dsl.connections import connections
es = connections.create_connection(AtricleType._doc_type.using)

import codecs  # 文件编码包
import json
import MySQLdb
import MySQLdb.cursors


class RcePipeline:
    def process_item(self, item, spider):
        return item


# 自定义pipeline
class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        """
        :param results:  获取图片的存放路径
        :param item:
        :param info:
        """
        if "front_image_path" in item:
            for ok, value in results:
                image_file_path = value["path"]
            item["front_image_path"] = image_file_path
        return item


# 将item储存至json文件【自定义的json存储】
class JsonWithEncoding(object):
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + '\n'  # 确保中文编码正常
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


class JsonExporterPipeline(object):
    # 调用scrapy提供的Json exporter导出json文件
    def __init__(self):
        self.file = open('articleexport.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


# 存储至MySQL数据库的pipeline【同步】
class Mysqlpipeline(object):
    def __init__(self):
        # 初始化数据库
        self.conn = MySQLdb.connect('localhost', 'root', '299086', 'article_spider', charset='utf8', user_unicode=True)
        self.cursor = self.conn.cursor()  # 数据库操作

    def process_item(self, item, spider):
        # sql语句
        insert_sql = """
                insert into rec_artivle(title, create_date, url, url_object_id, pertain_to) VALUES (%s,%s,%s,%s,%s)
                """
        # 执行插入数据到数据库操作
        self.cursor.execute(insert_sql, (item['title'], item['create_date'], item['url'], item['url_object_id'],
                                         item['pertain_to']))
        # 提交，不进行提交无法保存到数据库
        self.connect.commit()


# 存储至MySQL数据库的pipeline【异步】
class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)
        return cls(dbpool)

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)  # 指定操作方法和操作数据
        # 添加异常处理
        query.addErrback(self.handle_error, item, spider)

    def do_insert(self, cursor, item):
        # 对数据库进行插入操作，并不需要commit，twisted会自动commit
        insert_sql = """
                       insert into rec_artivle(title, create_date, url, url_object_id, pertain_to, content) VALUES (%s,%s,%s,%s,%s,%s)
                       """
        cursor.execute(insert_sql, (item['title'], item['create_date'], item['url'], item['url_object_id'],
                                    item['pertain_to'], item['content']))

    def handle_error(self, failure, item, spider):
        if failure:
            # 打印错误信息
            print(failure)


def gen_suggests(index, info_tuple):
    """
    :param index:
    :param info_tuple: 
    :return:
    """
    # 根据字符串生成搜索建议数组
    used_words = set()  # 为去重做准备【title：python重要性（10）、tags：python重要性（3）】
    suggests = []
    for text, weight in info_tuple:
        if text:
            # 调用es的analyze接口分析字符串
            words = es.indices.analyze(index=index, analyzer="ik_max_word", params={'filter':["lowercase"]}, body=text)
            anylyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"])>1])  # 【token】列表生成
            new_words = anylyzed_words - used_words
        else:
            new_words = set()
        if new_words:
            suggests.append({"input": list(new_words), "weight": weight})
    return suggests


class ElasticsearchPipeline(object):
    # 将数据写入到es
    def process_item(self, item, spider):
        # 将item变为es数据

        article = AtricleType()
        article.title = item["title"]
        article.create_date = item['create_date']
        article.url = item['url']
        article.meta.id = item['url_object_id']
        article.pertain_to = remove_tags(item['pertain_to'])
        article.content = remove_tags(item['content'])
        article.front_image_url = item['front_image_url']
        if "front_image_path" in item:
            article.front_image_path = item['front_image_path']

        article.suggest = gen_suggests(AtricleType._doc_type.index, ((article.title, 10), (article.pertain_to, 7)))  # 搜索建议补全
        article.save()

        return item
