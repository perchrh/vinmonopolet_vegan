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


import requests
from urllib.parse import urlparse


def get_webpage(url):
    if not urlparse(url).scheme:
        url = "http://" + url

    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.text
    except requests.exceptions.RequestException as ex:
        print(str(ex))
        return None


def get_title(url):
    body = get_webpage(url)
    if body:
        return parse_title(body)
    else:
        return None
