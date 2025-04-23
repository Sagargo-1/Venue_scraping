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
            callback=self.parse_venue_h
          )

    def parse_venue_h(self):
      new_link = response.meta.get('new_link')
      id = int(response.meta.get('new_link').split('/')[6])
      api = f'https://www.wedding-spot.com/api/v1/vendors-full/{id}/'
      response = scrapy.Request(api,headers=self.headers)
      jsont = json.loads(response.body) 
      h = []
      b = jsont.get('content').get('venue_highlights')
      for i in b:
        label = i.get('label')
        h.append(label)
      highlight = ','.join(h)
      return highlight

    def parse_detailed_page(self, response): 
      loader = ItemLoader(item=VenueItem(), response=response)
      SJsonBlob = response.css('script[type="application/ld+json"]::text').get()
      jsonBlob = json.loads(SJsonBlob)
      highlights = self.parse_venue_h()
      phone = int(''.join(jsonBlob.get('telephone','').split('-')))
      capacity = int(jsonBlob.get('maximumAttendeeCapacity',''))
      address = jsonBlob.get('address')
      a = []
      a.append(address.get("streetAddress",''))
      a.append(address.get( "addressLocality",''))
      a.append(address.get("addressRegion",''))
      location = ",".join(a)

      
      loader.add_value('Url', jsonBlob.get('url'))
      loader.add_value('venue_name', jsonBlob.get('name'))
      loader.add_value('phone',phone)
      loader.add_value('highlights', highlights)
      loader.add_value('capacity', capacity)
      loader.add_css('location', location)
    
      yield loader.load_item()


if __name__ == "__main__":
  process = CrawlerProcess(get_project_settings())
  process.crawl(VenueSpider)
  process.start()
  print("Scraping completed!")