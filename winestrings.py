#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata
import string
from difflib import SequenceMatcher
from collections import Counter
import json
import csv
import sys


def normalize_name(company_name):
    return remove_diacritics(company_name).strip().lower().replace(".", " ").replace(",", "").replace("-", " ").replace("  ", " ")


def get_common_abbreviations():
    common_abbreviations = {
        # poor man's abbreviation
        "domaine": "dom.",
        "domini": "dom.",
        "dominio": "dom.",
        "chateau": "ch.",
        "agricola": "agr.",
        "weingut": "weing.",
        "weingt": "weing.",
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
        "canada": "canada",
        'belgium': "belgia",
        'belize': "belize",
        'bermuda': "bermuda",
        'bulgaria': "bulgaria",
        'cayman islands': "caymanøyene",
        'china': "kina",
        'columbia': "kolombia",
        'costa rica': "costa rica",
        'czech republic': "tsjekkia",
        'dominican republic': 'den dominikanske republikk',
        'estonia': "estland",
        'ethiopia': "etiopia",
        'fiji': "fiji",
        'french guinea': "guinea",
        'guatemala': "guatemala",
        'hong kong': "hong kong",
        'iceland': "island",
        'india': "india",
        'isle of man': "man",
        'jamaica': "jamaica",
        'kenya': "kenya",
        'latvia': "latvia",
        'lithuania': "litauen",
        'malaysia': "malaysia",
        'namibia': "namibia",
        'northern ireland': "nord-irland",
        'palestine': "palestina",
        'philippines': "filipinene",
        'puerto rico': "puerto rico",
        'romania': "romania",
        'russia': "russland",
        'singapore': "singapore",
        'slovak republic': "slovakia",
        'south korea': "sør-korea",
        'taiwan': "taiwan"
    }

    try:
        return country_dict[country]
    except KeyError:
        print("KeyError for country '{}' (company id {})".format(country, company_id))
        return country


def remove_diacritics(s):
    return ''.join(x for x in unicodedata.normalize('NFKD', s) if x in string.printable)


def lcs(cleanString1, cleanString2):
    matcher = SequenceMatcher(None, cleanString1, cleanString2)
    match = matcher.find_longest_match(0, len(cleanString1), 0, len(cleanString2))
    return match.size


def name_similarity(cleanString1, cleanString2):
    return SequenceMatcher(None, cleanString1, cleanString2).ratio()


def get_stop_words(words):
    different_words = set(words)
    stopword_count = int(15 * len(words) / len(different_words))  # heuristic

    counter = Counter()

    counter.update(words)
    dynamic_stopwords = set([word[0] for word in counter.most_common(stopword_count)])

    static_stopwords = {'aa', 'ab', 'abbazia', 'ag', 'alta', 'at', 'az,', 'azienda', 'bds', 'beer house',
                        'bierbrouwerij', 'bieres', 'birra', 'birras', 'bodega', 'brew house', 'brewers', 'brygghus',
                        'bryghus', 'by', 'c', 'casa', 'casas', 'cellar', 'cellars', 'comp', 'compania', 'coop', 'corp',
                        'crl', 'cspa', 'das', 'dei', 'di', 'distillerie', 'do', 'du', 'e', 'el', 'estates', 'family',
                        'farm', 'fe', 'gran', 'grand', 'group', 'grupo', 'hills', 'il', 'inc', 'incorporated', 'les',
                        'limitee', 'long', 'martin', 'merchant', 'monte', 'nuevo', 'of', 'plc', 'port', 'prod',
                        'productions', 'pty', 'ridge', 'royal', 'sa', 'sca', 'sl', 'soc', 'sociedade',
                        'sociedadsocieta', 'societe', 'spa', 'spanish', 'spirits', 'srl', 'ss', 'supermarkets', 'urban',
                        'veuve', 'view', 'vignerons', 'vinedos', 'vineyard', 'vineyards', 'vinos', 'vintners', 'vit',
                        'viticultor', 'vitivinicola', 'weinbau', 'weinhaus', 'weinkellerei', 'wine', 'winemaker',
                        'wineries', 'wines', 'winework', 'y'}

    abbreviation_dict = get_common_abbreviations()
    abbreviations = set([x.replace(".", "") for x in (abbreviation_dict.keys() | abbreviation_dict.values())])

    return static_stopwords | dynamic_stopwords | abbreviations


