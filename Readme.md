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
from items import VenueItem

class VenueSpider(scrapy.Spider):
    """Scrapes wedding venue details from target website"""

    name = 'venspy'
    allowed_domains = ['wedding-spot.com']

    # Throttling and output configuration
    custom_settings = {
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,  # Polite crawling
        'DOWNLOAD_DELAY': 1,                 # 1s between requests
        'FEED_FORMAT': 'csv',                # Output format
        'FEED_URI': 'output/venues.csv'      # Output location
    }

    def start_requests(self):
        """Initial request with pagination tracking"""
        yield scrapy.Request(
            url='https://www.wedding-spot.com/wedding-venues/?page=1',
            callback=self.parse,
            meta={'current_page': 1}  # Track pagination state
        )

    def parse(self, response):
        """Handle pagination and venue listing"""
        current_page = response.meta['current_page']

        # Extract and follow venue detail links
        venue_links = response.xpath('//div[@class="venueCard--wrapper"]/a/@href').getall()
        for link in venue_links[:36]:  # Limit to first 36 venues
            yield response.follow(
                link,
                callback=self.parse_detailed_page,
                meta={'current_page': current_page}
            )

        # Pagination control
        if current_page < 20:
            next_page = current_page + 1
            next_url = f'https://www.wedding-spot.com/wedding-venues/?page={next_page}'
            yield scrapy.Request(
                next_url,
                callback=self.parse,
                meta={'current_page': next_page}
            )

    def parse_detailed_page(self, response):
        """Extract structured data from venue detail pages"""
        loader = ItemLoader(item=VenueItem(), response=response)

        # JSON-LD data extraction
        json_ld = response.css('script[type="application/ld+json"]::text').get()
        if json_ld:
            try:
                structured_data = json.loads(json_ld)
                loader.add_value('url', structured_data.get('url', response.url))
            except json.JSONDecodeError:
                self.logger.warning('Failed to parse structured data')

        # Phone number cleaning pipeline
        phone_raw = response.xpath('//span[@class="SecondaryCTA--hidden"]/text()').get()
        if phone_raw:
            phone_clean = ''.join(filter(str.isdigit, phone_raw.split('ext')[0]))
            loader.add_value('phone', int(phone_clean))

        # Add other field extractions...

        yield loader.load_item()
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

