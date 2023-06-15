# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class ProfileItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    uid = scrapy.Field()
    name = scrapy.Field()
    post_count = scrapy.Field()
    activity = scrapy.Field()
    merit = scrapy.Field()
    rank = scrapy.Field()

class PostItem(scrapy.Item):
    content = scrapy.Field()
    datetime_utc = scrapy.Field()
    link = scrapy.Field()
    