def create_company_list_from_vinmonpolet(products):
    companies_temp = {}
    for product in products:
        produsent = product["Produsent"]
        if not produsent in companies_temp:
            companies_temp[produsent] = []
        companies_temp[produsent].append(product)

    companies = []
    company_id_counter = 0
    for name, products in companies_temp.items():
        # Using the same structure as Barnivore's json export, for simplicity
        companies.append(
            {"company_name": name,
             "id": company_id_counter,
             "products_found_at_vinmonopolet": products,
             "dev.countries": set([x["Land"].lower() for x in products])
             })
        company_id_counter += 1

    return companies


def import_products_from_vinmonopolet(filename):
    with open(filename, 'r', newline='', encoding='iso-8859-1') as csvfile:
        cvs_reader = csv.DictReader(csvfile, delimiter=';')
        try:
            return list(cvs_reader)  # read it all into memory
        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(filename, cvs_reader.line_num, e))


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


def load_companies_from_barnivore(filename):
    companies = list()
    with open(filename, encoding='utf-8') as file:
        for candidate in json.loads(file.read()):
            candidate_company = candidate["company"]
            candidate_company['dev.countries'] = {translate_country_name(candidate_company['country'].lower(), candidate_company['id'])}
            companies.append(candidate_company)

    return companies


def load_wine_companies_from_vinmonopolet(filename):
    products = load_vinmonopolet_data(filename)
    wine_products = [x for x in products if "vin" in x["Varetype"] or "Champagne" in x["Varetype"]]

    return create_company_list_from_vinmonpolet(wine_products)


def load_beer_companies_from_vinmonopolet(filename):
    products = load_vinmonopolet_data(filename)
    beer_products = [x for x in products if "ale" in x["Varetype"].lower()
                     or "lager" in x["Varetype"].lower()
                     or "kloster" in x["Varetype"].lower()
                     or "øl" in x["Varetype"].lower()
                     or "porter" in x["Varetype"].lower()
                     or "stout" in x["Varetype"].lower()
                     or "bitter" in x["Varetype"].lower()
                     or "barley" in x["Varetype"].lower()
                     ]

    return create_company_list_from_vinmonpolet(beer_products)

def load_spirits_companies_from_vinmonopolet(filename):
    products = load_vinmonopolet_data(filename)

    spirits_products = [x for x in products if
                        "Akevitt" in x["Varetype"]
                        or "Gin" in x["Varetype"]
                        or "Madeira" in x["Varetype"]
                        or "Rom" in x["Varetype"]
                        or "Sake" in x["Varetype"]
                        or "Sherry" in x["Varetype"]
                        or "Vermut" in x["Varetype"]
                        or "Likør" in x["Varetype"]
                        or "Genever" in x["Varetype"]
                        or "Vodka" in x["Varetype"]
                        or "Whisky" in x["Varetype"]
                        ]

    return create_company_list_from_vinmonpolet(spirits_products)


def load_vinmonopolet_data(filename):
    products = import_products_from_vinmonopolet(filename)
    products = post_process_vinmonopolet_data(products)
    return products


def get_normalized_company_names(source_list):
    words = []
    for source in source_list:
        for product in source:
            normalized_company_name = normalize_name(product["company_name"])
            words += normalized_company_name.split(" ")
    return words


def create_stopword_list(companies_from_barnivore, companies_at_vinmonopolet):
    company_names = get_normalized_company_names([companies_from_barnivore, companies_at_vinmonopolet])
    return get_stop_words(company_names)


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
