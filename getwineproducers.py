#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import unicodedata
import time
from selenium import webdriver
import urllib.parse
from difflib import SequenceMatcher
import string

vegan_friendly_output_filename = "vegan-friendly-searchresult-vinmonopolet.json"
some_vegan_products_output_filename = "some-vegan-options-searchresult-vinmonopolet.json"


def LongestCommonSubstringSize(S1, S2):
    cleanString1 = cleanString(S1)
    cleanString2 = cleanString(S2)
    matcher = SequenceMatcher(None, cleanString1, cleanString2)
    match = matcher.find_longest_match(0, len(cleanString1), 0, len(cleanString2))
    return match.size


def cleanString(S1):
    return remove_diacritics(S1).lower().strip()


def calculateStringSimilarityPercentage(S1, S2):
    cleanString1 = cleanString(S1)
    cleanString2 = cleanString(S2)
    return SequenceMatcher(None, cleanString1, cleanString2).ratio() * 100


def remove_diacritics(s):
    return ''.join(x for x in unicodedata.normalize('NFKD', s) if x in string.printable)


def derive_short_name(original_name):
    #Removes parts of the name that may not be used by vinmonopolet, like "winery", "ltd." and so
    name_parts = original_name.lower().strip().split()
    short_name = u""
    generic_name_exclude_list = {"winery", "company", "pty", "ltd", "ltd.", "vineyard", "vineyards", "estate", "estates", "plc", "cellar",
                                 "winemaker", "group", "international", "wines", "limited", "agricola", "winework", "wineries",
                                 "farm", "family", "vigneron", "vign.", "merchant", "at", "of", "the", "de", "du", "cellars", "vintners",
                                 "agr.", "gmbh", "weinkellerei", "s.a.", "F.E.", "dr.", "s.p.a", "c.", "casa", "casas",
                                 "champagne", "weingut", "weing.", "weinhaus", "a.z.", "az,", "inc.", "ag", "gebr.", "ch.", "cant.", "winery", 
                                 "bros", "cast.", "corp", "di", "dominio", "pty", "il", "est.", "s.r.l", "das", "do"}

    for part in name_parts:
        found = False
        for exclude in generic_name_exclude_list:
            if part.find(exclude) >= 0:
                found = True
                break
        if not found:
            short_name = " ".join([short_name, part])

    while short_name and short_name[-1] not in string.ascii_letters:
        short_name = short_name[:-1].strip()
    if not short_name:
        short_name = original_name # name could not be shortened
    return short_name.strip()


def derive_synonyms(original_name_lower):
    return {
        original_name_lower.replace("marques", "marq."),
        original_name_lower.replace("agricola", "agr."),
        original_name_lower.replace("weingut", "weing."),
        original_name_lower.replace("bodegas", "bod."),
        original_name_lower.replace("domaine", "dom.")
    }


def generate_name_variations(original_name):
    variations = set()
    search_base = remove_diacritics(original_name).lower().strip()
    terms = {
        search_base,
        derive_short_name(search_base)
    }
    terms |= derive_synonyms(original_name.lower())

    #remove trailing generic terms of name
    for variation in terms:
    # todo cleanup, extract method
        while len(variation.split(" ")) > 1 and (
                                    variation.split()[-1].lower().endswith("and")
                                or variation.split()[-1].lower().endswith("wines")
                            or variation.split()[-1].lower().endswith("wine")
                        or variation.split()[-1].lower().endswith("winery")
                    or variation.split()[-1].lower().endswith("spirits")
                or variation.split()[-1].lower().endswith("champagne")
            or variation.split()[-1].lower().endswith("productions")):
            variation = u" ".join(variation.split()[0:-1])
        while variation[-1] not in string.ascii_letters:
            variation = variation[:-1].strip()
        variations.add(variation.strip())

        #allow use of dashes instead of spaces in first part of the name
        variations.add(variation.replace(" ", "-", 1))
        variations.add(variation.replace(" ", "-", 2))

    #discard too general names
    variations -= {"wine", "hills", "creek", "view", "weingut"}

    #Discard too short name variations, but keep the short_name we created
    variations = {name for name in variations if len(name) > 3 or name == derive_short_name(original_name)}

    #print("DEBUG: returning variations for original: ", original_name, variations)
    return variations


def create_vegan_friendly_company_list_with_name_variations():
    return build_company_name_list(False)


def create_some_vegan_options_company_list_with_name_variations():
    return build_company_name_list(True)


def sort_by_company_name(company_list_tuple):
    company_dict, variations = company_list_tuple
    return company_dict["company_name"]


def build_company_name_list(allowPartial):
    #Read known companies from Barnivore data
    file = open('wine.json', encoding='utf-8')
    candidate_companies = json.loads(file.read())
    file.close()

    companies = list()
    for candidate in candidate_companies:
        status = candidate['company']['status']
        if (status == 'Has Some Vegan Options' and allowPartial) or (status == 'Vegan Friendly' and not allowPartial):
            candidate['company']['barnivore_url'] = "http://www.barnivore.com/wine/%s/company" % candidate['company']['id'] #to simplify lookups later
            companies.append(( candidate["company"], (generate_name_variations(candidate['company']['company_name']))))

    #Sort company list
    companies.sort(key=sort_by_company_name)

    return companies


