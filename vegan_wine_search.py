#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import csv
import sys
import unicodedata
import string
from difflib import SequenceMatcher
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


def import_products_from_barnivore():
    companies = list()
    with open('wine.json', encoding='utf-8') as file:
        for candidate in json.loads(file.read()):
            candidate_company = candidate["company"]
            candidate_company['dev.countries'] = {translate_country_name(candidate_company['country'].lower(), candidate_company['id'])}
            companies.append(candidate_company)

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
        product["ProdusentSide"] = None  # mangler i exporten
        product["ProduktBilde"] = "https://bilder.vinmonopolet.no/cache/600x600-0/%s-1.jpg" % (row["Varenummer"])

        if product["Produktutvalg"] == "Partiutvalget" or product["Produktutvalg"] == "Testutvalget":
            # print("Skipping product that's not expected to stay in stores a while"))
            continue

        products.append(product)

    return products


def remove_diacritics(s):
    return ''.join(x for x in unicodedata.normalize('NFKD', s) if x in string.printable)


def lcs(cleanString1, cleanString2):
    matcher = SequenceMatcher(None, cleanString1, cleanString2)
    match = matcher.find_longest_match(0, len(cleanString1), 0, len(cleanString2))
    return match.size


def name_similarity(cleanString1, cleanString2):
    return SequenceMatcher(None, cleanString1, cleanString2).ratio() * 100


def get_stop_words(source_list):
    words = []
    for source in source_list:
        for product in source:
            normalized_company_name = normalize_name(product["company_name"])
            words += normalized_company_name.split(" ")

    different_words = set(words)
    stopword_count = int(15 * len(words) / len(different_words))  # heuristic

    counter = Counter()

    counter.update(words)
    dynamic_stopwords = set([word[0] for word in counter.most_common(stopword_count)])

    static_stopwords = {'aa', 'ab', 'abbazia', 'ag', 'alta', 'and', 'at', 'az,', 'azienda', 'bds', 'beer', 'beer house', 'bierbrouwerij', 'bieres', 'birra',
                        'birras', 'bodega', 'brasserie', 'brauerei', 'brew house', 'breweries', 'brewers', 'brewery', 'brewing', 'brouwerij', 'bryggeri',
                        'brygghus', 'bryghus', 'by', 'c', 'casa', 'casas', 'cellar', 'cellars', 'co', 'comp', 'compania', 'company', 'coop', 'corp', 'creek',
                        'crl', 'cspa', 'das', 'de', 'di', 'distillerie', 'do', 'dominio', 'du', 'e', 'el', 'estates', 'family', 'farm', 'fe', 'gmbh', 'gran',
                        'grand', 'group', 'grupo', 'hills', 'house', 'il', 'inc', 'incorporated', 'les', 'limited', 'limitee', 'llc', 'long', 'ltd', 'martin',
                        'merchant', 'monte', 'nuevo', 'of', 'plc', 'port', 'prod', 'productions', 'pty', 'ridge', 'royal', 'sa', 'sca', 'sl', 'soc',
                        'sociedade', 'sociedadsocieta', 'societe', 'spa', 'spanish', 'spirits', 'srl', 'ss', 'supermarkets', 'the', 'urban', 'valley', 'veuve',
                        'view', 'vignerons', 'vinedos', 'vineyard', 'vineyards', 'vinos', 'vintners', 'vit', 'viticultor', 'vitivinicola', 'weinbau',
                        'weinhaus', 'weinkellerei', 'wine', 'winemaker', 'wineries', 'winery', 'wines', 'winework', 'y'}

    abbreviation_dict = get_common_abbreviations()
    abbreviations = set([x.replace(".", "") for x in (abbreviation_dict.keys() | abbreviation_dict.values())])

    return static_stopwords | dynamic_stopwords | abbreviations


def add_normalized_names(company_list, stopwords):
    for company in company_list:
        company_name = company["company_name"]
        company["dev.normalized_name"] = normalize_name(replace_abbreviations(company_name))

        normalized_name = normalize_name(company_name)
        search_string_parts = [x for x in normalized_name.split(" ") if not x in stopwords]
        search_string = " ".join(search_string_parts)

        if not search_string or len(search_string) < 4:
            print("Warning: empty or very short name after normalization, using full search name instead, for {} ('{}')".format(company_name, normalized_name))
            search_string = normalized_name

        company["dev.search_string"] = search_string

    return company_list


