#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import codecs
import sys
import unicodedata
import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import urllib
import time

sys.stdout = codecs.getwriter('utf8')(sys.stdout)


#returns the longest common substring
def lcs(S1, S2):
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


def namesAreSimilarEnough(companyName, manufacturer_name):
    return len(lcs(manufacturer_name.lower(), companyName.lower())) >= 4

#replaces accented characters
def replaceAccents(variation):
    reCombining = re.compile(u'[\u0300-\u036f\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f]', re.U)
    return reCombining.sub('', unicodedata.normalize('NFD', unicode(variation)))


def replaceAccents2(variation):
    return ''.join((c for c in unicodedata.normalize('NFD', variation) if unicodedata.category(c) != 'Mn'))


def endsWithCommonWord(variation):
    if not variation:
        return False

    words = variation.split()
    lastWord = words[-1].lower()
    return lastWord in {"and", "wines", "wine", "spirits"}


def generate_name_variations(name):
    #these words may not be used as part of the company name at Vinmonopolet
    excludedWords = {"winery", "company", "pty", "ltd", "ltd.", "vineyard", "estate", "plc", "cellar", "winemaker",
                     "group", "international", "wines", "limited", "agricola", "winework", "wineries", "farm",
                     "family", "vigneron", "merchant", "at", "of", "the", "tasting", "room", "l.l.c.", "s.r.l.",
                     "s.p.a",
                     "c.", "vinegarden", "s.a.", "cellars", "brands", "signature", "ranch", "distilleries", "inc",
                     "organic", "sons"}
    variations = []
    name_parts = name.lower().strip().split()
    short_name = u""
    for part in name_parts:
        if part.lower() not in excludedWords:
            short_name = short_name + part + u" "
    variation = short_name.strip()
    while variation.endswith("-") or variation.endswith("&"):
        variation = variation[0:-1].strip()
    while endsWithCommonWord(variation):
        variation = u" ".join(variation.split()[0:-1]).strip()
    while variation.endswith("-") or variation.endswith("&"):
        #remove them again, in case there are new ones after stripping away words
        variation = variation[0:-1].strip()

    #add mutations of the name as well as the name itself
    variations.append(variation)
    variations.append(variation.replace(" ", "-", 1))
    variations.append(variation.replace(" ", "-", 2))
    variations.append(replaceAccents(variation))
    variations.append(replaceAccents2(variation))

    names = set()
    names.add(name.lower().strip()) #always add the original name
    for variant_name in variations:
        the_name = variant_name.strip().lower()
        if len(the_name) > 3:
            names.add(the_name)

    return names - {"wine", "hills", "creek", "view", "weingut"} #exclude some generic names


def fetchProcessedCompanyList(partial=False):
    file = codecs.open('wine.json', encoding='utf-8')
    data = file.read()
    companies = json.loads(data)

    companyObjects = list()
    for candidate in companies:
        status = candidate['company']['status']
        if (status == 'Has Some Vegan Options' and partial) or (status == 'Vegan Friendly' and not partial):
            #add company name aliases
            candidate["company"]["company_name_aliases"] = generate_name_variations(
                candidate['company']['company_name'])
            companyObjects.append(candidate)
    file.close()

    return companyObjects


def printPotentialProductMatch(search_result):
    html_link_product = "<a href='%s'>%s</a>" % (search_result["Lenke"], search_result["Varenummer"])
    print "<li>%s, %s. %s fra %s (%s) med varenummer %s</li>" % (
        search_result["Produsent"], search_result["Produktnavn"], search_result["Varetype"],
        search_result["Land/distrikt"], search_result["Produktutvalg"], html_link_product)


