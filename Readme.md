# 🕷️ Wedding Venue Scraper Documentation 

**Compatibility Section :**  
<div style="display: flex; gap: 40px; align-items: center; padding: 20px; background: #f8f9fa; border-radius: 8px; flex-wrap: wrap;">
  <div style="text-align: center;">
    <img src="https://www.python.org/static/img/python-logo.png" width="120">
    <div style="margin-top: 10px; font-family: 'Segoe UI', sans-serif; font-size: 1rem; color: #306998; font-weight: 600;">
      <code>Python 3.8+</code>
    </div>
  </div>
    <br>   
  <div style="text-align: center;">
    <img src="https://scrapy.org/img/scrapylogo.png" width="120">
    <div style="margin-top: 10px; font-family: 'Segoe UI', sans-serif; font-size: 1rem; color: #2C504E; font-weight: 600;">
      <code>Scrapy Framework latest Version</code>
    </div>
  </div>
</div>

## 🚀 Quick Start

### Clone, Install & Run the Spider
```bash
git clone https://github.com/Sagargo-1/Venue_scraping.git
```
```bash
pip install scrapy
```
```bash
scrapy runspider venue_scraper.py
```
---
## 📂 Project Structure
```
└── 📁 venv
└── items.py
└── venue_scraper.py
└── output.csv
└── README.md
```
---

## 🧩 Core Component

<p style="font-size: 0.9em; color: #666;">
By inheriting <code>scrapy.Item</code>, we define structured data containers for scraped information. 
This approach enables automatic field validation and ensures consistent data formatting throughout the scraping pipeline.
</p>

## Item.py
```python
import scrapy

class VenueItem(scrapy.Item):
    ''' Data schema for venue information '''
    
    url = scrapy.Field()          
    venue_name = scrapy.Field()   
    phone = scrapy.Field()        
    highlights = scrapy.Field()  
    capacity = scrapy.Field()     
    location = scrapy.Field()    
```
## venue_scraper.py
<p style="font-size: 0.9em; color: #666;">
The spider inherits from <code>scrapy.Spider</code> to implement website crawling logic, handling pagination, request throttling, and structured data extraction using our custom <code>VenueItem</code>.
</p>

```python
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
```
---

# 📊 Sample Output
<div style="overflow-x: auto; margin: 20px 0;">

| Capacity | Highlights                          | Location                          | Phone          | URL                                                                 | Venue Name                     |
|----------|-------------------------------------|-----------------------------------|----------------|---------------------------------------------------------------------|--------------------------------|
| 95       | BYO, Valet parking, BYO            | 6109 Atlantic Avenue, Wildwood, NJ 08260 | (609) 522-1177 | [Cape Cod Inn Motel](https://www.wedding-spot.com/venue/12608/)    | Cape Cod Inn Motel            |
| 1000     | 4x award winner, Indoor/outdoor spaces | 555 Northern Blvd, Great Neck, NY 11021 | (516) 487-7900 | [Leonard's Palazzo](https://www.wedding-spot.com/venue/1400/)      | Leonard's Palazzo             |
</div>


# 🕸️ Troubleshooting
<p style="font-size: 2em; color: #666;">If you are hitting any Error . try these command in your 
<code>cmd</code> or <code>bash</code> to troubleshoot it.</p>

```bash
# Debug mode
scrapy runspider venue_scraper.py --loglevel=DEBUG

# Disable cache
scrapy runspider venue_scraper.py -s HTTPCACHE_ENABLED=0
```
 
# 🎉 Conclusion

**Wedding Venue Scraper** offers a production-ready solution for efficiently harvesting structured venue data while maintaining web-crawling best practices. With its modular architecture and built-in throttling mechanisms, the spider balances performance with website respect through:

- **Compliance-first design**: 1-second delay between requests + concurrent request limits  
- **Data quality**: Field validation, phone normalization, and JSON-LD parsing  
- **Scalability**: Pagination handling for 20+ pages and dynamic content extraction
- **Free Of Cost**: No extra charges of Proxies and different Paid Tools 

The included `output.csv` schema provides immediate business value for:  
✅ Market analysis  ✅ Capacity planning  ✅ Vendor comparison  ✅ Lead generation 

# 🛡️ Pro-tip :

- **Page Source**: Always inspect element from page source by clicking `Ctrl + U` and locate or search for specific item by clicking `Ctrl + F` because sometime the selector in inspect or Devtools is different than page Source and your code will not work because of wrong selector and the selector from page source or html is legit and workable 
- **Selector gadget**: Use selector gadget chrome extension for inspecting css selector easily and fastly
- **Debug by html**: Use below code to genrate html code and locate your desired item in that html file and check your selector
is legit or not 
```python
with open('response.html','w') as f:
    f.write(response.body)
    f.close()
```    