def normalize_name(company_name):
    return remove_diacritics(company_name).strip().lower().replace(".", "").replace(",", "")


def get_common_abbreviations():
    common_abbreviations = {
        # poor man's abbreviation
        "domaine": "dom.",
        "chateau": "ch.",
        "agricola": "agr.",
        "weingut": "weing.",
        "bodegas": "bod.",
        "cantine": "cant.",
        "cantina": "cant.",
        "tenuta": "ten.",
        "vinicole": "vin.",
        "saint": "st.",
        "estate": "est.",
        "vigneron": "vign.",
        "castello": "cast.",
        "fattoria": "fatt.",
        "distillery": "dist.",
        "distilleria": "dist.",
        "fratelli": "f.lli",
        "doctor": "dr.",
        "poderi": "pod.",
        "marques": "marq.",
        "marchesi": "march.",
        "azienda agricola": "az.agr.",
        "brothers": "bros.",
        "sainte": "ste.",
        "societa' agricola": "soc.agr.",
        "societa agricola": "soc.agr.",
        "mount": "mt.",
        "gebruder": "gebr.",
        "champagne": "champ."
    }
    return common_abbreviations


def replace_abbreviations(word):
    if not word: return word

    try:
        return get_common_abbreviations()[word]
    except KeyError:
        return word


def translate_country_name(country, company_id):
    if not country: return country

    country_dict = {
        # poor man's translation to Norwegian
        "italy": "italia",
        "france": "frankrike",
        "germany": "tyskland",
        "spain": "spania",
        "austria": "østerrike",
        "norway": "norge",
        "sweden": "sverige",
        "denmark": "danmark",
        "netherlands": "nederland",
        "ireland": "irland",
        "belgium": "belgia",
        "greece": "hellas",
        "hungary": "ungarn",
        "croatia": "kroatia",
        "finland": "finland",
        "slovakia": "slovakia",
        "poland": "polen",
        "south africa": "sør-afrika",
        "usa": "usa",
        "england": "england",
        "chile": "chile",
        "united kingdom": "storbritannia",
        "argentina": "argentina",
        "israel": "israel",
        "mexico": "mexico",
        "luxembourg": "luxemburg",
        "switzerland": "sveits",
        "lebanon": "libanon",
        "malta": "malta",
        "slovenia": "slovenia",
        "montenegro": "montenegro",
        "tasmania": "tasmania",
        "cyprus": "kypros",
        "turkey": "turkia",
        "venezuela": "venezuela",
        "scotland": "scotland",
        "georgia": "georgia",
        "thailand": "thailand",
        "the netherlands": "nederland",
        "new zealand": "new zealand",
        "portugal": "portugal",
        "uruguay": "uruguay",
        "brazil": "brasil",
        "japan": "japan",
        "australia": "australia",
        "canada": "canada"
    }

    try:
        return country_dict[country]
    except KeyError:
        print("KeyError for country '{}' (company id {})".format(country, company_id))
        return country


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
        wine_companies.append({"company_name": name, "products_found_at_vinmonopolet": products,
                               "dev.countries": set([x["Land"].lower() for x in products])})

    return wine_companies


def possible_name_match(vegan_company, vinmonopolet_company):
    a_name = vegan_company["dev.search_string"]
    another_name = vinmonopolet_company["dev.search_string"]
    possible_name_match = lcs(a_name, another_name) >= 4 and name_similarity(a_name, another_name) > 85  # todo test if lcs actually helps, tweak thresholds

    return possible_name_match


