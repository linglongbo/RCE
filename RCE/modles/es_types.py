from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Keyword, Text

from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

from elasticsearch_dsl.connections import connections
connections.create_connection(hosts=["192.168.1.105:9200"])


class CustomAnalyze(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}


ik_analyzer = CustomAnalyze("ik_max_word", filter=["lowercase"])  # filter:大小写


class AtricleType(DocType):
    # 移入自定义一个analyzer
    suggest = Completion(analyzer=ik_analyzer)

    title = Text(analyzer="ik_max_word")
    create_date = Date()  # 函数处理
    url = Keyword()
    url_object_id = Keyword()
    front_image_url = Keyword()
    # 为下载图片做准备
    front_image_path = Keyword()
    pertain_to = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_max_word")

    class Meta:
        index = "jobbole"
        doc_type = "article"


if __name__ == '__main__':
    AtricleType.init()