def visit_product_page_systembolaget(browser, company_name, company_search_results_url):
    manufacturer_name = "ukjent produsent"
    grocer = "ukjent grossist"
    year = "ukjent år"
    product_selection ="ukjent utvalg"

    root = browser.find_element_by_css_selector("div.beverageProperties")
    product_name = root.find_element_by_css_selector("span.produktnamnfet").text
    type_name = root.find_element_by_css_selector("span.character strong").text
    try:
        product_selection = root.find_element_by_css_selector("h2.sortimenttext").text
    except:
        #sometimes this section is not available
        pass

    sku = ''.join(c for c in root.find_element_by_css_selector("span.produktnamnmager").text if c.isdigit())

    region_name = root.find_element_by_css_selector("div.country").text

    data = root.find_elements_by_css_selector("ul.beverageFacts li")

    for field in data:
        field_name = field.find_element_by_css_selector("span").text.strip()
        if field_name.startswith("Årgång"):
            year = field.find_element_by_css_selector("strong").text
        elif field_name.startswith("Producent") and not field_name.startswith("Producenten"):
            manufacturer_name = field.find_element_by_css_selector("strong").text
        elif field_name.startswith("Leverantör"):
            grocer = field.find_element_by_css_selector("strong").text

    if type_name.lower().find("vin") < 0:
        return None
    elif manufacturer_name == "ukjent produsent":
        print("Missing manufacturer data for company", company_name, "and product", product_name, "by grocer", grocer, browser.current_url)
        return None
    else:
        return {
            "manufacturer_name": manufacturer_name,
            "product_name": product_name,
            "type": type_name,
            "region": region_name,
            "grocer": grocer,
            "selection": product_selection,
            "company_search_page": company_search_results_url,
            "product_page": browser.current_url,
            "year": year,
            "sku": sku
        }


def search_systembolaget_for_company_name_variation(browser, company_name):
    search_url = "http://www.systembolaget.se/Sok-dryck/?searchquery=\"%s\"&sortfield=Default&sortdirection=Ascending&hitsoffset=0&page=1&searchview=All&groupfiltersheader=Default&filters=searchquery" % urllib.parse.quote(
        company_name.strip().encode("utf-8"))
    browser.get(search_url)
    time.sleep(0.2) # Let the page load

    empty_result = False
    try:
        noresult = browser.find_element_by_css_selector("#resultList .noResult").text
        empty_result = True
    except:
        pass

    if empty_result: return []

    is_single_hit_result = False
    try:
        browser.find_element_by_css_selector("div.beverageProperties")
        is_single_hit_result = True
    except:
        pass

    if is_single_hit_result:
        #it' a single result product page
        product = visit_product_page_systembolaget(browser, company_name, search_url)
        return [product]

    search_result_header = browser.find_element_by_css_selector("h2.filtersHeader")

    if search_result_header.text.find("(0 träffar)") >= 0: return []

    product_linktexts = browser.find_elements_by_css_selector("table.resultListTable tr td a")
    product_links = [link.get_attribute("href") for link in product_linktexts]
    products = []
    for link in product_links:
        browser.get(link)
        product = visit_product_page_systembolaget(browser, company_name, search_url)
        if product:
            products.append(product)

    return products


def search_vinmonopolet_for_company_name_variation(browser, company_name):
    search_url = "http://www.vinmonopolet.no/vareutvalg/sok?query=\"%s\"" % urllib.parse.quote(company_name.strip().encode("utf-8"))
    browser.get(search_url)
    time.sleep(0.3) # Let the page load
    search_result = browser.find_element_by_css_selector("h1.title")

    if search_result.text == "Vareutvalg: ingen treff": return []

    product_linktexts = browser.find_elements_by_css_selector("#productList h3 a")
    product_links = [link.get_attribute("href") for link in product_linktexts]
    products = []
    for link in product_links:
        browser.get(link)

        product_name = browser.find_element_by_css_selector("div.head h1").text

        expired_from_stock = False
        for field in browser.find_elements_by_css_selector("table.productTable h3.stock"):
            if field.text.lower().strip().find("utgått") >= 0:
                expired_from_stock = True
        if expired_from_stock:
            print("Ignoring product that has expired from stock: '%s' - %s " % (product_name, link))
            continue

        data = browser.find_elements_by_css_selector("div.productData li")

        manufacturer_name = "ukjent produsent"
        type_name = "ukjent type"
        region_name = "ukjent region"
        grocer = "ukjent grossist"
        distributor = "ukjent distributør"
        product_selection = "ukjent produktutvalg"
        sku = "ukjent varenummer"
        year = "ukjent år"

        for field in data:
            field_name = field.find_element_by_css_selector("strong").text
            if field_name == "Produsent:":
                manufacturer_name = field.find_element_by_css_selector("span").text
            elif field_name == "Varetype:":
                type_name = field.find_element_by_css_selector("span").text
            elif field_name == "Land/distrikt:":
                region_name = field.find_element_by_css_selector("span").text
            elif field_name == "Grossist:":
                grocer = field.find_element_by_css_selector("span").text
            elif field_name == "Produktutvalg:":
                product_selection = field.find_element_by_css_selector("span").text
            elif field_name == "Varenummer:":
                sku = field.find_element_by_css_selector("span").text
            elif field_name == "Distributør:":
                distributor = field.find_element_by_css_selector("span").text
            elif field_name == "Årgang:":
                year = field.find_element_by_css_selector("span").text

        type_name_lower = type_name.lower()
        if type_name_lower.find("vin") < 0 and type_name_lower.find("champ") < 0 and type_name_lower.find("alkoholfr"):
            continue
        elif manufacturer_name == "ukjent produsent":
            print("Missing manufacturer data for company", company_name, "and product", product_name, "by grocer", grocer, link)
            continue
        else:
            products.append({
                "manufacturer_name": manufacturer_name,
                "product_name": product_name,
                "type": type_name,
                "region": region_name,
                "selection": product_selection,
                "distributor": distributor,
                "grocer": grocer,
                "company_search_page": search_url,
                "product_page": link,
                "year": year,
                "sku": sku
            })

    return products


