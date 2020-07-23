from urllib import parse
import re
import json

import scrapy
from scrapy import Request  # 异步io框架，没有多线程，类似nodejs

from ArticleSpider.items import JobBoleArticleItem
from ArticleSpider.utils import common

class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['news.cnblogs.com']
    start_urls = ['http://news.cnblogs.com/']

    # xpath: /html/body/div[2]/div[4]/div[1]/div[2]/h2/a/@href
    #        //*[@id="entry_667673"]/div[2]/h2/a/@href
    #        //div[@id="news_list"]//h2[@class="news_entry"]/a/@href
    # urls = response.xpath('//*[@id="entry_667673"]/div[2]/h2/a/@href').extract_first("")
    # urls = response.css('div#news_list h2.news_entry a::attr(href)').extract()
    # urls = response.xpath('//div[@id="news_list"]//h2[@class="news_entry"]/a/@href').extract()

    """
    1 根据给定的url，scrapy自动下载首页，使用parse获取首页中的标题urls list
    2 scrapy根据urls list中的每个url下载新闻详情页，然后使用parse_detail对其进行解析
    3 使用解析后的数据初始化item，将item通过pipeline存储到文件或者数据库
    4 获取新闻列表下一页的url，再次执行step 1
    """
    def parse(self, response):
        post_nodes = response.css('#news_list .news_block')[:2]
        for post_node in post_nodes:
            image_url = 'https:' + post_node.css('.entry_summary a img::attr(src)').extract_first("")
            post_url = post_node.css('h2 a::attr(href)').extract_first("")
            # 下载新闻详情页进行异步解析
            yield Request(url=parse.urljoin(response.url, post_url),
                          meta={"front_image_url": image_url}, callback=self.parse_detail)

        # 访问下一页，获取urls list交给scrapy下载
        # next_url = response.xpath('//a[contains(text(), "Next >")]/@href').extract_first("")
        # yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

        # next_url = response.css('div.pager a:last-child::text').extract_first("")
        # if next_url == "Next >":
        #     next_url = response.css('div.pager a:last-child::attr(href)').extract_first("")
        #     yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    # 解析新闻详情页
    def parse_detail(self, response):
        match_re = re.match('.*?(\d+)', response.url)
        print(match_re)
        if match_re:
            post_id = match_re.group(1)
            article_item = JobBoleArticleItem()

            title = response.css('#news_title a::text').extract_first("")
            # title = response.xpath('//*[@id="news_title"]//a/text()').extract_first("")

            create_date = response.css('#news_info .time::text').extract_first("")
            # create_date = response.xpath('//*[@id="news_info"]//*[@class="time"]/text()')

            match_re = re.match('.*?(\d+.*)', create_date)
            if match_re:
                create_date = match_re.group(1)
            content = response.css('#news_content').extract()[0]
            # content = response.xpath('//*[@id="news_content"]').extract()[0]

            tag_list = response.css('.news_tags a::text').extract()
            # tag_list = response.xpath('//*[@class="news_tags"]//a/text()').extract()
            tags = ",".join(tag_list)

            article_item['title'] = title
            article_item['create_date'] = create_date
            article_item['content'] = content
            article_item['tags'] = tags
            article_item['url'] = response.url

            if response.meta.get('front_image_url', ''):
                article_item['front_image_url'] = [response.meta.get('front_image_url', '')]
            else:
                article_item['front_image_url'] = []

            yield Request(url=parse.urljoin(response.url, '/NewsAjax/GetAjaxNewsInfo?contentId={}'.format(post_id)),
                          meta={'article_item': article_item}, callback=self.parse_nums)

    def parse_nums(self, response):
        j_data = json.loads(response.text)
        article_item = response.meta.get('article_item', '')

        praise_nums = j_data['DiggCount']
        view_nums = j_data['TotalView']
        comment_nums = j_data['CommentCount']

        article_item['praise_nums'] = praise_nums
        article_item['view_nums'] = view_nums
        article_item['comment_nums'] = comment_nums
        article_item['url_object_id'] = common.get_md5(article_item['url'])
        yield article_item





