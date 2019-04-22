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


import re


def pretty_format_grapes(product):
    value = product["Rastoff"].strip()
    withoutPercentages = re.sub(r'[0-9%]+', '', value).strip()
    return pretty_join(withoutPercentages.split(','), lowercase_tail=False)


def pretty_format_district(product):
    if "Øvrige" in product["Distrikt"]:
        return ""
    pretty_region = "fra {}".format(product["Distrikt"])
    if product["Underdistrikt"] and "Øvrige" not in product["Underdistrikt"]:
        pretty_region += " ({})".format(product["Underdistrikt"])

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
    company_name_from_vinmonopolet = next(iter(products))["Produsent"] if products else None
    for product in products:
        types.add(pretty_format_type(product))
        regions.add(pretty_format_region(product, subregion_count=1))
    types_list = pretty_join(types)
    regions_list = pretty_join(regions, lowercase_tail=False)
    print("<li>%s. %s. %s (%d varer i basisutvalget)</li>" % (
        company_name_from_vinmonopolet, types_list, regions_list, sort_by_product_count(company)))
print("</ul>")

print("<h2>Billig-liste</h2>")
print("<a name='billig'></a>")
print("<h3>De billigste veganske vinene</h3>")
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

print("<h3>Mest alkohol per krone</h3>")
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
    print("<h2>Veganske vinfirma på Vinmonopolet - %s</h2>" % filename)
    file = open(filename, encoding='utf-8')
    companies = json.loads(file.read())
    file.close()

    companies.sort(key=sort_by_company_name)
    products_by_country = {}
    for company_dict in companies:
        for product in company_dict["products_found_at_vinmonopolet"]:
            land = product["Land"]
            if not land in products_by_country:
                products_by_country[land] = []
            products_by_country[land].append((company_dict, product))

    print("<ul>")
    for country, products in products_by_country.items():
        print("<li><a href=#{}>{}</a></li>".format(country, country))
    print("</ul>")

    for country, products in products_by_country.items():
        print("<h3><a name='{}'>{}</a></h3>".format(country, country))
        products_by_type = {}
        for (company_dict, p) in products:
            type_name = pretty_format_type(p)
            if not type_name in products_by_type:
                products_by_type[type_name] = []
            products_by_type[type_name].append((company_dict, p))
        for product_type, products in products_by_type.items():
            print("<h4>{}</h4>".format(product_type))
            print("<ul>")
            for (company_dict, p) in products:
                isFairtrade = p["Fairtrade"] == "true"
                isOrganic = p["Okologisk"] == "true"
                isEco = p["Miljosmart_emballasje"] == "true"
                print("<li>{} - <a href='{}'>{}</a> {}. Laget på {}. {}{}{}. {} kr. <a href='{}'>[Barnivore]</a></li>".format(
                    p["Produsent"],
                    p["Vareurl"],
                    p["Varenavn"],
                    pretty_format_district(p),
                    pretty_format_grapes(p),
                    p["Produktutvalg"].replace("Basisutvalget", "<strong>Basisutvalget</strong>"),
                    ", fairtrade" if isFairtrade else "",
                    ", økologisk" if isOrganic else "",
                    ", miljøvennlig emballasje" if isEco else "",
                    p["Pris"],
                    company_dict['barnivore_url'])
                )
            print("</ul>")

print("</body></html>")
