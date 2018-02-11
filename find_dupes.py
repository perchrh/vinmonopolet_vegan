#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import sys
import json
from difflib import SequenceMatcher
import multiprocessing


def progress_bar(iteration, total, barLength=50):
    # Thanks to https://gist.github.com/azlux/7b8f449ac7fa308d45232c3a281be7bb
    percent = int(round((iteration / total) * 100))
    nb_bar_fill = int(round((barLength * percent) / 100))
    bar_fill = '#' * nb_bar_fill
    bar_empty = ' ' * (barLength - nb_bar_fill)
    sys.stdout.write("\r  [{0}] {1}%".format(str(bar_fill + bar_empty), percent))
    sys.stdout.flush()


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
            print("Found {} wine companies at Vinmonopolet".format(len(wine_companies)))
            report_duplicates(wine_companies, sku_map)

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

        report_duplicates(wine_companies, company_id_map)


if __name__ == "__main__":
    print("Possible duplicate wine companies at Barnivore:")
    import_products_from_barnivore("wine.json")

    print("\n\n")
    print("Possible duplicate wine companies at Vinmonopolet:")
    import_products_from_vinmonopolet("produkter.csv")
