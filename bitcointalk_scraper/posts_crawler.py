if __name__ == '__main__':
    import os
    import argparse
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('uid', type=int, help='the bitcointalk profile uid')
    arg_parser.add_argument('start_timestamp', type=int, help=
        'the start timestamp of round (seconds from epoch)')
    ns = arg_parser.parse_args()

    os.environ['SCRAPY_SETTINGS_MODULE'] =  'settings'
    s = get_project_settings()
    s['FEEDS'] = {
        "scraper_outputs/posts.json": {
            "format": "json",
            "overwrite": True,
        }
    }
    process = CrawlerProcess(s)

    process.crawl('posts', uid=ns.uid, start_timestamp=ns.start_timestamp)
    process.start()
    