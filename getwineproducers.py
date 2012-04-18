#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import codecs
import sys
import unicodedata
import re
import time
from selenium import webdriver
import urllib

sys.stdout = codecs.getwriter('utf8')(sys.stdout)


def LongestCommonSubstring(S1, S2):
    M = [[0] * (1 + len(S2)) for i in xrange(1 + len(S1))]
    longest, x_longest = 0, 0
    for x in xrange(1, 1 + len(S1)):
        for y in xrange(1, 1 + len(S2)):
            if S1[x - 1] == S2[y - 1]:
                M[x][y] = M[x - 1][y - 1] + 1
                if M[x][y] > longest:
                    longest = M[x][y]
                    x_longest = x
            else:
                M[x][y] = 0
    return S1[x_longest - longest: x_longest]


def generate_name_variations(name):
    reCombining = re.compile(u'[\u0300-\u036f\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f]', re.U)

    variations = []
    #remove parts of te name that may not be used by vinmonopolet, like "winery" "corp" and so
    name_parts = name.split(" ")
    short_name = u""
    exclude_list = ["winery", "company", "pty", "ltd", "ltd.", "vineyard", "estate", "plc", "cellar", "winemaker",
                    "group", "international", "wines", "limited", "agricola", "winework", "wineries", "farm",
                    "family", "vigneron", "merchant"]
    for part in name_parts:
        found = False
        for exclude in exclude_list:
            if part.lower().find(exclude) >= 0:
                found = True
                break
        if not found:
            short_name = short_name + part + u" "
    for variation in [name, short_name]:
        variation = variation.strip()
        while variation.endswith("-") or variation.endswith("&"):
            variation = variation[0:-1]
        while len(variation.split(" ")) > 1 and (
            variation.split(" ")[-1].lower().endswith("and") or variation.split()[-1].lower().endswith("wines") or
            variation.split()[-1].lower().endswith("wine") or
            variation.split()[-1].lower().endswith("spirits")):
            variation = u" ".join(variation.split(" ")[0:-1])
        while variation.endswith("-") or variation.endswith("&"):
            variation = variation[0:-1] #remove them again, in case there are new ones after stripping away words
        variations.append(variation)

        #add mutations of the name as well as the name
        variations.append(
            ''.join((c for c in unicodedata.normalize('NFD', variation) if unicodedata.category(c) != 'Mn')))
        variations.append(variation.replace(" ", "-", 1))
        variations.append(variation.replace(" ", "-", 2))
        variations.append(reCombining.sub('', unicodedata.normalize('NFD', unicode(variation))))

    return set(variations)


def build_company_name_list():
    file = codecs.open('wine.json', encoding='utf-8')
    data = file.read()
    companies = json.loads(data)
    company_names = set()
    for candidate in companies:
        status = candidate['company']['status']
        #if status == 'Vegan Friendly': # or status == 'Has Some Vegan Options':
        if status == 'Has Some Vegan Options':
            name = candidate['company']['company_name']
            company_names |= generate_name_variations(name)
    file.close()
    company_names.discard("")
    company_names.discard(" ")
    sorted_companies = list(company_names)
    sorted_companies.sort()
    return sorted_companies


def check_company(browser, company):
    #TODO filter on type (vin) and country too
    search_url = "http://www.vinmonopolet.no/vareutvalg/sok?query=" + "\"" + urllib.quote(
        company.strip().encode("utf-8")) + "\""
    browser.get(search_url)
    time.sleep(0.2) # Let the page load, will be added to the API
    search_result = browser.find_element_by_css_selector("h1.title")
    if search_result.text != "Vareutvalg: ingen treff":
        productlinktexts = browser.find_elements_by_css_selector("#productList h3 a")
        productlinks = [link.get_attribute("href") for link in productlinktexts]
        for link in productlinks:
            browser.get(link)

            data = browser.find_elements_by_css_selector("div.productData li")

            manufacturer_name = "ukjent produsent"
            type_name = "ukjent type"
            region_name = "ukjent region"
            grossist = "ukjent grossist"
            product_name = browser.find_element_by_css_selector("div.head h1").text

            for field in data:
                field_name = field.find_element_by_css_selector("strong").text
                if field_name == "Produsent:":
                    manufacturer_name = field.find_element_by_css_selector("span").text
                elif field_name == "Varetype:":
                    type_name = field.find_element_by_css_selector("span").text
                elif field_name == "Land/distrikt:":
                    region_name = field.find_element_by_css_selector("span").text
                elif field_name == "Grossist:":
                    grossist = field.find_element_by_css_selector("span").text

            if len(LongestCommonSubstring(manufacturer_name.lower(), company.lower())) >= 4:
                #don't add company if the name does not match
                html_link = "<a href='" + search_url + "'>" + company + "</a>"
                print company, "search ->", "<li>", ", ".join(
                    [manufacturer_name, product_name, type_name, region_name, html_link]), "</li>"
            elif manufacturer_name == "ukjent produsent":
                print company, "search ->", "Could not find manufacturer of ", product_name, "by", grossist, link


if __name__ == "__main__":
    browser = webdriver.Firefox() # Get local session of firefox
    company_names = build_company_name_list()

    for company in company_names:
        check_company(browser, company)

    browser.close()

