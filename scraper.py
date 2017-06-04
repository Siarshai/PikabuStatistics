from enum import Enum
import scrapy
import pickle
from calendar import monthrange
import datetime
from scrapy.crawler import CrawlerProcess


def search_day(date):
    d0 = datetime.date(2008, 1, 1)
    delta = date - d0
    return delta.days


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)

class ParseMethod(Enum):
    GENERAL=1
    POLITICS=2

class PikabuSpider(scrapy.Spider):
    name = 'pikabuspider'

    from_year = 2017
    from_month = 1
    from_day = 1
    page_max_number = 15
    should_extract_comments_data = True
    parse_method = ParseMethod.GENERAL

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        current_time = datetime.datetime.now()
        self.from_year, self.from_month, self.from_day = PikabuSpider.from_year, PikabuSpider.from_month, PikabuSpider.from_day
        self.to_year = current_time.year
        self.to_month = current_time.month
        self.to_day = current_time.day
        self.page_max_number = PikabuSpider.page_max_number
        self.posts_data = {}
        self.full_data = {}

    def start_requests(self):
        print("Begin creating start_requests")

        if PikabuSpider.parse_method == ParseMethod.GENERAL:
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
        elif PikabuSpider.parse_method == ParseMethod.POLITICS:
            start_date = datetime.date(self.from_year, self.from_month, self.from_day)
            end_date = datetime.date(self.to_year, self.to_month, self.to_day)
            for d in daterange(start_date, end_date):
                day = search_day(d)
                for page_n in range(1, self.page_max_number + 1):
                    if page_n == 1:
                        yield scrapy.Request("http://pikabu.ru/search.php?d=" + str(day) + "&t=%D0%9F%D0%BE%D0%BB%D0%B8%D1%82%D0%B8%D0%BA%D0%B0", self.parse)
                    else:
                        yield scrapy.Request("http://pikabu.ru/search.php?d=" + str(day) + "&t=%D0%9F%D0%BE%D0%BB%D0%B8%D1%82%D0%B8%D0%BA%D0%B0&page=" + str(page_n), self.parse)


        print("Done creating start_requests")

    def _is_placeholder_story(self, story):
        if story.root.attrib['data-story-id'] == "_":
            return True
        try:
            rating = int(story.xpath('.//div[@class="story__rating-count"]/text()').extract_first().strip())
        except ValueError:
            return True
        return False

    def _parse_basic_story_data(self, story):
        id = int(story.root.attrib['data-story-id'])
        title = story.xpath('.//div[@class="story__header-title"]')[0].xpath('.//a/text()').extract_first()
        author = story.xpath('.//a[@class="story__author"]/text()').extract_first()
        rating = int(story.xpath('.//div[@class="story__rating-count"]/text()').extract_first().strip())
        comments_number = int(story.xpath('.//a[@class="story__comments-count story__to-comments"]/text()').extract_first().split()[0])
        timestamp = int(story.xpath('.//div[@class="story__date"]')[0].root.attrib["title"])
        tags = [tag.strip().lower() for tag in story.xpath('.//div[@class="story__tags"]')[0].xpath('.//a[@class="story__tag"]/text()').extract()]
        return id, {
                "title" : title,
                "rating" : rating,
                "comments_number" : comments_number,
                "tags" : tags,
                "timestamp" : timestamp,
                "author" : author,
                }

    def parse(self, response):
        if response.xpath('//div[@id="no_stories_msg"]'):
            return
        stories = response.xpath('//div[@class="story"]')
        l = len(stories)
        for i, s in enumerate(stories):
            print("Extracting story {}/{}".format(i + 1, l))
            if self._is_placeholder_story(s):
                continue
            id, story_data = self._parse_basic_story_data(s)
            story_data["link"] = response._url
            self.posts_data[id] = story_data
            if PikabuSpider.should_extract_comments_data:
                precise_post_link = s.xpath('.//div[@class="story__header-title"]')[0].xpath('.//a')[0].root.attrib["href"].strip()
                yield scrapy.Request(precise_post_link, self.parse_precise)


    def parse_precise(self, response):
        print("On precise request")
        if response.xpath('//div[@id="no_stories_msg"]'):
            return
        post_id, story_data = self._parse_basic_story_data(response.xpath('//div[@class="story"]')[0])
        number_of_received_comments = len(response.xpath('//div[@class="b-comment"]'))
        story_data["link"] = response._url
        story_data["number_of_received_comments"] = number_of_received_comments
        comments = []
        for comment in response.xpath('//div[@class="b-comment"]'):
            parent = comment.root.attrib["data-parent-id"]
            id = comment.root.attrib["id"]
            comment_body = comment.xpath('div[@class="b-comment__body "]')
            if not comment_body: continue #last comment placeholder
            comment_body = comment_body[0]
            header_section = comment_body.xpath('div[@class="b-comment__header"]')[0]
            content_section = comment_body.xpath('div[@class="b-comment__content"]')[0]
            try:
                rating = int(header_section.xpath('div[@class="b-comment__rating-count"]/text()')[0].extract())
            except IndexError:
                continue #skipping last story placeholder
            user = header_section.xpath('div[@class="b-comment__user"]')[0].xpath('a')[0].xpath('span/text()')[0].extract()
            timestamp = header_section.xpath('div[@class="b-comment__user"]')[0].xpath('time')[0].root.attrib["datetime"]
            text = content_section.root.text.strip()
            number_of_images = len(content_section.xpath('div[@class="b-p b-p_type_image"]'))
            comments.append({
                "parent" : parent,
                "id" : id,
                "content_section" : content_section,
                "rating" : rating,
                "user" : user,
                "timestamp" : timestamp,
                "text" : text,
                "number_of_images" : number_of_images,
            })
        story_data["comments"] = comments
        self.full_data[post_id] = story_data

    def closed(self, reason):
        print("Spider closed. Processing data")

        len_before = len(self.posts_data)

        # There seems to be a few strange duplicates. Let's remove them.
        keys = sorted(list(self.posts_data.keys()))
        result = {}
        for i, k in enumerate(keys):
            new_key = (self.posts_data[k]["title"], self.posts_data[k]["comments_number"], "_".join(self.posts_data[k]["tags"]))
            if new_key in result:
                result[new_key]["number"] += 1
                result[new_key]["keys"].append((k, self.posts_data[k]["rating"]))
            else:
                result[new_key] = {
                    "number" : 1,
                    "keys" : [(k, self.posts_data[k]["rating"])]
                }

        result = {key: value for key, value in result.items() if value["number"] > 1}
        for gist in result.values():
            keys = sorted(gist["keys"], key=lambda x: -x[1])
            for key in keys[1:]:
                del self.posts_data[key[0]]

        len_after = len(self.posts_data)
        print("{} duplicates removed".format(len_before - len_after))

        # Also Pikabu seems to store timestamps as Coordinated Universal Time, let's rewind them to UTC+3 (Moscow)
        for key in self.posts_data.keys():
            self.posts_data[key]["timestamp"] += 3*60*60

        print("Pickling data")

        with open("data.pkl", "wb") as handle:
            pickle.dump(self.posts_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

        if PikabuSpider.should_extract_comments_data:
            # But no need to clean full data, duplicates already got overwritten
            with open("full_data.pkl", "wb") as handle:
                pickle.dump(self.full_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

        print("DONE")


if __name__ == "__main__":

    PikabuSpider.from_year = 2017
    PikabuSpider.from_month = 1
    PikabuSpider.from_day = 1
    PikabuSpider.page_max_number = 10
    PikabuSpider.parse_method = ParseMethod.POLITICS
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    })
    process.crawl(PikabuSpider, should_extract_additional_data=True)
    process.start()
