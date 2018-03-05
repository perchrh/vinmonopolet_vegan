#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup


def parse_title(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')
    if soup.title:
        title = soup.title.string
        if title:
            return title.strip()

    return None


import urllib3
urllib3.disable_warnings()
import requests
from urllib.parse import urlparse


def get_webpage(url):
    if not urlparse(url).scheme:
        url = "http://" + url

    # use a fake custom user agent string to avoid silly webpages rejecting the library's default agent string
    custom_user_agent = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36"}
    r = requests.get(url, headers=custom_user_agent, verify=False, timeout=30)
    r.raise_for_status()
    return r.text


def get_title(url):
    try:
        body = get_webpage(url)
        if body:
            return parse_title(body)
        else:
            return None
    except requests.exceptions.RequestException as ex:
        print("Error retrieving web page: {} ".format(type(ex)))
        return None
