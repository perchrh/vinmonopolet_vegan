#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import unicodedata
import time
import urllib.parse
from difflib import SequenceMatcher
import string

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

vegan_friendly_output_filename = "vegan-friendly-searchresult-vinmonopolet.json"
some_vegan_products_output_filename = "some-vegan-options-searchresult-vinmonopolet.json"


def LongestCommonSubstringSize(S1, S2):
    cleanString1 = cleanString(S1)
    cleanString2 = cleanString(S2)
    matcher = SequenceMatcher(None, cleanString1, cleanString2)
    match = matcher.find_longest_match(0, len(cleanString1), 0, len(cleanString2))
    return match.size


def cleanString(S1):
    return S1.lower().strip()


def calculateStringSimilarityPercentage(S1, S2):
    cleanString1 = cleanString(S1)
    cleanString2 = cleanString(S2)
    return SequenceMatcher(None, cleanString1, cleanString2).ratio() * 100


def remove_diacritics(s):
    return ''.join(x for x in unicodedata.normalize('NFKD', s) if x in string.printable)


def derive_short_name(original_name):
    # Removes parts of the name that may not be used by vinmonopolet, like "winery", "ltd." and so
    name_parts = original_name.lower().strip().split()
    short_name = u""
    generic_name_exclude_list = {"winery", "company", "pty", "ltd", "vineyard", "vineyards", "estate", "estates", "plc",
                                 "cellar",
                                 "winemaker", "group", "international", "wines", "limited", "agricola", "winework",
                                 "wineries", "wine",
                                 "farm", "family", "vigneron", "vign", "merchant", "at", "of", "the", "de", "du",
                                 "cellars", "vintners",
                                 "agr", "gmbh", "weinkellerei", "sa", "fe", "dr", "spa", "c", "co", "casa", "casas",
                                 "ab", "cspa", "fatt",
                                 "champagne", "weingut", "weing", "weinhaus", "az,", "inc", "ag", "gebr", "gebruder",
                                 "ch", "cant", "winery", "vin",
                                 "bros", "cast", "corp", "di", "el", "dominio", "pty", "il", "est", "srl", "das", "do",
                                 "llc", "bds", "int",
                                 "bryggeri", "brygghus", "bryghus", "brewery", "ab", "by", "azienda",
                                 "brewers", "breweries", "brewing", "brouwerij", "birras",
                                 "beer", "beer house", "brew house", "birra", "brauerei", "brasserie", "bieres",
                                 "bierbrouwerij", "abbazia"}

    for part in name_parts:
        found = False
        for exclude in generic_name_exclude_list:
            if part.replace('.', '').find(exclude.lower()) >= 0:  # ignore '.' during matching
                found = True
                break
        if not found:
            short_name = " ".join([short_name, part])

    while short_name and remove_diacritics(short_name[-1]) not in string.ascii_letters:
        short_name = short_name[:-1].strip()
    if not short_name:
        short_name = original_name  # name could not be shortened
    return short_name.strip()


def derive_synonyms(original_name_lower):
    return {
        original_name_lower.replace("marques", "marq."),
        original_name_lower.replace("agricola", "agr."),
        original_name_lower.replace("vigneron", "vign."),
        original_name_lower.replace("weingut", "weing."),
        original_name_lower.replace("bodegas", "bod."),
        original_name_lower.replace("domaine", "dom."),
        original_name_lower.replace("champagne", "champ."),
        original_name_lower.replace("gebruder", "gebr."),
        original_name_lower.replace("brothers", "bros."),
        original_name_lower.replace("doctor", "dr."),
        original_name_lower.replace("saint", "st."),
        original_name_lower.replace("company", "co."),
        original_name_lower.replace("cantine", "cant."),
        original_name_lower.replace("cantina", "cant."),
        original_name_lower.replace("distilleria", "dist."),
        original_name_lower.replace("chateau", "ch."),
        original_name_lower.replace("vinicole", "vin."),
        original_name_lower.replace("fattoria", "fatt.")
    }


