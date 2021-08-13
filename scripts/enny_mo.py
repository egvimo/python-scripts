#!/usr/bin/env python3

import re
from urllib.parse import urljoin
from functools import partial
from pathlib import Path
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


class EnnyMoSpider(scrapy.Spider):
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) '
                       'Gecko/20100101 Firefox/77.0')
    }

    def __init__(self, name="enny_mo", **kwargs):
        super().__init__(name=name, **kwargs)
        self.episode_boundary = kwargs.get('episode_boundary')

    def start_requests(self):
        urls = [
            'https://www.baby-und-familie.de/--allgemein/Enny-und-Mo--Staffel-1-542125_3.html',
            'https://www.baby-und-familie.de/--allgemein/Enny-und-Mo--Staffel-2-542125_4.html',
            'https://www.baby-und-familie.de/--allgemein/Enny-und-Mo--Staffel-3-542125_5.html',
            'https://www.baby-und-familie.de/--allgemein/Hoergeschichten-zum-Download-542125_2.html'
        ]
        for url in urls:
            yield scrapy.Request(url=url, headers=self.headers,
                                 callback=self.parse)

    def parse(self, response, **kwargs):
        result = response.css('#maincontent .box-free-download__text')

        for item in result:
            text = item.css('a::text').get()
            href = item.css('a').attrib['href']
            name = text.replace('Teil ', '').replace(
                '?', '').replace(':', ' -') + '.mp3'
            url = urljoin(response.url, href)

            if self.crawl_episode(name):
                yield scrapy.Request(url=url, headers=self.headers,
                                     callback=partial(self.download_file,
                                                      name=name))

    def crawl_episode(self, episode):
        if self.episode_boundary is None:
            return True

        episode_number = re.search(r"^\d+", episode)
        return self.episode_boundary <= int(episode_number.group())

    def download_file(self, response, name):
        self.log('Saving {} as {}'.format(response.url, name))
        Path('out/').mkdir(parents=True, exist_ok=True)
        with open('out/' + name, 'wb') as file:
            file.write(response.body)


def start_crawler(episode_boundary=None):
    process = CrawlerProcess(get_project_settings())

    process.crawl(EnnyMoSpider, episode_boundary=episode_boundary)
    process.start()


if __name__ == '__main__':
    start_crawler()
