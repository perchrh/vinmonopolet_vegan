#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import csv
import sys
import unicodedata
import string
from difflib import SequenceMatcher
from functools import reduce
import operator
from collections import Counter
from timeit import default_timer as timer

vegan_friendly_output_filename = "vegan-friendly-searchresult-vinmonopolet.json"
some_vegan_products_output_filename = "some-vegan-options-searchresult-vinmonopolet.json"

def import_products_from_vinmonopolet(filename):
    with open(filename, 'r', newline='', encoding='iso-8859-1') as csvfile:
        wine_reader = csv.DictReader(csvfile, delimiter=';')
        try:
            return list(wine_reader)  # read it all into memory
        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(filename, wine_reader.line_num, e))


def import_products_from_barnivore(partialOnly):
    companies = list()
    with open('wine.json', encoding='utf-8') as file:
        for candidate in json.loads(file.read()):
            candidate['company']['dev.countries'] = {translate_country_name(candidate['company']['country'].lower())}
            status = candidate['company']['status']
            if (status == 'Has Some Vegan Options' and partialOnly) or (status == 'Vegan Friendly' and not partialOnly):
                companies.append(candidate)

    return companies


def post_process_vinmonopolet_data(export_data):
    products = []
    for row in export_data:
        # Headers are:
        # Datotid;Varenummer;Varenavn;Volum;Pris;Literpris;Varetype;Produktutvalg;Butikkategori;
        # Fylde;Friskhet;Garvestoffer;Bitterhet;Sodme;Farge;Lukt;Smak;Passertil01;Passertil02;Passertil03;
        # Land;Distrikt;Underdistrikt;
        # Argang;Rastoff;Metode;Alkohol;Sukker;Syre;Lagringsgrad;
        # Produsent;Grossist;Distributor;
        # Emballasjetype;Korktype;Vareurl

        product = row
        product["Lagerstatus"] = row["Produktutvalg"]  # mangler i exporten?
        product["ProdusentSide"] = None  # mangler i exporten?
        product["ProduktBilde"] = "https://bilder.vinmonopolet.no/cache/600x600-0/%s-1.jpg" % (product["Varenummer"])

        products.append(product)

    return products


def remove_diacritics(s):
    return ''.join(x for x in unicodedata.normalize('NFKD', s) if x in string.printable)


def lcs(S1, S2):
    cleanString1 = cleanString(S1)
    cleanString2 = cleanString(S2)
    matcher = SequenceMatcher(None, cleanString1, cleanString2)
    match = matcher.find_longest_match(0, len(cleanString1), 0, len(cleanString2))
    return match.size


def cleanString(S1):
    return S1.lower().strip()


def name_similarity(S1, S2):
    cleanString1 = cleanString(S1)
    cleanString2 = cleanString(S2)
    return SequenceMatcher(None, cleanString1, cleanString2).ratio() * 100