def generate_name_variations(original_name):
    variations = set()
    search_base = original_name.lower().strip()
    search_base = search_base.replace(')', ' ').replace(')', ' ')
    terms = {
        search_base,
        derive_short_name(search_base)
    }
    terms |= derive_synonyms(search_base)

    # remove trailing generic terms of name
    for variation in terms:
        # todo cleanup, extract method
        while len(variation.split(" ")) > 1 and (variation.split()[-1].lower().endswith("wines")
                                                 or variation.split()[-1].lower().endswith("vineyards")
                                                 or variation.split()[-1].lower().endswith("wine")
                                                 or variation.split()[-1].lower().endswith("beer")
                                                 or variation.split()[-1].lower().endswith("winery")
                                                 or variation.split()[-1].lower().endswith("brewery")
                                                 or variation.split()[-1].lower().endswith("spirits")
                                                 or variation.split()[-1].lower().endswith("champagne")
                                                 or variation.split()[-1].lower().endswith("productions")):
            variation = u" ".join(variation.split()[0:-1])
        while variation and remove_diacritics(variation[-1]) not in string.ascii_letters:
            variation = variation[:-1].strip()
        variations.add(variation.strip())

    # discard too common words, TODO avoid that short_name becomes a too generic word
    variations -= {"hills", "creek", "view", "valley", "ridge", "grand", "alta", "house", "nuevo", "gran",
                   "chateau", "monte", "mount", "veuve", "long", "port", "martin", "royal", "urban"}
    #TODO discard all country names and place names
    #TODO discard all adjectives

    # Discard stop words
    variations -= {"and", "la", "by", "las", "el", "a", "i", "mas", "bon"}

    # Discard too short name variations, but keep the short_name we created
    variations = {name for name in variations if (len(name) > 3 or name == derive_short_name(search_base))}

    # Include the full original name as well
    # Test to see if this gives false positive because of fuzzy matching at vinmonopolet.no
    # variations |= original_name.lower()

    return variations


def create_vegan_friendly_company_list_with_name_variations():
    return build_company_name_list(False)


def create_some_vegan_options_company_list_with_name_variations():
    return build_company_name_list(True)


def sort_by_company_name(company_list_tuple):
    company_dict, variations = company_list_tuple
    return company_dict["company_name"]


def build_company_name_list(allowPartial):
    # Read known companies from Barnivore data
    file = open('wine.json', encoding='utf-8')
    candidate_companies = json.loads(file.read())
    file.close()

    companies = list()
    for candidate in candidate_companies:
        country = candidate['company']['country']
        if (country == 'USA'):  # Too much non-matching data on USA wines, few of them available at Vinmonopolet
            print("Skipping wine for country =", country, "company =", candidate['company']['company_name'])
            continue

        status = candidate['company']['status']
        if (status == 'Has Some Vegan Options' and allowPartial) or (status == 'Vegan Friendly' and not allowPartial):
            candidate['company']['barnivore_url'] = "http://www.barnivore.com/wine/%s/company" % candidate['company'][
                'id']  # to simplify lookups later
            companies.append((candidate["company"], (generate_name_variations(candidate['company']['company_name']))))

    # Sort company list
    companies.sort(key=sort_by_company_name)

    return companies


