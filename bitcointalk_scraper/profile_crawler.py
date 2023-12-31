if __name__ == '__main__':
    import os
    import argparse
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('uid', help='the bitcointalk profile uid')
    ns = arg_parser.parse_args()

    os.environ['SCRAPY_SETTINGS_MODULE'] =  'settings'
    s = get_project_settings()
    s['FEEDS'] = {
        "scraper_outputs/profile.json": {
            "format": "json",
            "overwrite": True,
        }
    }
    process = CrawlerProcess(s)

    process.crawl('profile', uid=ns.uid)
    process.start()
    