def get_stop_words(source_list):
    word_list_from_product_names = []
    for source in source_list:
        word_list_from_product_names += [x["company"]["company_name"].split(" ") for x in source]

    words = reduce(operator.concat, word_list_from_product_names)
    different_words = set(words)
    stopword_count = int(100 * len(different_words) / len(words))  # heuristic

    counter = Counter()

    counter.update(words)
    dynamic_stopwords = set([word[0] for word in counter.most_common(stopword_count)])

    static_stopwords = {'bryghus', 'fatt', 'saint', 'veuve', 'doctor', 'monte', 'cspa', 'vigneron', 'brewers',
                        'mount', 'cant', 'dr', 'the', 'distillery', 'il', 'bryggeri', 'e', 'distillerie', 'company',
                        'dom', 'royal', 'winemaker', 'weing', 'bierbrouwerij', 'grand', 'distilleria', 'el', 'birra',
                        'view', 'c', 'int', 'ridge', 'merchant', 'bros', 'grupo', 'coop', 'weingut', 'vintners', 'ab',
                        'vignerons', 'spanish', 'vin', 'estates', 'vineyards', 'di', 'house', 'dist', 'gebruder',
                        'est', 'corp', 'weinbau', 'international', 'weinkellerei', 'beer house', 'creek', 'at', 'by',
                        'cantina', 'weinhaus', 'and', 'supermarkets', 'de', 'brasserie', 'farm', 'port', 'winery',
                        'estate', 'family', 'of', 'comp', 'breweries', 'group', 'marq', 'ltd', 'spa', 'vineyard',
                        'bod', 'abbazia', 'chateau', 'les', 'st', 'beer', 'co', 'martin', 'az,', 'bodega', 'casas',
                        'gran', 'srl', 'fattoria', 'gebr', 'brothers', 'domaine', 'inc', 'brewing', 'do',
                        'viticultor', 'brauerei', 'champagne', 'brouwerij', 'casa', 'productions', 'bieres',
                        'marques', 'cellars', 'gmbh', 'bds', 'vinedos', 'nuevo', 'cast', 'llc', 'wineries', 'sl',
                        'brygghus', 'hills', 'y', 'urban', 'vitivinicola', 'winework', 'sca', 'valley', 'limited',
                        'plc', 'wine', 'du', 'birras', 'brewery', 'long', 'pty', 'dominio', 'sociedade', 'alta',
                        'compania', 'spirits', 'azienda', 'sa', 'vign', 'societa', 'champ', 'agricola', 'fe', 'ch',
                        'vinos', 'vinicole', 'cellar', 'brew house', 'ag', 'agr', 'das', 'cantine', 'wines'}

    return static_stopwords | dynamic_stopwords


def add_normalized_names(company_list, stopwords):
    for company in company_list:
        company_name = company["company"]["company_name"]
        name_parts = remove_diacritics(company_name).strip().lower().replace(".", "").replace(",", "").split(" ")
        normalized_name_parts = [x for x in name_parts if not x in stopwords and len(x) > 2]
        normalized_name = " ".join(normalized_name_parts)
        # print("original, normalized name = '{}', '{}'".format(company_name, normalized_name))
        if not normalized_name:
            print("Warning: empty name after normalization, using full name instead, for {}".format(company_name))
            normalized_name = " ".join(name_parts)
        company["company"]["dev.normalized_name"] = normalized_name

    return company_list


def translate_country_name(country):
    # poor man's translation to Norwegian
    return country.replace("italy", "italia"). \
        replace("france", "frankrike"). \
        replace("germany", "tyskland"). \
        replace("spain", "spania"). \
        replace("austria", "østerrike"). \
        replace("norway", "norge"). \
        replace("sweden", "sverige"). \
        replace("denmark", "danmark"). \
        replace("netherlands", "nederland"). \
        replace("ireland", "irland"). \
        replace("belgium", "belgia"). \
        replace("greece", "hellas"). \
        replace("hungary", "ungarn"). \
        replace("croatia", "kroatia"). \
        replace("finland", "finland"). \
        replace("austria", "østerrike"). \
        replace("slovakia", "slovakia"). \
        replace("poland", "polen"). \
        replace("south africa", "sør-afrika")


def create_company_list_from_vinmonpolet(products):
    wine_products = [x for x in products if "vin" in x["Varetype"] or "Champagne" in x["Varetype"]]

    wine_companies_temp = {}
    for product in wine_products:
        produsent = product["Produsent"]
        if not produsent in wine_companies_temp:
            wine_companies_temp[produsent] = []
            wine_companies_temp[produsent].append(product)

    wine_companies = []
    for name, products in wine_companies_temp.items():
        # Using the same structure as Barnivore's json export, for simplicity
        wine_companies.append({"company": {"company_name": name, "products_found_at_vinmonopolet": products,
                                           "dev.countries": set([x["Land"].lower() for x in products])}})

    return wine_companies


