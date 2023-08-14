#!/usr/bin/env python3
""" FAQ scraper for faceswap Discord bot """

import logging
import urllib.request

from threading import Thread, Lock, Event
from time import sleep

import lxml.html as LH

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class FAQs():
    """ Scrapes the FAQ section every given hours and stores data in dictionaries """
    def __init__(self, scrape_interval=24):
        self.url = "https://faceswap.dev/forum/app.php/faqpage"
        self.loaded = Event()
        self.refresh = Event()
        self.interval = scrape_interval * 86400
        self.lock = Lock()
        self._contents = {}
        self._search_dict = {}
        thread = Thread(target=self.get_faqs, daemon=True, args=(self.loaded, self.refresh))
        thread.start()

    @property
    def contents(self):
        """ Return contents dict, locked """
        with self.lock:
            return self._contents

    @property
    def search_dict(self):
        """ Return search dict, locked """
        with self.lock:
            return self._search_dict

    def get_faqs(self, loaded_event, refresh_event):
        """ Gets the faq web contents and parses it into the dictionaries
            runs in a background thread and runs automatically every self.interval seconds
        """
        while True:
            html = self.scrape_website()
            doc = LH.fromstring(html)
            self.set_contents(doc)
            self.set_search_dict(doc)
            refresh_event.clear()
            loaded_event.set()
            for _ in range(self.interval):
                if refresh_event.is_set():
                    break
                sleep(60)

    def scrape_website(self):
        """ Scrape the website for latest faqs """
        logger.info("Getting HTML")
        with urllib.request.urlopen(self.url) as rsp:
            response = rsp.read()
        logger.info("Returned HTML")
        return response

    def set_contents(self, doc):
        """ Parse the contents section to get the links to the
            first item in each section """
        contents = {}
        index = [item for item in doc.xpath("//dl[@class='faq']") if not item[0].items()]
        for item in index:
            children = item.getchildren()
            heading = children[0].text_content().replace("\t",
                                                         "").lower().replace("ation",
                                                                             "").replace("ing", "")
            link = list(children[1].iterlinks())[0][2]
            contents[heading] = link
        with self.lock:
            self._contents = contents
        logger.info("Set contents: %s", self.contents)

    def set_search_dict(self, doc):
        """ Parse the FAQS section to build a search dict """
        search_dict = {}
        faqs = [item for item in doc.xpath("//dl[@class='faq']") if item[0].items()]
        for item in faqs:
            tag = f"#{item[0].items()[0][1]}"
            faq = [child.text_content().replace("\t", "") for child in item.getchildren()]
            search_dict[tag] = faq
        with self.lock:
            self._search_dict = search_dict
        logger.info("Set search_dict")

    def search(self, search_term):
        """ Search the search dict for a term and return the tag with the question """
        search_term = search_term.lower()
        results = {}
        for key, val in self.search_dict.items():
            search_text = " ".join(val).lower()
            if search_text.count(search_term) > 0:
                results[key] = val[0]
        return results

    def refresh_cache(self):
        """ Refresh the cache """
        self.loaded.clear()
        self.refresh.set()
        while True:
            # Wait for FAQ Cache
            if self.loaded.is_set():
                break
            sleep(1)
        return True


faq_cache = FAQs()  # pylint: disable=invalid-name
