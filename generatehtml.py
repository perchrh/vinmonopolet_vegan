#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import codecs
import sys

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

file = codecs.open('vegan-wine-companies-at-vinmonopolet', encoding='utf-8')

#TODO also output wine type and region

print u"<h1>Veganske vinfirma på Vinmonopolet</h1>"
print u"<ul>"
for company in file:
    company = company.strip()
    search_url=u"http://www.vinmonopolet.no/vareutvalg/sok?query=" + "\"" + urllib.quote(company.strip().encode("utf-8")) + "\""
    html_link=u"<a href='" + search_url +"'>"+company+"</a>"
    print u"<li>", html_link, u"</li>"
print u"</ul>"


file = codecs.open('partial-vegan-wine-companies-at-vinmonopolet', encoding='utf-8')

print u"<h1>Delvis veganske vinfirma på Vinmonopolet</h1>"
print u"<ul>"
for company in file:
    company = company.strip()
    search_url=u"http://www.vinmonopolet.no/vareutvalg/sok?query=" + "\"" + urllib.quote(company.strip().encode("utf-8")) + "\""
    html_link=u"<a href='" + search_url +"'>"+company+"</a>"
    print u"<li>", html_link, u"</li>"
print u"</ul>"
