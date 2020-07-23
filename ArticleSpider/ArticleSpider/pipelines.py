# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json

from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

class ArticlespiderPipeline:
    def process_item(self, item, spider):
        return item

# 使用自定义的方法将item保存到json文件
class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('article.json', 'a', encoding='utf-8')

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + '\n'
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()

# 使用built in item exporter方法保存到json文件
class JsonExporterPipeline(object):
    def __init__(self):
        self.file = open('article_spider.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

# 自定义image pipeline继承ImagesPipeline，更新image在本地的存储路径
class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        global image_file_path
        if 'front_image_url' in item:
            for ok, val in results:
                image_file_path = val['path']
            item['front_image_path'] = image_file_path

        return item
