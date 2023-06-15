# Scrapy settings for bitcointalk project
BOT_NAME = "bitcointalk"

SPIDER_MODULES = ["bitcointalk.spiders"]
NEWSPIDER_MODULE = "bitcointalk.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
    "bitcointalk.middlewares.BitcointalkSpiderMiddleware": 543,
}
# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Only get error logs
LOG_LEVEL = 'ERROR'
