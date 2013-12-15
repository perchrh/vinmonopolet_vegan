#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json


def pretty_format_region(product, subregion_count=2):
    return ",".join(product["region"].split(",")[:subregion_count]).replace(", Øvrige", "").replace(", Champagne", "")


def pretty_format_type(product):
    return product["type"].split()[0].replace("Champ.", "Champagne")


def pretty_join(items, lowercase_tail=True):
    if len(items) == 1: return next(iter(items))

    item_list = list(items)
    modified_list = []
    modified_list.append(item_list[0])
    if lowercase_tail:
        for item in [t.lower() for t in item_list[1:]]: modified_list.append(item)
    else:
        for item in item_list[1:]: modified_list.append(item)

    first_part = ", ".join(modified_list[:-1])
    return "%s og %s" % (first_part, modified_list[-1])


def sort_by_product_count(company_dict):
    number_in_basis_selection = 0
    for product in company_dict["products_found_at_vinmonopolet"].values():
        if "Basisutvalg" == product["selection"]: number_in_basis_selection += 1
    return number_in_basis_selection


def sort_by_company_name(company_dict):
    return next(iter(company_dict["products_found_at_vinmonopolet"].values()))["manufacturer_name"]


total_product_count = 0
basisutvalg_count = 0
all_companies = []
for filename in ["vegan-friendly-searchresult-vinmonopolet.json", "some-vegan-options-searchresult-vinmonopolet.json"]:
    file = open(filename, encoding='utf-8')
    companies = json.loads(file.read())
    file.close()

    for company_dict in companies:
        products = company_dict["products_found_at_vinmonopolet"]
        total_product_count += len(products)
        for product in products.values():
            if product["selection"] == "Basisutvalg": basisutvalg_count += 1
        all_companies.append(company_dict)

companies_with_the_most_products = list(all_companies)
companies_with_the_most_products.sort(key=sort_by_product_count, reverse=True)
print("<p>De merkene som er mest vanlige og lettest å finne på Vinmonopolet er:</p>")
print("<ul>")
for company in companies_with_the_most_products[:9]:
    types = set()
    regions = set()
    products = company["products_found_at_vinmonopolet"].values()
    company_link = next(iter(products))["company_search_page"] if products else None
    company_name_from_vinmonopolet = next(iter(products))["manufacturer_name"] if products else None
    for product in products:
        types.add(pretty_format_type(product))
        regions.add(pretty_format_region(product, subregion_count=1))
    types_list = pretty_join(types)
    regions_list = pretty_join(regions, lowercase_tail=False)
    print("<li><a href='%s'>%s</a>. %s. %s (%d varer)</li>" % (company_link, company_name_from_vinmonopolet, types_list, regions_list, sort_by_product_count(company)))
print("</ul>")

print("<p>Vinmonopolet har %d veganske viner fra %d produsenter. %d av disse vinene er i basisutvalget, som er ekstra lett å få tak i.</p>" % (
    total_product_count, len(all_companies), basisutvalg_count))

for filename in ["vegan-friendly-searchresult-vinmonopolet.json", "some-vegan-options-searchresult-vinmonopolet.json"]:
    print("<h5>Veganske vinfirma på Vinmonopolet - %s</h5>" % filename)
    file = open(filename, encoding='utf-8')
    companies = json.loads(file.read())
    file.close()

    print("<ul>")

    companies.sort(key=sort_by_company_name)

    for company_dict in companies:
        names = set()
        regions = set()
        types = set()
        selections = set()
        company_search_pages = set()

        products = company_dict["products_found_at_vinmonopolet"]
        product_count = len(products)
        for sku in products.keys():
            product = products[sku]
            names.add(product["manufacturer_name"])
            regions.add(pretty_format_region(product, subregion_count=1))
            types.add(pretty_format_type(product))
            selections.add(product["selection"])
            company_search_pages.add(product["company_search_page"])

        company_search_result_page = next(iter(company_search_pages))
        basisutvalg = "Basisutvalg" in selections

        print("<li><a href='%s'>%s</a>. %s. %s. %s fra %s." % (
            company_search_result_page, "; ".join(names), str(product_count) + " varer" if product_count > 1 else "1 vare",
            "<strong>Basisutvalg</strong>" if basisutvalg else "Bestillingsutvalg", pretty_join(types), pretty_join(regions, lowercase_tail=False)
        ))
        print("<ul>")
        for product in products.values():
            print("<li>%s. %s fra %s (%s) med varenummer <a href='%s'>%s</a>.</li>" % (
                product["product_name"],
                pretty_format_type(product),
                pretty_format_region(product),
                product["selection"].replace("Basisutvalg", "<strong>Basisutvalg</strong>"),
                product["product_page"],
                product["sku"]))
        print("</ul>")
        print("</li>")

    print("</ul>")

    #print skus for storage
    skus = set()
    for company_dict in companies:
        products = company_dict["products_found_at_vinmonopolet"]
        for sku in products.keys():
            skus.add(sku)
    print("<h6>SKUs</h6>")
    print("\n".join(skus))
    print("<br/>")
