import scrapy
from scrapy.selector import Selector
from scrapy.loader import ItemLoader 
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from items import VenueItem
import json

class VenueSpider(scrapy.Spider):
    name = 'venspy'
    headers = {
        'user-agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    }

    custom_settings = {
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 1,
        'FEED_URI': 'output.json',
        'FEED_FORMAT': 'json',
        # 'FEED_EXPORT_FIELDS': ['']
    } 

    def start_requests(self):  # Corrected method name
      urls = [
        'https://www.wedding-spot.com/wedding-venues/?page=1&pr=new%20jersey&r=new%20jersey%3anorth%20jersey&r=new%20jersey%3aatlantic%20city&r=new%20jersey%3ajersey%20shore&r=new%20jersey%3asouth%20jersey&r=new%20jersey%3acentral%20jersey&r=new%20york%3along%20island&r=new%20york%3amanhattan&r=new%20york%3abrooklyn&r=pennsylvania%3aphiladelphia&sr=1'
      ]
      for url in urls:
        yield scrapy.Request(
          url,
          headers=self.headers,
          meta = {'current_page':1,'base_url':url},
          callback=self.parse
        )

    def parse(self,response):
      each_detailed_page_link = response.xpath('//div[@class="venueCard--wrapper"]/a')
      new_each_detailed_page_link = each_detailed_page_link[:36].copy()
      for link in new_each_detailed_page_link:
        new_link = 'https://www.wedding-spot.com' + link.xpath('@href').get()  

        if new_link:
          yield scrapy.Request(
            new_link,
            headers=self.headers,
            meta = {
    'current_page': response.meta.get('current_page'),
    'base_url': response.meta.get('base_url'),
    'new_link': new_link },
            callback=self.parse_detailed_page
          )

    # def parse_venue_h(self, response):
    #   new_link = response.meta.get('new_link')
    #   id = int(response.meta.get('new_link').split('/')[6])
    #   api = f'https://www.wedding-spot.com/api/v1/vendors-full/{id}/'
    #   response = scrapy.Request(api,headers=self.headers)
    #   jsont = json.loads(response.body) 
    #   h = []
    #   b = jsont.get('content').get('venue_highlights')
    #   for i in b:
    #     label = i.get('label')
    #     h.append(label)
    #   highlight = ','.join(h)
    #   return highlight

    def parse_detailed_page(self, response): 
      loader = ItemLoader(item=VenueItem(), response=response)
      SJsonBlob = response.css('script[type="application/ld+json"]::text').get()
      jsonBlob = json.loads(SJsonBlob)
      # highlights = self.parse_venue_h()
      phone = jsonBlob.get('telephone', '')
      numeric_phone = ''.join(filter(str.isdigit, phone.split(' ')[0])) if phone else 'nan'

      capacity = jsonBlob.get('maximumAttendeeCapacity', 'nan')
      address = jsonBlob.get('address', {})
      a = [
          address.get("streetAddress", ''),
          address.get("addressLocality", ''),
          address.get("addressRegion", '')
      ]
      location = ",".join([e for e in a if e])


      loader.add_value('Url', jsonBlob.get('url'))
      loader.add_value('venue_name', jsonBlob.get('name'))
      loader.add_value('phone', numeric_phone)
      loader.add_value('highlights', 'nan')
      loader.add_value('capacity', capacity)
      loader.add_value('location', location)

      yield loader.load_item()


if __name__ == "__main__":
  process = CrawlerProcess(get_project_settings())
  process.crawl(VenueSpider)
  process.start()
  print("Scraping completed!")