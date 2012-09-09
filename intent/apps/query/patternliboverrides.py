__author__ = 'browsepad'

from pattern.web import *


#--- PATTERN CLIPS LIB TWITTER CLASS OVERRIDE -------------------------------------------------------------------------

class TwitterEx(SearchEngine):

    def __init__(self, license=None, throttle=0.5, language=None):
        SearchEngine.__init__(self, license or TWITTER_LICENSE, throttle, language)

    def search(self, query, type=SEARCH, start=1, count=10, sort=RELEVANCY, size=None, cached=False, **kwargs):
        """ Returns a list of results from Twitter for the given query.
            - type : SEARCH or TRENDS,
            - start: maximum 1500 results (10 for trends) => start 1-15 with count=100, 1500/count,
            - count: maximum 100, or 10 for trends.
            There is an hourly limit of 150+ queries (actual amount undisclosed).
        """
        if type != SEARCH:
            raise SearchEngineTypeError
        if not query or count < 1 or start < 1 or start > 1500/count:
            return Results(TWITTER, query, type)
            # 1) Construct request URL.
        url = URL(TWITTER + "search.json?", method=GET)
        url.query = {
            "q": query,
            "page": start,
            "rpp": min(count, 100)
        }
        if "geo" in kwargs:
            # Filter by location with geo=(latitude, longitude, radius).
            # It can also be a (latitude, longitude)-tuple with default radius "10km".
            url.query["geocode"] = ",".join((map(str, kwargs.pop("geo")) + ["10km"])[:3])
            # 2) Restrict language.
        url.query["lang"] = self.language or ""
        # 3) Parse JSON response.
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        try:
            data = URL(url).download(cached=cached, **kwargs)
        except HTTP420Error:
            raise SearchEngineLimitError
        try:
            data = json.loads(data)
        except:
            raise Exception('Twitter api returned unexpected result')
        results = Results(TWITTER, query, type)
        results.total = None
        for x in data.get("results", data.get("trends", [])):
            r = Result(url=None)
            try:
                r.url         = self.format(TWITTER_SOURCE.search(x.get("source", "href=&quot;&quot;")).group(1))
            except Exception, e:
                r.url = ''
            r.description       = self.format(x.get("text"))
            r.date              = self.format(x.get("created_at", data.get("as_of")))
            r.author            = self.format(x.get("from_user"))
            r.author_user_id    = self.format(x.get("from_user_id"))
            r.profile           = self.format(x.get("profile_image_url")) # Profile picture URL.
            r.language          = self.format(x.get("iso_language_code"))
            r.tweet_id          = self.format(x.get("id"))
            r.author_user_name  = self.format(x.get("from_user_name"))
            results.append(r)
        return results

    def trends(self, **kwargs):
        """ Returns a list with 10 trending topics on Twitter.
        """
        url = URL("https://api.twitter.com/1/trends/1.json")
        kwargs.setdefault("cached", False)
        kwargs.setdefault("unicode", True)
        kwargs.setdefault("throttle", self.throttle)
        data = url.download(**kwargs)
        data = json.loads(data)
        return [u(x.get("name")) for x in data[0].get("trends", [])]