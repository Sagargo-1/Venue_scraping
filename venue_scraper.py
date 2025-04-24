import scrapy
import json
from scrapy.loader import ItemLoader
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from items import VenueItem

class VenueSpider(scrapy.Spider):
    name = 'venspy'
    headers = {
        'user-agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Accept': 'application/json'
    }

    custom_settings = {
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 1,
        'FEED_URI': 'output.csv',
        'FEED_FORMAT': 'csv',
        'FEED_HEADERS': {'URL', 'Venue name', 'Phone', 'Venue highlights', 'Guest capacity', 'Address'}
    }

    def start_requests(self):
        urls = [
            'https://www.wedding-spot.com/wedding-venues/?page=1&pr=new%20jersey&r=new%20jersey%3anorth%20jersey&r=new%20jersey%3aatlantic%20city&r=new%20jersey%3ajersey%20shore&r=new%20jersey%3asouth%20jersey&r=new%20jersey%3acentral%20jersey&r=new%20york%3along%20island&r=new%20york%3amanhattan&r=new%20york%3abrooklyn&r=pennsylvania%3aphiladelphia&sr=1'
        ]
        for url in urls:
            yield scrapy.Request(
                url,
                headers=self.headers,
                meta={'current_page': 1},
                callback=self.parse
            )

    def parse(self, response):
        venue_links = response.xpath('//div[@class="venueCard--wrapper"]/a/@href').getall()
        for link in venue_links[:36]:
            detail_url = response.urljoin(link)
            yield scrapy.Request(
                detail_url,
                headers=self.headers,
                meta=response.meta,
                callback=self.parse_detailed_page
            )

    def parse_detailed_page(self, response):
        loader = ItemLoader(item=VenueItem(), response=response)
        json_ld = response.css('script[type="application/ld+json"]::text').get()
        json_data = json.loads(json_ld) if json_ld else {}

        try:
            highlights = ",".join(response.xpath('//div[@class="VenueHighlights--label"]/text()').getall()[:3])
        except Exception as e:
            self.logger.error(f"Error extracting highlights: {e}")
            highlights = "N/A"

        try:
            numeric_phone = ''.join(response.xpath('//span[@class="SecondaryCTA--hidden"]/text()').get().split("-"))
            if 'ext' in numeric_phone:
                phone = numeric_phone.split('ext')
                numeric_phone = phone[0]
        except Exception as e:
            self.logger.error(f"Error extracting phone: {e}")
            numeric_phone = "N/A"

        try:
            capacity = response.xpath('//p[contains(text(),"Accommodates")]/text()').get().split()[3].replace('[','').replace(']','')
        except Exception as e:
            self.logger.error(f"Error extracting capacity: {e}")
            capacity = "N/A"

        try:
            location = response.xpath('//h3[contains(text(),"Location")]/following-sibling::p[@class="VenuePage--detail-description"]/text()').get() + ',' + response.xpath('//h3[contains(text(),"Location")]/following-sibling::p[@class="VenuePage--detail-description"]/span/text()').get()
        except Exception as e:
            self.logger.error(f"Error extracting location: {e}")
            location = "N/A"

        loader.add_value('url', json_data.get('url', response.url))
        loader.add_value('venue_name', response.xpath('//div[@class="SecondaryCTA--venueName"]/text()').get())
        loader.add_value('phone', int(numeric_phone.replace('[','').replace(']','')))
        loader.add_value('highlights', highlights)
        loader.add_value('capacity', int(capacity))
        loader.add_value('location', location)

        yield loader.load_item()

        # Handle Pagination
        try:
            current_page = response.meta.get('current_page',1)
            current_page += 1
            if current_page <= 20 and not None:
                next_page_url = f'https://www.wedding-spot.com/wedding-venues/new-jersey/?page={str(current_page)}&pr=new%20jersey&r=new%20jersey%3anorth%20jersey&r=new%20jersey%3aatlantic%20city&r=new%20jersey%3ajersey%20shore&r=new%20jersey%3asouth%20jersey&r=new%20jersey%3acentral%20jersey&r=new%20york%3along%20island&r=new%20york%3amanhattan&r=new%20york%3abrooklyn&r=pennsylvania%3aphiladelphia&sr=1'
                yield scrapy.Request(next_page_url, meta={'current_page':current_page}, headers=self.headers, callback=self.parse)
        except Exception as e:
            self.logger.error(f"Error in pagination: {e}")

if __name__ == "__main__":
    process = CrawlerProcess(get_project_settings())
    process.crawl(VenueSpider)
    process.start()
    print("Scraping completed!")