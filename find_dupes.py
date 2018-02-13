#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from difflib import SequenceMatcher
import multiprocessing
import winestrings as wines


def sort_by_ratio(item):
    return item[0]


def import_products_from_vinmonopolet(wine_companies_at_vinmonopolet):
    wine_companies = set()
    company_id_map = {}
    for item in wine_companies_at_vinmonopolet:
        name = item["company_name"]
        wine_companies.add(name)
        company_id_map[name] = item["id"]

    return (wine_companies, company_id_map)


def compute_similarity(company_tuple):
    company, other_company = company_tuple
    ratio = SequenceMatcher(None, company, other_company).ratio()
    return (ratio, company, other_company)


def find_duplicates(wine_companies, id_map):
    dataset = set()
    for company in wine_companies:
        for other_company in wine_companies:
            if other_company == company:
                continue
            sorted_companies = sorted([company, other_company])
            company_tuple = (sorted_companies[0], sorted_companies[1])
            dataset.add(company_tuple)

    print("Comparing company names ({} combinations)..".format(len(dataset)))

    duplicates = []
    num_agents = multiprocessing.cpu_count() - 1 or 1
    chunk_size = int(len(dataset) / num_agents + 0.5)
    with multiprocessing.Pool(processes=num_agents) as pool:
        result = pool.map(compute_similarity, dataset, chunk_size)

        print("Sorting matches by similarity...")
        result.sort(key=sort_by_ratio, reverse=True)
        print("Similar company names:")
        for company in result:
            (ratio, company, other_company) = company
            if ratio > 0.9:
                id = id_map[company]
                other_company_id = id_map[other_company]
                duplicate_tuple = (company, id, other_company, other_company_id, ratio)
                duplicates.append(duplicate_tuple)
            else:
                break
    return duplicates


def import_products_from_barnivore(wine_companies_from_barnivore):
    wine_companies = set()
    company_id_map = {}
    for item in wine_companies_from_barnivore:
        name = item["company_name"]
        if not name in wine_companies:
            wine_companies.add(name)
            company_id_map[name] = item["id"]
        else:
            print("Identical company name: {} - id {} and {}".format(name,
                                                                     item["id"],
                                                                     company_id_map[name]))
            # print("Compare {} to {}".format("http://www.barnivore.com/wine/%s/company" %item["company"]["id"],
            #                                "http://www.barnivore.com/wine/%s/company" % company_id_map[name]))

    return (wine_companies, company_id_map)


def find_product_ids_by_company_id(id, wine_companies):
    product_ids = []
    for company in wine_companies:
        if company["id"] == id:
            for product in company["products_found_at_vinmonopolet"]:
                product_ids.append(product["Varenummer"])
    return product_ids


def find_company_name_by_id(id, wine_companies):
    for company in wine_companies:
        if company["id"] == id:
            return company["company_name"]
    return None


if __name__ == "__main__":
    wine_companies_from_barnivore = wines.load_wine_companies_from_barnivore("wine.json")[0:100]
    barnivore_companies, barnivore_id_map = import_products_from_barnivore(wine_companies_from_barnivore)
    barnivore_companies_normalized = [wines.normalize_name(wines.replace_abbreviations(x)) for x in barnivore_companies]
    barnivore_id_map_normalized = {}
    for key, value in barnivore_id_map.items():
        barnivore_id_map_normalized[wines.normalize_name(wines.replace_abbreviations(key))] = value
    print("Found {} wine companies at Barnivore".format(len(barnivore_companies_normalized)))
    print("Possible duplicate wine companies at Barnivore:")
    duplicates = find_duplicates(barnivore_companies_normalized, barnivore_id_map_normalized)
    for (company, id, other_company, other_company_id, ratio) in duplicates:
        print("{} ({}) ~ {} ({}) - {:.3f}".format(
            company, id, other_company, other_company_id, ratio))

    print("\n\n")
    wine_companies_at_vinmonopolet = wines.load_wine_companies_from_vinmonopolet("produkter.csv")
    vinmonopolet_companies, vinmonopolet_id_map = import_products_from_vinmonopolet(wine_companies_at_vinmonopolet)
    vinmonopolet_companies_normalized = [wines.normalize_name(wines.replace_abbreviations(x)) for x in vinmonopolet_companies]
    vinmonopolet_id_map_normalized = {}
    for key, value in vinmonopolet_id_map.items():
        vinmonopolet_id_map_normalized[wines.normalize_name(wines.replace_abbreviations(key))] = value
    print("Found {} wine companies at Vinmonopolet".format(len(vinmonopolet_companies)))
    print("Possible duplicate wine companies at Vinmonopolet:")
    duplicates = find_duplicates(vinmonopolet_companies_normalized, vinmonopolet_id_map_normalized)
    for (company, id, other_company, other_company_id, ratio) in duplicates:
        company_original_name = find_company_name_by_id(id, wine_companies_at_vinmonopolet)
        other_company_original_name = find_company_name_by_id(other_company_id, wine_companies_at_vinmonopolet)
        print("{} ({}) ~ {} ({}) - {:.3f}".format(company_original_name, id, other_company_original_name, other_company_id, ratio))
        company_skus = find_product_ids_by_company_id(id, wine_companies_at_vinmonopolet) \
                       + find_product_ids_by_company_id(other_company_id, wine_companies_at_vinmonopolet)
        print("   product ids = {}".format(sorted(company_skus)))