def checkCompany(browser, company):
    search_results = []
    for alias in company["company"]["company_name_aliases"]:
        encodedCompanyName = urllib.quote(alias.encode("utf-8"))
        search_url = "http://www.vinmonopolet.no/vareutvalg/sok?query=" + "\"" + encodedCompanyName + "\""
        browser.get(search_url)
        time.sleep(0.2) # Let the page load
        search_result_summary = browser.find_element_by_css_selector("h1.title")
        if search_result_summary.text != "Vareutvalg: ingen treff":
            productlinktexts = browser.find_elements_by_css_selector("#productList h3 a")
            productlinks = [link.get_attribute("href") for link in productlinktexts]
            for link in productlinks:
                browser.get(link)

                product_name = browser.find_element_by_css_selector("div.head h1").text
                result_data = {
                    "Lenke": link,
                    "Søkeord": alias,
                    "Firmalenke": search_url,
                    "Produktnavn": product_name
                }

                for field in browser.find_elements_by_css_selector("div.productData li"):
                    try:
                        field_name = field.find_element_by_css_selector("strong").text
                        key = field_name.replace(":", "").strip()
                        field_value = field.find_element_by_css_selector("span").text
                        value = field_value.strip()
                        if value:
                            result_data[key] = value
                    except NoSuchElementException:
                        pass

                if not "Varetype" in result_data: #must have a declared type name
                    print "WARNING: could not find product type for", result_data
                    pass
                elif not result_data["Varetype"].lower().find("vin") >= 0:  #must be a wine to match
                    pass
                elif "Produsent" not in result_data:
                    print "WARNING: Missing manufacturer data for company with alias", alias, "and product", product_name, "by grocer", result_data["Grossist"], link
                elif namesAreSimilarEnough(alias, result_data["Produsent"]):
                    search_results.append(result_data)
                else:
                    print "WARNING: Ignoring bad match", product_name, "from", result_data["Produsent"]

    if not search_results:
        company["search_results"] = []
    else:
        #delete duplicate products, keep the ones with the most popular alias
        #check if the sku exist in one of less popular alias, and if so, delete it
        most_popular_alias = findMostFrequentAliasInSearchResults(search_results)
        known_skus = set()
        filtered_search_results = list()
        for item in search_results:
            if item["Søkeord"] == most_popular_alias:
                known_skus.add(item["Varenummer"])
                filtered_search_results.append(item)

        for item in search_results:
            if item["Søkeord"] == most_popular_alias:
                continue

            sku = item["Varenummer"]
            if sku not in known_skus:
                filtered_search_results.append(item)

        company["search_results"] = filtered_search_results


def findMostFrequentAliasInSearchResults(list_of_result_data):
    aliases = [item["Søkeord"] for item in list_of_result_data]
    maxAlias = max(set(aliases), key=aliases.count)
    maxCount = aliases.count(maxAlias)

    return maxAlias, maxCount


def prettyJoin(list):
    stripped_list = [x.strip() for x in list]
    term_list = []
    for term in stripped_list:
        if term.endswith(","):
            term_list.append(term[0:-1]).strip()
        else:
            term_list.append(term)
    filtered_list = sorted(set([x for x in term_list if x]))

    if len(filtered_list) == 1:
        return filtered_list[0]

    return " og ".join([", ".join(filtered_list[0:-1]), filtered_list[-1]])


def printCompanySummary(potential_matches, company_name):
    (most_frequent_alias, count) = findMostFrequentAliasInSearchResults(potential_matches)
    company_link = None
    company_types = set()
    company_regions = set()
    company_order_categories = set()
    inBasisUtvalg = False
    for result_data in potential_matches:
        if result_data["Søkeord"] == most_frequent_alias:
            company_link = result_data["Firmalenke"]

            type = result_data["Varetype"]
            company_types.add(type)

            region = (result_data["Land/distrikt"].replace(u", Øvrige", u"").replace(u", ", u"/", 1))
            company_regions.add(region)

            category = result_data["Produktutvalg"]
            company_order_categories.add(category)
            if "Basisutvalg" == category:
                inBasisUtvalg = True

    print "<a href='%s'>%s</a>. %d varer. %s. %s fra %s." % (
        company_link, company_name, count, "<b>Basisutvalg</b>" if inBasisUtvalg else company_order_categories.pop(),
        prettyJoin(list(company_types)), prettyJoin(list(company_regions)))


def printCompany(company):
    potential_matches = company["search_results"]
    if potential_matches:
        print "Potential match for company", company["company"]["company_name"], ":"
        printCompanySummary(potential_matches, company["company"]["company_name"])
        print "<ul>"

        for result_data in potential_matches:
            printPotentialProductMatch(result_data)

        print "</ul>"
        print ""

if __name__ == "__main__":
    browser = webdriver.Firefox() # Get local session of firefox

    companies = fetchProcessedCompanyList()
    print "Vegan Friendly wine manufacturers (", len(companies), "candidates ):"
    print "-------------------------------------"
    for company in companies:
        checkCompany(browser, company)
        printCompany(company)

    companies = fetchProcessedCompanyList(True)
    print ""
    print "Wine manufacturers with some vegan options (", len(companies), "candidates ):"
    print "-------------------------------------"
    for company in companies:
        checkCompany(browser, company)
        printCompany(company)

    browser.close()

