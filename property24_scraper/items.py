import scrapy


class VacantPlotItem(scrapy.Item):
    """All fields extracted from a Property24 vacant land / plot listing."""

    listing_url       = scrapy.Field()
    listing_no        = scrapy.Field()
    title             = scrapy.Field()
    price             = scrapy.Field()
    location          = scrapy.Field()
    street_address    = scrapy.Field()
    erf_size          = scrapy.Field()
    description       = scrapy.Field()

    # bonus fields grabbed for free while we're there
    property_type     = scrapy.Field()
    list_date         = scrapy.Field()
    scraped_at        = scrapy.Field()
