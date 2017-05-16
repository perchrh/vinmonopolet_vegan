#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json


def pretty_format_region(product, subregion_count=2):
    pretty_region = product["Land"]
    if subregion_count > 1 and product["Distrikt"]:
        pretty_region += ", " + product["Distrikt"]
    if subregion_count > 2 and product["Underdistrikt"]:
        pretty_region += ", " + product["Underdistrikt"]

    return pretty_region


def pretty_format_type(product):
    return product["Varetype"].split()[0].replace("Champ.", "Champagne")


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
        if "Basisutvalget" == product["Utvalg"]: number_in_basis_selection += 1
    return number_in_basis_selection


def sort_by_company_name(company_dict):
    return next(iter(company_dict["products_found_at_vinmonopolet"].values()))["Produsent"]


total_product_count = 0
basisutvalg_count = 0
all_companies = []
for filename in ["vegan-friendly-searchresult-vinmonopolet.json", "some-vegan-options-searchresult-vinmonopolet.json"]:
    file = open(filename, encoding='utf-8')
    companies = json.loads(file.read())
    file.close()

    for company_dict in companies:
        products = company_dict["products_found_at_vinmonopolet"]
        if filename.find("some") >=0:
            # Ignore some entries for "some vegan options" companies
            basisutvalget = False
            for product in products.values():
                if product["Utvalg"] == "Basisutvalget":
                    basisutvalget = True
                    break
            if basisutvalget and len(products) > 1:
                total_product_count += len(products)
                all_companies.append(company_dict)
        else:
            total_product_count += len(products)
            for product in products.values():
                if product["Utvalg"] == "Basisutvalget": basisutvalg_count += 1
            all_companies.append(company_dict)

companies_with_the_most_products = list(all_companies)
companies_with_the_most_products.sort(key=sort_by_product_count, reverse=True)
print("<p>De merkene som er mest vanlige og lettest å finne på Vinmonopolet er:</p>")
print("<ul>")
for company in companies_with_the_most_products[:9]:
    types = set()
    regions = set()
    products = company["products_found_at_vinmonopolet"].values()
    company_link = next(iter(products))["ProdusentSide"] if products else None
    company_name_from_vinmonopolet = next(iter(products))["Produsent"] if products else None
    for product in products:
        types.add(pretty_format_type(product))
        regions.add(pretty_format_region(product, subregion_count=1))
    types_list = pretty_join(types)
    regions_list = pretty_join(regions, lowercase_tail=False)
    print("<li><a href='%s'>%s</a>. %s. %s (%d varer i basisutvalget)</li>" % (
    company_link, company_name_from_vinmonopolet, types_list, regions_list, sort_by_product_count(company)))
print("</ul>")

print(
    "<p>Vinmonopolet har %d veganske viner fra %d produsenter. %d av disse vinene er i basisutvalget, som er ekstra lett å få tak i.</p>" % (
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
        company_url = company_dict['barnivore_url']
        company_name = company_dict['company_name']

        products = company_dict["products_found_at_vinmonopolet"]
        product_count = len(products)
        for sku in products.keys():
            product = products[sku]
            names.add(product["Produsent"])
            regions.add(pretty_format_region(product, subregion_count=1))
            types.add(pretty_format_type(product))
            selections.add(product["Utvalg"])
            company_search_pages.add(product["ProdusentSide"])
        names = sorted(names)

        company_search_result_page = next(iter(company_search_pages))
        basisutvalget = "Basisutvalget" in selections

        if filename.find("some") >=0 and (not basisutvalget or product_count < 2):
            # Ignoring producers with only some vegan options and nothing in Basisutvalget
            continue

        print("<li>")  # begin company
        print("<a href='%s'>%s</a>. %s. %s. %s fra %s. <a href='%s'>[Barnivore]</a>" % (
            company_search_result_page,
            "; ".join(names),
            str(product_count) + " varer" if product_count > 1 else "1 vare",
            "<strong>Basisutvalget</strong>" if basisutvalget else "Bestillingsutvalget",
            pretty_join(types),
            pretty_join(regions, lowercase_tail=False),
            company_url
        ))
        print("<ul>")  # begin product list
        for product in products.values():
            print("<li>")  # begin product
            print("%s. %s fra %s (%s) med varenummer <a href='%s'>%s</a>." % (
                product["Produktnavn"],
                pretty_format_type(product),
                pretty_format_region(product),
                product["Utvalg"].replace("Basisutvalget", "<strong>Basisutvalget</strong>"),
                product["Produktside"],
                product["Varenummer"]))
            print("</li>")  # end product
        print("</ul>")  # end end product list
        print("</li>")  # end company

    print("</ul>")  # end category

    # print skus for storage
    skus = set()
    for company_dict in companies:
        products = company_dict["products_found_at_vinmonopolet"]
        for sku in products.keys():
            skus.add(sku)
    print("<h6>SKUs</h6>")
    print("\n".join(skus))
    print("<br/>")