def translate_country_name(country):
    #poor man's translation to Norwegian
    return country.replace("italy", "italia"). \
        replace("france", "frankrike"). \
        replace("germany", "tyskland"). \
        replace("spain", "spania"). \
        replace("austria", "østerrike"). \
        replace("south africa", "sør-afrika")


def countries_differ(company_dict, region):
    if "country" in company_dict.keys():
        clean_country = translate_country_name(company_dict["country"].lower().strip()).replace("-", " ")
        clean_region = region.lower().strip().replace("-", " ")
        country_not_matching = clean_region.find(clean_country) == -1 #not found, ergo different
        return country_not_matching
    return False #otherwise cannot say


def product_names_differ_too_much(original_name, manufacturer_name, variation):
    if LongestCommonSubstringSize(original_name, manufacturer_name) < 4:
        return True # search result doesn't contain a similar company name as in the search query
    elif calculateStringSimilarityPercentage(derive_short_name(original_name), derive_short_name(manufacturer_name)) < 80 \
        and calculateStringSimilarityPercentage(original_name, manufacturer_name) < 80 \
        and not original_name.lower().startswith(variation.lower()): #allow mismatch because of added words
        print("Warning: ignoring product with too big difference in original company name and search result's company name: '%s' != '%s'" % (
            derive_short_name(original_name), derive_short_name(manufacturer_name)))
        return True # search result doesn't contain a similar company name as in the search query
    else:
        return False


def find_products_from_manufacturer(company_dict, name_variations):
    original_name = company_dict["company_name"]
    print("Searching for wine producer='%s' with name variations='%s'" % (original_name, name_variations))

    company_products_found_in_search = {}
    for variation in name_variations:
        for product in search_vinmonopolet_for_company_name_variation(browser, variation):
            if product_names_differ_too_much(company_dict["company_name"], product["manufacturer_name"], variation):
                continue
            elif countries_differ(company_dict, product["region"]):
                print("Warning: country looks different for this product, expected '%s' and got '%s'" % (translate_country_name(company_dict["country"]), product["region"]))
                pass

            sku = product["sku"]
            if not sku in company_products_found_in_search.keys():
                company_products_found_in_search[sku] = product
            else:
                #already added.. keep the entry with the longest search string hit, as that is assumed to be the most precise name
                old_entry = company_products_found_in_search[sku]
                if len(old_entry["company_search_page"]) < len(product["company_search_page"]):
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
            print("Skipping already processed company %s found in %s while resuming previous search" % (company_name, inputfile))

        if company_name == last_company_searched_for:
            is_adding = True

    return to_process, previously_searched_companies


def search_for_wines_and_write_results_file(company_and_name_variations_tuple, outputfile, is_resuming=False):
    all_companies = []

    if is_resuming:
        #TODO write every company to output file, even when there are no search results. That way we know better which companies have been searched for and not
        to_process_company_and_name_variations_tuple, previously_searched_companies = partition_by_previously_searched_companies(company_and_name_variations_tuple, outputfile)
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

            #Write the current list to file, to avoid losing all data in case of network/http server/other problems)
            f = open(outputfile, mode='w', encoding='utf-8')
            json.dump(all_companies, f, indent=2, ensure_ascii=False, sort_keys=True)
            f.flush()
            f.close()

        time.sleep(0.3) # Don't hammer website


if __name__ == "__main__":
    browser = webdriver.Firefox() # Get local session of firefox
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
        browser.close() #make sure to call close, or /tmp will fill up with large firefox session files
        raise exc
    finally:
        browser.close() #make sure to call close, or /tmp will fill up with large firefox session files