def search_vinmonopolet_for_company_name_variation(browser, company_name):
    search_url = "https://www.vinmonopolet.no/vmpSite/search/?q=\"%s\"&searchType=product" % urllib.parse.quote(
        company_name.strip().encode("utf-8"))
    browser.get(search_url)

    try:
        browser.find_element_by_css_selector("#search-results h1")
    except NoSuchElementException:
        browser.find_element_by_css_selector("div.search-empty-results-page")
        return []

    product_linktexts = browser.find_elements_by_css_selector("h2.product-item__name a")
    product_links = [link.get_attribute("href") for link in product_linktexts]
    products = []
    for link in product_links:
        browser.get(link)

        wine_properties = {}
        product_name = browser.find_element_by_css_selector("div.product__hgroup h1").text
        wine_properties["Produktnavn"] = product_name

        stock_status = browser.find_element_by_css_selector("div.product-stock-status")
        wine_properties["Lagerstatus"] = stock_status.text.strip()
        if stock_status.text.strip().lower().find("utgått") >= 0:
            print("Ignoring product that has expired from stock: '%s' - %s " % (product_name, link))
            continue

        # Expand tabs to make all product information visible
        product_data_groups = browser.find_element_by_css_selector("div.product__all-info div.accordion")
        data_buttons = product_data_groups.find_elements_by_tag_name("button")
        data_containers = product_data_groups.find_elements_by_tag_name("div")
        for i in range(0, len(data_buttons)):
            if not data_containers[i].is_displayed():
                data_buttons[i].click()

        for group in browser.find_elements_by_css_selector("div.product__all-info dl"):
            labels = group.find_elements_by_css_selector("dt")
            values = group.find_elements_by_css_selector("dd")
            for i in range(0, len(labels)):
                key = labels[i].text.replace(":", "").replace("*", "").strip()
                value = values[i].text.strip()
                wine_properties[key] = value

        if wine_properties["Utvalg"] == "Partiutvalget" or wine_properties["Utvalg"] == "Testutvalget":
            # print("Skipping product that's not expected to stay in stores a while")
            continue

        land = None
        distrikt = None
        underdistrikt = None
        geo = wine_properties.pop("Land, distrikt, underdistrikt").split(", ")
        if len(geo) == 3:
            (land, distrikt, underdistrikt) = geo
        elif len(geo) == 2:
            (land, distrikt) = geo
        elif len(geo) == 1:
            land = geo[0]

        wine_properties["Land"] = land if "Øvrige" != land else None
        wine_properties["Distrikt"] = distrikt if "Øvrige" != distrikt else None
        wine_properties["Underdistrikt"] = underdistrikt if "Øvrige" != underdistrikt else None

        wine_properties["Produktside"] = link
        wine_properties["Søkeside"] = search_url
        wine_properties["ProduktPris"] = browser.find_element_by_css_selector("span.product__price").text
        wine_properties["ProduktPrisPerEnhet"] = browser.find_element_by_css_selector("span.product__cost_per_unit").text
        wine_properties["ProduktVolum"] = browser.find_element_by_css_selector("span.product__amount").text

        for candidate in browser.find_elements_by_css_selector("ul.link-list--with-separators li a"):
            description = candidate.text
            if description.find("Produsent") >= 0:
                wine_properties["ProdusentSide"] = candidate.get_attribute("href")
                break

        # Product image url. It Is Known.
        wine_properties["ProduktBilde"] = "https://bilder.vinmonopolet.no/cache/600x600-0/%s-1.jpg" % (wine_properties["Varenummer"])

        type_name_lower = wine_properties["Varetype"]
        if (type_name_lower.find("vin") < 0
            and type_name_lower.find("champ") < 0
            and type_name_lower.find("alkoholfr") < 0) \
                or type_name_lower.find("brennevin") >= 0:
            print("Skipping product that's not a wine, type was", type_name_lower)
            continue
        else:
            products.append(wine_properties)

        time.sleep(0.3)  # Don't hammer the website

    return products


def translate_country_name(country):
    # poor man's translation to Norwegian
    return country.replace("italy", "italia"). \
        replace("france", "frankrike"). \
        replace("germany", "tyskland"). \
        replace("spain", "spania"). \
        replace("austria", "østerrike"). \
        replace("norway", "norge"). \
        replace("sweden", "sverige"). \
        replace("denmark", "danmark"). \
        replace("netherlands", "nederland"). \
        replace("ireland", "irland"). \
        replace("belgium", "belgia"). \
        replace("greece", "hellas"). \
        replace("hungary", "ungarn"). \
        replace("croatia", "kroatia"). \
        replace("finland", "finland"). \
        replace("austria", "østerrike"). \
        replace("slovakia", "slovakia"). \
        replace("poland", "polen"). \
        replace("south africa", "sør-afrika")


def countries_differ(company_dict, country):
    if "country" in company_dict.keys():
        clean_country_expected = translate_country_name(company_dict["country"].lower().strip()).replace("-", " ")
        clean_country_found = country.lower().strip().replace("-", " ")
        country_not_matching = clean_country_found.find(clean_country_expected) == -1  # not found, ergo different
        return country_not_matching
    return False  # otherwise cannot say


def product_names_differ_too_much(original_name, manufacturer_name, variation):
    if LongestCommonSubstringSize(original_name, manufacturer_name) < 4:
        return True  # search result doesn't contain a similar company name as in the search query
    elif calculateStringSimilarityPercentage(derive_short_name(original_name),
                                             derive_short_name(manufacturer_name)) < 80 \
            and calculateStringSimilarityPercentage(original_name, manufacturer_name) < 80 \
            and calculateStringSimilarityPercentage(original_name,
                                                    derive_synonyms(manufacturer_name.lower()).pop()) < 80 \
            and not original_name.lower().startswith(variation.lower()):  # allow mismatch because of added words
        print(
            "Warning: ignoring product with too big difference in original company name and search result's company name: '%s' != '%s'" % (
                derive_short_name(original_name), derive_short_name(manufacturer_name)))
        return True  # search result doesn't contain a similar company name as in the search query
    else:
        return False