def possible_name_match(vegan_company, vinmonopolet_company):
    a_name = vegan_company["dev.normalized_name"]
    another_name = vinmonopolet_company["dev.normalized_name"]
    possible_name_match = lcs(a_name, another_name) > 4 and name_similarity(a_name, another_name) > 80
    if possible_name_match:
        if vegan_company["dev.countries"].isdisjoint(vinmonopolet_company["dev.countries"]):
            # If countries do not match, require a very close name match
            close_name_match = lcs(a_name, another_name) > 6 and name_similarity(a_name, another_name) > 90
            if close_name_match:
                print("Warning: country mismatch for companies '{}' and '{}'".
                      format(vegan_company["company_name"], vinmonopolet_company["company_name"]))
                vegan_company["dev.country_mismatch"] = True # Mark the entry for inspection
            return close_name_match

    return possible_name_match

def write_result_file(enriched_company_list, outputfile):
    all_companies = []
    for company in enriched_company_list:
        if "products_found_at_vinmonopolet" in company["company"]:
            company['company']['dev.countries'] = list(company['company']['dev.countries']) # convert set to list for JSON serialization to work
            all_companies.append(company)

    # Write the current list to file, to avoid losing all data in case of network/http server/other problems)
    with open(outputfile, mode='w', encoding='utf-8') as f:
        json.dump(all_companies, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.flush()

if __name__ == "__main__":
    start = timer()

    products = import_products_from_vinmonopolet('produkter.csv')
    products = post_process_vinmonopolet_data(products)

    wine_companies_at_vinmonopolet = create_company_list_from_vinmonpolet(products)
    vegan_companies = import_products_from_barnivore(False)

    stopwords = get_stop_words([vegan_companies, wine_companies_at_vinmonopolet])
    wine_companies_at_vinmonopolet = add_normalized_names(wine_companies_at_vinmonopolet, stopwords)
    vegan_companies = add_normalized_names(vegan_companies, stopwords)

    print("Found {} wine companies at Vinmonopolet, and {} listed in Barnivore".format(
        len(wine_companies_at_vinmonopolet), len(vegan_companies)))

    match_count = 0
    for vegan_company in vegan_companies:
        for vinmonopolet_company in wine_companies_at_vinmonopolet:
            if possible_name_match(vegan_company["company"], vinmonopolet_company["company"]):
                vegan_company_name = vegan_company["company"]["company_name"]
                vinmonopolet_company_name = vinmonopolet_company["company"]["company_name"]
                print("Possible match between '{}' and '{}' ('{}' ≈ '{}')'".format(vegan_company_name, vinmonopolet_company_name,
                                                                                  vegan_company["company"]["dev.normalized_name"],
                                                                                  vinmonopolet_company["company"]["dev.normalized_name"]))
                match_count += 1
                if "products_found_at_vinmonopolet" in vegan_company["company"]:
                    # Exists already. Overwrite the old entry if the new match is better
                    old_similarity = name_similarity(vegan_company_name, vegan_company["company"]["products_found_at_vinmonopolet"][0]["Produsent"])
                    new_similarity = name_similarity(vegan_company_name, vinmonopolet_company_name)
                    if new_similarity > old_similarity:
                        # Overwrite it
                        print("Warning overwrite of results for company {}".format(
                            vegan_company_name))
                        vegan_company["company"]["products_found_at_vinmonopolet"] = vinmonopolet_company["company"]["products_found_at_vinmonopolet"]
                else:
                    # Doesn't exist yet, just add it
                    vegan_company["company"]["products_found_at_vinmonopolet"] = vinmonopolet_company["company"]["products_found_at_vinmonopolet"]

    end = timer()
    print("Found {} possible company matches in {}s".format(match_count, int(end - start + 0.5)))

    write_result_file(vegan_companies, vegan_friendly_output_filename)
    print("Wrote results to {}".format(vegan_friendly_output_filename))