def write_result_file(enriched_company_list, outputfile_all_vegan, outputfile_some_vegan):
    all_vegan_companies = []
    partly_vegan_companies = []
    for company in enriched_company_list:
        if "products_found_at_vinmonopolet" in company:
            company['dev.countries'] = list(company['dev.countries'])  # convert set to list for JSON serialization to work
            company['barnivore_url'] = "http://www.barnivore.com/wine/%s/company" % company['id']  # to simplify lookups later
            status = company["status"]
            if status == 'Has Some Vegan Options':
                partly_vegan_companies.append(company)
            elif (status == 'Vegan Friendly'):
                all_vegan_companies.append(company)

    # Write the current list to file, to avoid losing all data in case of network/http server/other problems)
    with open(outputfile_all_vegan, mode='w', encoding='utf-8') as f:
        json.dump(all_vegan_companies, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.flush()
    print("Found {} possible vegan wine company matches".format(len(all_vegan_companies)))

    # Write the current list to file, to avoid losing all data in case of network/http server/other problems)
    with open(outputfile_some_vegan, mode='w', encoding='utf-8') as f:
        json.dump(partly_vegan_companies, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.flush()
    print("Found {} possible matches for wine companies with some vegan options".format(len(partly_vegan_companies)))


def find_possible_company_matches(vegan_companies, wine_companies_at_vinmonopolet):
    for vegan_company in vegan_companies:
        vegan_company_name = vegan_company["company_name"]
        print("Searching for company '{}' ('{}') at Vinmonopolet...".format(vegan_company_name, vegan_company["dev.search_string"]))

        possible_name_matches = []
        for vinmonopolet_company in wine_companies_at_vinmonopolet:
            if possible_name_match(vegan_company, vinmonopolet_company):
                possible_name_matches.append(vinmonopolet_company)

        possible_matches = []
        for candidate in possible_name_matches:
            vinmonopolet_company_name = candidate["company_name"]
            if not candidate["dev.countries"]:
                print("Warning: no country data at vinmonopolet for company '{}'".format(vinmonopolet_company_name))
                possible_matches.append(candidate)
                continue

            if vegan_company["dev.countries"].isdisjoint(candidate["dev.countries"]):
                # If countries do not match, require a very close name match
                close_name_match = name_similarity(vegan_company["dev.search_string"], candidate["dev.search_string"]) > 90
                if close_name_match:
                    print("Warning: country mismatch for companies '{}' and '{}'".
                          format(vegan_company_name, vinmonopolet_company_name))
                    vegan_company["dev.country_mismatch"] = True  # Mark the entry for inspection
                    possible_matches.append(candidate)
                else:
                    print("Warning: ignoring match between companies '{}' and '{}', countries differ".format(vegan_company_name, vinmonopolet_company_name))
            else:
                possible_matches.append(candidate)

        if len(possible_matches) > 1:
            print("Multiple possible matches for company '{}':".format(vegan_company_name))
            for candidate in possible_matches:
                print("    '{}' ('{}' ≈ '{}')".format(candidate["company_name"],
                                                      vegan_company["dev.normalized_name"],
                                                      candidate["dev.normalized_name"]))

            best_candidate = None
            best_similarity_score = -1
            for candidate in possible_matches:
                similarity_score = name_similarity(vegan_company["dev.normalized_name"], candidate["dev.normalized_name"])
                if similarity_score > best_similarity_score:
                    best_candidate = candidate
                    best_similarity_score = similarity_score
                # todo OR - sort by similarity, and if top two matches are really close in similarity, do a tie break comparision

            print("Selected '{}' as the most closest match".format(best_candidate["company_name"]))
            vegan_company["products_found_at_vinmonopolet"] = best_candidate["products_found_at_vinmonopolet"]
        elif possible_matches:
            print("Possible match for company '{}' ('{}')".format(vegan_company_name, possible_matches[0]["company_name"]))
            vegan_company["products_found_at_vinmonopolet"] = possible_matches[0]["products_found_at_vinmonopolet"]

    return vegan_companies


if __name__ == "__main__":
    start = timer()

    products = import_products_from_vinmonopolet('produkter.csv')
    products = post_process_vinmonopolet_data(products)
    wine_companies_at_vinmonopolet = create_company_list_from_vinmonpolet(products)

    wine_companies_from_barnivore = import_products_from_barnivore()

    print("Using {} wine companies at Vinmonopolet, and {} listed in Barnivore".format(
        len(wine_companies_at_vinmonopolet), len(wine_companies_from_barnivore)))

    stopwords = get_stop_words([wine_companies_from_barnivore, wine_companies_at_vinmonopolet])
    wine_companies_at_vinmonopolet = add_normalized_names(wine_companies_at_vinmonopolet, stopwords)
    wine_companies_from_barnivore = add_normalized_names(wine_companies_from_barnivore, stopwords)

    vegan_companies_at_vinmonopolet = find_possible_company_matches(wine_companies_from_barnivore, wine_companies_at_vinmonopolet)

    write_result_file(wine_companies_from_barnivore, vegan_friendly_output_filename, some_vegan_products_output_filename)

    end = timer()
    print("Total time usage: {}s".format(int(end - start + 0.5)))
