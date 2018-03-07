#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import string

def parse_title(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')
    if soup.title:
        title = soup.title.string
        if title:
            clean_title = ''.join([x for x in title if x in string.printable])
            return clean_title.strip()

    return None


import urllib3
urllib3.disable_warnings()
import requests
from urllib.parse import urlparse


def get_webpage(url, identifier=None, name=None):
    if not urlparse(url).scheme:
        url = "http://" + url

    # use a fake custom user agent string to avoid silly webpages rejecting the library's default agent string
    custom_user_agent = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36"}
    r = requests.get(url, headers=custom_user_agent, verify=False, timeout=30)
    if r.status_code == 404:
        root_page = urlparse(url)
        new_url = "{}://{}".format(root_page.scheme, root_page.netloc)
        r2 = requests.get(new_url, headers=custom_user_agent, verify=False, timeout=30)
        if r2.status_code == 200:
            print("WARNING: error retrieving url={}, id={}, name={}, but {} worked".format(url, identifier, name, new_url))
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
