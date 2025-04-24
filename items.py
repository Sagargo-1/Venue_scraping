import scrapy

class VenueItem(scrapy.Item):
  url = scrapy.Field()
  venue_name = scrapy.Field()
  phone = scrapy.Field()
  highlights = scrapy.Field()
  capacity = scrapy.Field()
  location = scrapy.Field()
  