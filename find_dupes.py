import csv
import sys
import json
from difflib import SequenceMatcher


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


def report_duplicates(wine_companies, id_map):
    matches = []
    counter = 0
    target_count = int(0.5 * len(wine_companies) ** 2)
    processed_combinations = set()
    print("Comparing company names ({} combinations)".format(target_count))
    for company in wine_companies:
        for other_company in wine_companies:
            if id_map[company] == id_map[other_company]:
                # same entry
                continue
            compared_companies = sorted([company, other_company])
            if (compared_companies[0], compared_companies[1]) in processed_combinations:
                # same combination
                continue

            ratio = SequenceMatcher(None, company, other_company).ratio()
            matches.append((ratio, company, other_company))
            counter += 1

            progress_bar(counter, target_count, 50)

            processed_combinations.add((compared_companies[0], compared_companies[1]))
    print("\n")

    print("Sorting matches...")
    matches.sort(key=sort_by_ratio, reverse=True)
    five_percent = int(0.5 + len(matches) * 0.05)
    print("Top 5% most similar wine company names")
    for i in range(0, five_percent):
        (ratio, company, other_company) = matches[i]
        id = id_map[company]
        other_company_id = id_map[other_company]
        if ratio > 0.9:
            print("{} ({}) ~ {} ({}) - {:.3f}".format(
                company, id, other_company, other_company_id, ratio))


def import_products_from_barnivore(filename):
    with open(filename, encoding='utf-8') as file:
        wine_companies = set()
        company_id_map = {}
        for item in json.loads(file.read()):
            name = item["company"]["company_name"]
            wine_companies.add(name)
            company_id_map[name] = item["company"]["id"]

        report_duplicates(wine_companies, company_id_map)


if __name__ == "__main__":
    print("Possible duplicate wine companies at Barnivore:")
    import_products_from_barnivore("wine.json")

    print("Possible duplicate wine companies at Vinmonopolet:")
    import_products_from_vinmonopolet("produkter.csv")
