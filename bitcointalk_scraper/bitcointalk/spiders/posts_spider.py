"""Bitcointalk User Posts spider"""
import scrapy
import re
import base64
from datetime import datetime, timezone, date
from bs4 import BeautifulSoup
from scrapy.exceptions import CloseSpider


from ..items import PostItem
from ..html_parser import PostContentParser


class BitcointalkPostsSpider(scrapy.Spider):
    """Bitcointalk user posts spider"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datetime_now = datetime.utcnow()
        self.start_post_no = 0
        self.start_datetime = None
        self.base_url = None
    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
        'SPIDER_MIDDLEWARES': {
            "bitcointalk.middlewares.BitcointalkSpiderMiddleware": 543,
        }
    }
    allowed_domains = ['bitcointalk.org']
    name = 'posts'


    def start_requests(self):
        """Starts the actual scraping"""
        uid = getattr(self, "uid", None)
        start_timestamp = float(getattr(self, "start_timestamp", None))
        try:
            if uid is not None and start_timestamp is not None:
                self.start_datetime = datetime.utcfromtimestamp(start_timestamp)
                if self.datetime_now > self.start_datetime:
                    self.base_url = (
                        f"https://bitcointalk.org/index.php?action=profile;u={uid};sa=showPosts"
                    )
                    yield scrapy.Request(url=self.base_url, callback=self.parse)
                else:
                    raise CloseSpider("Start of round cannot be in the future... stopping spider.")
        except ValueError as err:
            raise CloseSpider(
                "ValueError. Timestamp may be unable to be parsed as a float.") from err
        except OverflowError as err:
            raise CloseSpider("Overflow. Timestamp out of range.") from err
        except TypeError as err:
            raise CloseSpider("Timestamp TypeError. Needs to be integer or float.") from err


    def parse(self, response):
        """Parser"""
        self.log("Scraping a page of posts...")
        # Find tables wherein are divs with class "post"
        post_tables = response.xpath(
            '//div[contains(@id, "bodyarea")]//table[./tr/td/div[contains(@class, "post")]]')
        if not post_tables:
            raise CloseSpider(
                "No posts found on page. "
                "Stopping spider incase wrong page or something else wrong.")
        for item in self.parse_post(post_tables):
            yield item
        self.start_post_no += 20
        new_url = f"{self.base_url};start={self.start_post_no}"
        yield scrapy.Request(url=new_url, callback=self.parse)


    def parse_post(self, post_tables):
        """Post parser"""
        for post_table in post_tables:
            post_item = PostItem()
            # Locate the cell in the table where datetime of the post is
            datetime_cell = post_table.xpath('./tr[1]/td[3]')
            # Locate the cell of post link
            post_link = post_table.xpath('./tr[1]/td[2]/a[last()]/@href').get()
            # combine different parts which make up the datetime and strip newlines etc.
            datetime_string = ''.join(datetime_cell.xpath('.//text()').getall()).strip()
            # Div containing actual post content
            post_div = post_table.xpath('.//div[contains(@class, "post")]').get()
            if post_link and post_div and datetime_string:
                # Regex for matching different datetimes
                today_pattern = re.compile(r"on: Today at (\d{2}:\d{2}:\d{2} (?:AM|PM))")
                other_days  = re.compile(
                    r"on: ([A-Z][a-z]{2,8} \d{2}, \d{4}, \d{2}:\d{2}:\d{2} (?:AM|PM))")
                try:
                    # If date of post other than today
                    if match := other_days.match(datetime_string):
                        post_datetime = datetime.strptime(match.group(1), "%B %d, %Y, %I:%M:%S %p")
                    # If date is today
                    elif match := today_pattern.match(datetime_string):
                        today_string = date.today().isoformat()
                        time_string = f"{today_string} {match.group(1)}"
                        post_datetime = datetime.strptime(time_string, "%Y-%m-%d %I:%M:%S %p")
                    post_datetime.replace(tzinfo=timezone.utc)
                    if post_datetime < self.start_datetime:
                        raise CloseSpider("Found a post older than start date.")
                except ValueError as err:
                    raise CloseSpider(
                        "Datetime of post could not be parsed. Stopping spider.") from err
                post_item['content'] = PostContentParser().parse_post_content(post_div)
                post_item['datetime_utc'] = post_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                post_item['link'] = post_link
                yield post_item
            else:
                raise CloseSpider(
                    "Something was wrong on the page and not all information was "
                    "successfully scraped. Stopping spider.")
