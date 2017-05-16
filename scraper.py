import scrapy
import pickle
from calendar import monthrange
import datetime
from scrapy.crawler import CrawlerProcess


raw_data = {}

class PikabuSpider(scrapy.Spider):
    name = 'pikabuspider'

    from_year = 2017
    from_month = 1
    from_day = 1
    page_max_number=15

    def __init__(self, should_extract_additional_data=False, **kwargs):
        super().__init__(**kwargs)
        current_time = datetime.datetime.now()
        self.from_year, self.from_month, self.from_day = PikabuSpider.from_year, PikabuSpider.from_month, PikabuSpider.from_day
        self.to_year = current_time.year
        self.to_month = current_time.month
        self.to_day = current_time.day
        self.page_max_number = PikabuSpider.page_max_number

    def start_requests(self):
        print("Begin creating start_requests")

        from_month = self.from_month
        from_day = self.from_day
        for year_number in range(self.from_year, self.to_year+1):
            to_month = self.to_month if year_number == self.to_year else 12
            for month_number in range(from_month, to_month+1):
                max_day = monthrange(year_number, month_number)[1]
                to_day = self.to_day if year_number == self.to_year and month_number == self.to_month else max_day
                for day_number in range(from_day, to_day+1):
                    date_str = "{0:02d}-{1:02d}-{2:04d}".format(day_number, month_number, year_number)
                    print("Day " + date_str)
                    for page_number in range(1, self.page_max_number + 1):
                        print("Page {}".format(page_number))
                        yield scrapy.Request('http://pikabu.ru/best/' + date_str + "?page=" + str(page_number), self.parse)
                from_day = 1
            from_month = 1

        print("Done creating start_requests")

    def parse(self, response):
        stories = response.xpath('//div[@class="story"]')
        l = len(stories)
        for i, s in enumerate(stories):
            print("Extracting story {}/{}".format(i + 1, l))
            id = s.root.attrib['data-story-id']
            if id == "_":
                continue #skipping last story placeholder
            id = int(id)
            title = s.xpath('.//div[@class="story__header-title"]')[0].xpath('.//a/text()').extract_first()
            rating = int(s.xpath('.//div[@class="story__rating-count"]/text()').extract_first().strip())
            comments_number = s.xpath('.//a[@class="story__comments-count story__to-comments"]/text()').extract_first()
            comments_number = int(comments_number.split()[0])
            timestamp = int(s.xpath('.//div[@class="story__date"]')[0].root.attrib["title"])
            tags = [tag.strip().lower() for tag in s.xpath('.//div[@class="story__tags"]')[0].xpath('.//a[@class="story__tag"]/text()').extract()]
            raw_data[id] = {
                "title" : title,
                "rating" : rating,
                "comments_number" : comments_number,
                "tags" : tags,
                "timestamp" : timestamp,
                }

    def closed(self, reason):
        print("Spider closed. Processing data")

        len_before = len(raw_data)

        # There seems to be a few strange duplicates. Let's remove them.
        keys = sorted(list(raw_data.keys()))
        result = {}
        for i, k in enumerate(keys):
            new_key = (raw_data[k]["title"], raw_data[k]["comments_number"], "_".join(raw_data[k]["tags"]))
            if new_key in result:
                result[new_key]["number"] += 1
                result[new_key]["keys"].append((k, raw_data[k]["rating"]))
            else:
                result[new_key] = {
                    "number" : 1,
                    "keys" : [(k, raw_data[k]["rating"])]
                }

        result = {key: value for key, value in result.items() if value["number"] > 1}
        for gist in result.values():
            keys = sorted(gist["keys"], key=lambda x: -x[1])
            for key in keys[1:]:
                del raw_data[key[0]]

        len_after = len(raw_data)
        print("{} duplicates removed".format(len_before - len_after))

        # Also Pikabu seems to store timestamps as Coordinated Universal Time, let's rewind them to UTC+3 (Moscow)
        for key in raw_data.keys():
            raw_data[key]["timestamp"] += 3*60*60

        print("Pickling data")

        with open("data.pkl", "wb") as handle:
            pickle.dump(raw_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

        print("DONE")


if __name__ == "__main__":

    PikabuSpider.from_year = 2014
    PikabuSpider.from_month = 1
    PikabuSpider.from_day = 1
    PikabuSpider.page_max_number = 15
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    })
    process.crawl(PikabuSpider, should_extract_additional_data=True)
    process.start()
