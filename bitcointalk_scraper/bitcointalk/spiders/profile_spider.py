"""Bitcointalk user profile spider"""

import scrapy
from scrapy.exceptions import CloseSpider

from ..items import ProfileItem

class BitcointalkProfileSpider(scrapy.Spider):
    """Bitcointalk profile spider"""
    allowed_domains = ['bitcointalk.org']
    name = 'profile'
    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
    }


    def start_requests(self):
        """Start actual scraping"""
        if uid := getattr(self, 'uid', None):
            url = f"https://bitcointalk.org/index.php?action=profile;u={uid}"
            yield scrapy.Request(url=url, callback=self.parse, meta={'uid': uid})

    def parse(self, response):
        """Parse the scraped page"""
        self.log("Parsing profile...")
        profile_item = ProfileItem()
        table = response.xpath('//table[tr/td/b[contains(text(), "Name:")]]')
        errors = {"profile_errors":[]}

        name = table.xpath(
            '//tr[td/b[contains(text(), "Name:")]]/td[2]/text()').get()
        if not name:
            errors["profile_errors"].append("name not found")

        post_count = table.xpath(
            '//tr[td/b[contains(text(), "Posts:")]]/td[2]/text()').get()
        if not post_count:
            errors["profile_errors"].append("post_count not found")

        activity = table.xpath(
            '//tr[td/b[contains(text(), "Activity:")]]/td[2]/text()').get()
        if not activity:
            errors["profile_errors"].append("activity not found")

        merit = table.xpath(
            '//tr[td/b/a[contains(text(), "Merit")]]/td[2]/text()').get()
        if not merit:
            errors["profile_errors"].append("merit not found")

        rank = table.xpath(
            '//tr[td/b[contains(text(), "Position:")]]/td[2]/text()').get()
        if not rank:
            errors["profile_errors"].append("rank not found")

        if errors["profile_errors"]:
            raise CloseSpider(errors)
        profile_item["uid"] = int(response.meta.get('uid'))
        profile_item["name"] = name
        profile_item["post_count"] = int(post_count)
        profile_item["activity"] = int(activity)
        profile_item["merit"] = int(merit)
        profile_item["rank"] = rank
        yield profile_item
        