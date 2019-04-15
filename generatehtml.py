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
    if not items:
        return None
    elif len(items) == 1:
        return next(iter(items))

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
    for product in company_dict["products_found_at_vinmonopolet"]:
        if "Basisutvalget" == product["Produktutvalg"]: number_in_basis_selection += 1
    return number_in_basis_selection


def sort_by_product_price(product_dict):
    price_raw = product_dict["Literpris"]  # eg. Kr. 106,53 pr. liter
    price_numeric = trim_non_numeric(price_raw)
    return int(price_numeric)  # eg 10653


import sys


def sort_by_trønder_kvotient(product_dict):
    try:
        price_raw = product_dict["Literpris"]  # eg. Kr. 106,53 pr. liter
        price_numeric = trim_non_numeric(price_raw)
        alchohol_percentage_raw = product_dict["Alkohol"]  # eg. 12,50
        alchohol_percentage_numeric = float(alchohol_percentage_raw)
        if product_dict["Varetype"].lower().find("alkoholfri") >= 0:
            # skip these products
            raise ValueError
        return int(price_numeric) * alchohol_percentage_numeric / 100.0
    except (KeyError, ValueError):
        return sys.maxsize


def trim_non_numeric(str):
    return "".join([x for x in str if x.isdigit()])


def sort_by_company_name(company_dict):
    values = company_dict["products_found_at_vinmonopolet"]
    if not values:
        # Allow companies without products at this point, we'll simply not print them later
        return ""
    return next(iter(values))["Produsent"]


print("""<html>
   <head>
       <meta charset='UTF-8'/>
   </head>
   <body>""")

total_product_count = 0
basisutvalg_count = 0
all_companies = []
for filename in ["vegan-friendly-searchresult-vinmonopolet.json", "some-vegan-options-searchresult-vinmonopolet.json"]:
    file = open(filename, encoding='utf-8')
    companies = json.loads(file.read())
    file.close()

    for company_dict in companies:
        products = company_dict["products_found_at_vinmonopolet"]

        if filename.find("some") >= 0:
            # Ignore some minor entries for "some vegan options" companies, for ease of manual post-processing
            basisutvalget = False
            for product in products:
                if product["Produktutvalg"] == "Basisutvalget":
                    basisutvalget = True
                    break
            if basisutvalget and len(products) > 1:
                total_product_count += len(products)
                all_companies.append(company_dict)
            for product in products:
                if product["Produktutvalg"] == "Basisutvalget": basisutvalg_count += 1
        else:
            total_product_count += len(products)
            for product in products:
                if product["Produktutvalg"] == "Basisutvalget": basisutvalg_count += 1
            all_companies.append(company_dict)

companies_with_the_most_products = list(all_companies)
companies_with_the_most_products.sort(key=sort_by_product_count, reverse=True)
print("<p>De merkene som er mest vanlige og lettest å finne på Vinmonopolet er:</p>")
print("<ul>")
for company in companies_with_the_most_products[:9]:
    types = set()
    regions = set()
    products = company["products_found_at_vinmonopolet"]
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

print("<h5>Billig-liste</h5>")
print("<a name='billig'></a>")
print("<h4>De billigste veganske vinene</h4>")
all_products = []
for company in all_companies:
    all_products += company["products_found_at_vinmonopolet"]

glass_flasker_i_basis = [x for x in all_products if x["Produktutvalg"] == "Basisutvalget"]

hvitvin = [x for x in glass_flasker_i_basis if x["Varetype"].lower().find("hvitvin") >= 0]
rødvin = [x for x in glass_flasker_i_basis if x["Varetype"].lower().find("rødvin") >= 0]
musserende = [x for x in glass_flasker_i_basis if x["Varetype"].lower().find("musserende") >= 0]
typer = {"Hvitvin": hvitvin, "Rødvin": rødvin, "Musserende vin": musserende}
for vintype, viner in typer.items():
    viner.sort(key=sort_by_product_price)
    print(vintype)
    print("<ul>")
    for i in range(0, min(len(viner), 3)):
        product = viner[i]
        print("<li><a href='%s'>%s</a>. %s fra %s produsert av %s (kr %s, %sL, %s)</li>" % (
            product["Vareurl"], product["Varenavn"], product["Varetype"], product["Land"], product["Produsent"],
            product["Pris"].lower(),
            product["Volum"].lower(),
            product["Emballasjetype"].lower())
        )
    print("</ul>")

print("<h4>Mest alkohol per krone</h4>")
all_products = []
for company in all_companies:
    all_products += company["products_found_at_vinmonopolet"]

hvitvin = [x for x in all_products if x["Varetype"].lower().find("hvitvin") >= 0]
rødvin = [x for x in all_products if x["Varetype"].lower().find("rødvin") >= 0]
musserende = [x for x in all_products if x["Varetype"].lower().find("musserende") >= 0]
typer = {"Hvitvin": hvitvin, "Rødvin": rødvin, "Musserende vin": musserende}

hvitvin.sort(key=sort_by_trønder_kvotient)
rødvin.sort(key=sort_by_trønder_kvotient)
musserende.sort(key=sort_by_trønder_kvotient)

for vintype, viner in typer.items():
    viner.sort(key=sort_by_product_price)
    print(vintype)
    print("<ul>")
    for i in range(0, min(len(viner), 3)):
        product = viner[i]
        print("<li><a href='%s'>%s</a>. %s fra %s produsert av %s (kr %s, %sL, %s)</li>" % (
            product["Vareurl"], product["Varenavn"], product["Varetype"], product["Land"], product["Produsent"],
            product["Pris"].lower(),
            product["Volum"].lower(),
            product["Emballasjetype"].lower())
              )
    print("</ul>")

print("<a name='liste'></a>")

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
        if not products:
            continue

        product_count = len(products)
        for product in products:
            names.add(product["Produsent"])
            regions.add(pretty_format_region(product, subregion_count=1))
            types.add(pretty_format_type(product))
            selections.add(product["Produktutvalg"])
            company_search_pages.add(product["ProdusentSide"])
        names = sorted(names)

        company_search_result_page = next(iter(company_search_pages))
        basisutvalget = "Basisutvalget" in selections

        if product_count < 2 and not basisutvalget:
            # skip these guys to simplify manual post processing of results
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
        for product in products:
            isFairtrade = product["Fairtrade"] == "true"
            print("<li>")  # begin product
            print(" <a href='%s'>%s</a> %s fra %s (%s%s)." % (
                product["Vareurl"],
                product["Varenavn"],
                pretty_format_type(product),
                pretty_format_region(product),
                product["Produktutvalg"].replace("Basisutvalget", "<strong>Basisutvalget</strong>"),
                ", Fairtrade" if isFairtrade else ""
            ))
            print("</li>")  # end product
        print("</ul>")  # end end product list
        print("</li>")  # end company

    print("</ul>")  # end category

print("</body></html>")
