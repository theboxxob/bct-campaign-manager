from bs4 import BeautifulSoup
from bs4 import NavigableString
from datetime import datetime,date
from scrapy.exceptions import CloseSpider

import re


def is_quoteheader(node):
    """Check if node has class quoteheader"""
    if class_dict := node.get('class'):
        return "quoteheader" in class_dict
    return False

def is_quotediv(node):
    """Check if node has class quote"""
    if class_dict := node.get('class'):
        return "quote" in class_dict
    return False


class PostContentParser:
    """Parse post content using BeautifulSoup instead of Scrapy"""
    def parse_post_content(self, html_string):
        """Parse content of HTML string with post div"""
        soup = BeautifulSoup(html_string, 'lxml').div
        return self.process_post(soup)


    def process_post(self, post_div):
        """Process post div element"""
        post = dict()
        self.process_children(post_div, post)
        return post


    def process_children(self, node, parent):
        """Process post div child elements"""
        if 'children' not in parent:
            parent['children'] = []
        for child in node.children:
            if processed_child := self.process_child(child):
                if error := processed_child.get('error'):
                    if 'errors' not in parent:
                        parent['errors'] = []
                    parent['errors'].append(error)
                parent['children'].append(processed_child)
        return parent


    def process_child(self, node):
        """Process a child element"""
        if isinstance(node, NavigableString):
            return {
                'type': 'text',
                'content': str(node)
            }
        if is_quoteheader(node):
            return self.process_quote(node)
        if node.name == 'br':
            return {
                'type': 'text',
                'content': '\n\n'
            }
        if node.name == 'a':
            return {
                'type': 'link',
                'url': node.get('href')
            }
        if node.name == 'img':
            return {
                'type': 'image',
                'src': node.get('src')
            }
        return None


    def process_quote(self, quote_header):
        """Process a quote node"""
        header = ' '.join(quote_header.stripped_strings)
        quote_div = quote_header.next_sibling
        quote = {
            'type': 'quote',
        }
        if quote_div and is_quotediv(quote_div):
            if (a := quote_header.a) and (link := a.get('href')):
                quote['url'] = link
                header_today_pattern = re.compile(
                    r"Quote from: (?P<username>[\w ]{,25}) on Today at "
                    r"(?P<time>\d{2}:\d{2}:\d{2} (?:AM|PM))")
                header_regular_pattern = re.compile(
                    r"Quote from: (?P<username>[\w ]{,25}) on "
                    r"(?P<datetime>[A-Z][a-z]{2,8} \d{2}, \d{4}, \d{2}:\d{2}:\d{2} (?:AM|PM))")
                if match := header_regular_pattern.match(header):
                    match_dict = match.groupdict()
                    post_datetime = datetime.strptime(
                        match_dict.get('datetime'), "%B %d, %Y, %I:%M:%S %p")
                    quote['datetime_utc'] = post_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                    quote['username'] = match_dict.get('username')
                elif match := header_today_pattern.match(header):
                    match_dict = match.groupdict()
                    today_string = date.today().isoformat()
                    time_string = f"{today_string} {match_dict.get('time')}"
                    post_datetime = datetime.strptime(time_string, "%Y-%m-%d %I:%M:%S %p")
                    quote['datetime_utc'] = post_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                    quote['username'] = match_dict.get('username')
                else:
                    quote['header'] = header
            return self.process_children(quote_div, quote)
        quote['error'] = "Quote header not followed by a quote"
        quote['header'] = header
        return quote
