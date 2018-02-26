#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from difflib import SequenceMatcher
import multiprocessing
import winestrings as wines


def sort_by_ratio(item):
    return item[0]


def import_products_from_vinmonopolet(companies_at_vinmonopolet):
    company_names = set()
    company_id_map = {}
    for item in companies_at_vinmonopolet:
        name = item["company_name"]
        company_names.add(name)
        company_id_map[name] = item["id"]

    return (company_names, company_id_map)


def compute_similarity(company_tuple):
    company, other_company = company_tuple
    ratio = SequenceMatcher(None, company, other_company).ratio()
    return (ratio, company, other_company)


def find_duplicates(companies, id_map):
    dataset = set()
    for company in companies:
        for other_company in companies:
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


def import_products_from_barnivore(companies):
    company_names = set()
    company_id_map = {}
    for item in companies:
        name = item["company_name"]
        if not name in company_names:
            company_names.add(name)
            company_id_map[name] = item["id"]
        else:
            print("Identical company name: {}".format(name))
            print("    http://www.barnivore.com/wine/{}/company".format(item["id"]))
            print("    http://www.barnivore.com/wine/{}/company".format(company_id_map[name]))

    return (company_names, company_id_map)


def find_product_ids_by_company_id(id, companies):
    product_ids = []
    for company in companies:
        if company["id"] == id:
            for product in company["products_found_at_vinmonopolet"]:
                product_ids.append(product["Varenummer"])
    return product_ids


def find_company_name_by_id(id, companies):
    for company in companies:
        if company["id"] == id:
            return company["company_name"]
    return None


if __name__ == "__main__":
    companies_from_barnivore = wines.load_companies_from_barnivore("wine.json")
    barnivore_companies, barnivore_id_map = import_products_from_barnivore(companies_from_barnivore)
    barnivore_companies_normalized = [wines.normalize_name(wines.replace_abbreviations(x)) for x in barnivore_companies]
    barnivore_id_map_normalized = {}
    for key, value in barnivore_id_map.items():
        barnivore_id_map_normalized[wines.normalize_name(wines.replace_abbreviations(key))] = value
    print("Found {} companies at Barnivore".format(len(barnivore_companies_normalized)))
    print("Possible duplicate companies at Barnivore:")
    duplicates = find_duplicates(barnivore_companies_normalized, barnivore_id_map_normalized)
    for (company, id, other_company, other_company_id, ratio) in duplicates:
        company_original_name = find_company_name_by_id(id, companies_from_barnivore)
        other_company_original_name = find_company_name_by_id(other_company_id, companies_from_barnivore)
        print("{} ({}) ~ {} ({}) - {:.3f}".format(company_original_name, id, other_company_original_name,
                                                  other_company_id, ratio))
        print("    http://www.barnivore.com/wine/{}/company".format(id))
        print("    http://www.barnivore.com/wine/{}/company".format(other_company_id))

    print("\n\n")
    companies_at_vinmonopolet = wines.load_wine_companies_from_vinmonopolet("produkter.csv")
    vinmonopolet_companies, vinmonopolet_id_map = import_products_from_vinmonopolet(companies_at_vinmonopolet)
    vinmonopolet_companies_normalized = [wines.normalize_name(wines.replace_abbreviations(x)) for x in vinmonopolet_companies]
    vinmonopolet_id_map_normalized = {}
    for key, value in vinmonopolet_id_map.items():
        vinmonopolet_id_map_normalized[wines.normalize_name(wines.replace_abbreviations(key))] = value
    print("Found {} companies at Vinmonopolet".format(len(vinmonopolet_companies)))
    print("Possible duplicate companies at Vinmonopolet:")
    duplicates = find_duplicates(vinmonopolet_companies_normalized, vinmonopolet_id_map_normalized)
    for (company, id, other_company, other_company_id, ratio) in duplicates:
        company_original_name = find_company_name_by_id(id, companies_at_vinmonopolet)
        other_company_original_name = find_company_name_by_id(other_company_id, companies_at_vinmonopolet)
        print("{} ({}) ~ {} ({}) - {:.3f}".format(company_original_name, id, other_company_original_name, other_company_id, ratio))
        company_skus = find_product_ids_by_company_id(id, companies_at_vinmonopolet) \
                       + find_product_ids_by_company_id(other_company_id, companies_at_vinmonopolet)
        print("   product ids = {}".format(sorted(company_skus)))