def find_products_from_manufacturer(company_dict, name_variations):
    original_name = company_dict["company_name"]
    print("Searching for wine producer='%s' with name variations='%s'" % (original_name, name_variations))

    company_products_found_in_search = {}
    for variation in name_variations:
        for product in search_vinmonopolet_for_company_name_variation(browser, variation):
            if product_names_differ_too_much(company_dict["company_name"], product["Produsent"], variation):
                continue
            elif countries_differ(company_dict, product["Land"]):
                print("Warning: country mismatch for this product (%s), expected '%s' and got '%s'" % (
                product["Produktnavn"], translate_country_name(company_dict["country"].lower()),
                product["Land"].lower()))
                pass

            sku = product["Varenummer"]
            if not sku in company_products_found_in_search.keys():
                company_products_found_in_search[sku] = product
            else:
                # already added.. keep the entry with the longest search string hit, as that is assumed to be the most precise name
                old_entry = company_products_found_in_search[sku]
                if len(old_entry["Søkeside"]) < len(product["Søkeside"]):
                    company_products_found_in_search[sku] = product

    return company_products_found_in_search


def read_previously_searched_companies(inputfile):
    previously_searched_companies = list()
    try:
        file = open(inputfile, encoding='utf-8')
        search_results_from_previous_run = json.loads(file.read())
        file.close()
        for company in search_results_from_previous_run:
            previously_searched_companies.append(company)
    except Exception as exc:
        print("Warning: Couldn't read stored search results. Assuming should start from scratch. (Got %s)" % exc)
        pass
    return previously_searched_companies


def partition_by_previously_searched_companies(company_and_name_variations_tuple, inputfile):
    previously_searched_companies = read_previously_searched_companies(inputfile)
    if not previously_searched_companies:
        return company_and_name_variations_tuple, []

    last_company_searched_for = previously_searched_companies[-1]["company_name"]
    to_process = []
    is_adding = False
    for company_dict, name_variations in company_and_name_variations_tuple:
        company_name = company_dict["company_name"]
        if is_adding:
            to_process.append((company_dict, name_variations))
        else:
            print("Skipping already processed company %s found in %s while resuming previous search" % (
            company_name, inputfile))

        if company_name == last_company_searched_for:
            is_adding = True

    return to_process, previously_searched_companies


def search_for_wines_and_write_results_file(company_and_name_variations_tuple, outputfile, is_resuming=False):
    all_companies = []

    if is_resuming:
        # TODO write every company to output file, even when there are no search results. That way we know better which companies have been searched for and not
        to_process_company_and_name_variations_tuple, previously_searched_companies = partition_by_previously_searched_companies(
            company_and_name_variations_tuple, outputfile)
        company_and_name_variations_tuple = to_process_company_and_name_variations_tuple
        for company_dict in previously_searched_companies:
            all_companies.append(company_dict)

    for company_dict, name_variations in company_and_name_variations_tuple:
        company_name = company_dict["company_name"]

        company_products_found_in_search = find_products_from_manufacturer(company_dict, name_variations)

        if (company_products_found_in_search):
            company_dict["products_found_at_vinmonopolet"] = company_products_found_in_search
            print("Found %d products for company %s" % (len(company_products_found_in_search), company_name))
            all_companies.append(company_dict)

            # Write the current list to file, to avoid losing all data in case of network/http server/other problems)
            f = open(outputfile, mode='w', encoding='utf-8')
            json.dump(all_companies, f, indent=2, ensure_ascii=False, sort_keys=True)
            f.flush()
            f.close()


if __name__ == "__main__":
    browser = webdriver.Chrome()  # Get local browser session
    try:
        company_list = create_vegan_friendly_company_list_with_name_variations()
        print("Searching for %d vegan friendly wine companies at Vinmonopolet" % len(company_list))
        print("Outputting search results to file", vegan_friendly_output_filename)
        search_for_wines_and_write_results_file(company_list, vegan_friendly_output_filename, is_resuming=True)

        company_list = create_some_vegan_options_company_list_with_name_variations()
        print("Searching for %d wine manufactureres with some vegan options at Vinmonopolet" % len(company_list))
        print("Outputting search results to file", some_vegan_products_output_filename)
        search_for_wines_and_write_results_file(company_list, some_vegan_products_output_filename, is_resuming=True)
    except Exception as exc:
        browser.close()  # make sure to call close, or /tmp will fill up with large firefox session files
        raise exc
    finally:
        browser.close()  # make sure to call close, or /tmp will fill up with large firefox session files
