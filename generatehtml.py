#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json


def pretty_format_region(product, subregion_count=2):
    return ",".join(product["region"].split(",")[:subregion_count]).replace(", Øvrige", "")


def sort_by_product_count(company_dict):
    number_in_basis_selection = 0
    for product in company_dict["products_found_at_vinmonopolet"].values():
        if "Basisutvalg" == product["selection"]: number_in_basis_selection += 1
    return number_in_basis_selection


for filename in ["vegan-friendly-searchresult-vinmonopolet.json", "some-vegan-options-searchresult-vinmonopolet.json"]:
    print("<h1>Veganske vinfirma på Vinmonopolet - %s</h1>" % filename)
    file = open(filename, encoding='utf-8')
    companies = json.loads(file.read())
    file.close()

    total_product_count = 0
    basisutvalg_count = 0
    for company_dict in companies:
        products = company_dict["products_found_at_vinmonopolet"]
        total_product_count += len(products)
        for product in products.values():
            if product["selection"] == "Basisutvalg": basisutvalg_count += 1

    print("<p>Vinmonopolet har %d veganske viner fra %d produsenter. %d av disse er i basisutvalget.</p>" % (total_product_count, len(companies), basisutvalg_count))

    companies_with_the_most_products = list(companies)
    companies_with_the_most_products.sort(key=sort_by_product_count, reverse=True)
    print("<p>De merkene som er mest vanlige og lettest å finne på Vinmonopolet er:</p>")
    print("<ul>")
    for company in companies_with_the_most_products[:9]:
        types = set()
        regions = set()
        products = company["products_found_at_vinmonopolet"].values()
        for product in products:
            types.add(product["type"])
            regions.add(pretty_format_region(product, subregion_count=1))
        types_list = " og ".join(types)
        regions_list = " og ".join(regions)
        print("<li>%s. %s. %s (%d varer)</li>" % (company["company_name"], types_list, regions_list, len(products)))
    print("</ul>")

    print("<ul>")

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
            regions.add(pretty_format_region(product))
            types.add(product["type"].split()[0])
            selections.add(product["selection"])
            company_search_pages.add(product["company_search_page"])

        company_search_result_page = next(iter(company_search_pages))
        basisutvalg = "Basisutvalg" in selections

        print("<li><a href='%s'>%s</a>. %s. %s. %s fra %s." % (
            company_search_result_page, "; ".join(names), str(product_count) + " varer" if product_count > 1 else "1 vare",
            "<strong>Basisutvalg</strong>" if basisutvalg else "Bestillingsutvalg", " og ".join(types), "; ".join(regions)
        ))
        print("<ul>")
        for product in products.values():
            print("<li>%s. %s fra %s (%s) med varenummer <a href='%s'>%s</a>.</li>" % (
                product["product_name"],
                product["type"],
                pretty_format_region(product),
                product["selection"].replace("Basisutvalg", "<strong>Basisutvalg</strong>"),
                product["product_page"],
                product["sku"]))
        print("</ul>")
        print("</li>")

    print("</ul>")
