#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import sys
import json
from difflib import SequenceMatcher
import multiprocessing
import winestrings as wines


def sort_by_ratio(item):
    return item[0]


def import_products_from_vinmonopolet(filename):
    with open(filename, 'r', newline='', encoding='iso-8859-1') as csvfile:
        wine_reader = csv.DictReader(csvfile, delimiter=';')
        try:
            products = list(wine_reader)  # read it all into memory
            wine_products = [x for x in products if "vin" in x["Varetype"] or "Champagne" in x["Varetype"]]
            wine_companies = set()
            sku_map = {}
            for product in wine_products:
                name = product["Produsent"]
                wine_companies.add(name)
                sku_map[name] = product["Varenummer"]
            return (wine_companies, sku_map)

        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(filename, wine_reader.line_num, e))


def compute_similarity(company_tuple):
    company, other_company = company_tuple
    ratio = SequenceMatcher(None, company, other_company).ratio()
    return (ratio, company, other_company)


def report_duplicates(wine_companies, id_map):
    dataset = set()
    for company in wine_companies:
        for other_company in wine_companies:
            if other_company == company:
                continue
            sorted_companies = sorted([company, other_company])
            company_tuple = (sorted_companies[0], sorted_companies[1])
            dataset.add(company_tuple)

    print("Comparing company names ({} combinations)..".format(len(dataset)))

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
                print("{} ({}) ~ {} ({}) - {:.3f}".format(
                    company, id, other_company, other_company_id, ratio))
            else:
                break


def import_products_from_barnivore(filename):
    with open(filename, encoding='utf-8') as file:
        wine_companies = set()
        company_id_map = {}
        for item in json.loads(file.read()):
            name = item["company"]["company_name"]
            if not name in wine_companies:
                wine_companies.add(name)
                company_id_map[name] = item["company"]["id"]
            else:
                print("Identical company name: {} - id {} and {}".format(name,
                                                                         item["company"]["id"],
                                                                         company_id_map[name]))
                # print("Compare {} to {}".format("http://www.barnivore.com/wine/%s/company" %item["company"]["id"],
                #                                "http://www.barnivore.com/wine/%s/company" % company_id_map[name]))

        return (wine_companies, company_id_map)


if __name__ == "__main__":
    barnivore_companies, barnivore_id_map = import_products_from_barnivore("wine.json")
    barnivore_companies_normalized = [wines.normalize_name(wines.replace_abbreviations(x)) for x in barnivore_companies]
    barnivore_id_map_normalized = {}
    for key, value in barnivore_id_map.items():
        barnivore_id_map_normalized[wines.normalize_name(wines.replace_abbreviations(key))] = value
    print("Found {} wine companies at Barnivore".format(len(barnivore_companies_normalized)))
    print("Possible duplicate wine companies at Barnivore:")
    report_duplicates(barnivore_companies_normalized, barnivore_id_map_normalized)

    print("\n\n")
    vinmonopolet_companies, vinmonopolet_id_map = import_products_from_vinmonopolet("produkter.csv")
    vinmonopolet_companies_normalized = [wines.normalize_name(wines.replace_abbreviations(x)) for x in vinmonopolet_companies]
    vinmonopolet_id_map_normalized = {}
    for key, value in vinmonopolet_id_map.items():
        vinmonopolet_id_map_normalized[wines.normalize_name(wines.replace_abbreviations(key))] = value
    print("Found {} wine companies at Vinmonopolet".format(len(vinmonopolet_companies)))
    print("Possible duplicate wine companies at Vinmonopolet:")
    report_duplicates(vinmonopolet_companies_normalized, vinmonopolet_id_map_normalized)
