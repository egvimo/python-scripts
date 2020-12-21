import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from urllib.parse import urljoin
from functools import partial
from pathlib import Path


class EnnyMoSpider(scrapy.Spider):
    name = "enny_mo"

    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) '
                       'Gecko/20100101 Firefox/77.0')
    }

    def start_requests(self):
        urls = [
            ('https://www.baby-und-familie.de/'
             '--allgemein/Hoergeschichten-zum-Download-542125_2.html')
        ]
        for url in urls:
            yield scrapy.Request(url=url, headers=self.headers,
                                 callback=self.parse)

    def parse(self, response):
        result = response.css('#maincontent .box-free-download__text')

        for item in result:
            text = item.css('a::text').get()
            href = item.css('a').attrib['href']
            name = text.replace('Teil ', '').replace(
                '?', '').replace(':', ' -') + '.mp3'
            url = urljoin(response.url, href)

            yield scrapy.Request(url=url, headers=self.headers,
                                 callback=partial(self.download_file,
                                                  name=name))

    def download_file(self, response, name):
        self.log('Saving {} as {}'.format(response.url, name))
        Path('out/').mkdir(parents=True, exist_ok=True)
        with open('out/' + name, 'wb') as f:
            f.write(response.body)


process = CrawlerProcess(get_project_settings())

process.crawl(EnnyMoSpider)
process.start()
