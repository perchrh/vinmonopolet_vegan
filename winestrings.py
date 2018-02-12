#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata
import string
from difflib import SequenceMatcher
from collections import Counter


def normalize_name(company_name):
    return remove_diacritics(company_name).strip().lower().replace(".", " ").replace(",", "").replace("-", " ")


def get_common_abbreviations():
    common_abbreviations = {
        # poor man's abbreviation
        "domaine": "dom.",
        "domini": "dom.",
        "dominio": "dom.",
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
        "champ.": "ch.",  # abbreviate the abbreviation!
        "champagne": "ch."
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

    static_stopwords = {'aa', 'ab', 'abbazia', 'ag', 'alta', 'and', 'at', 'az,', 'azienda', 'bds', 'beer', 'beer house',
                        'bierbrouwerij', 'bieres', 'birra',
                        'birras', 'bodega', 'brasserie', 'brauerei', 'brew house', 'breweries', 'brewers', 'brewery',
                        'brewing', 'brouwerij', 'bryggeri',
                        'brygghus', 'bryghus', 'by', 'c', 'casa', 'casas', 'cellar', 'cellars', 'co', 'comp',
                        'compania', 'company', 'coop', 'corp', 'creek',
                        'crl', 'cspa', 'das', 'de', 'di', 'distillerie', 'do', 'du', 'e', 'el', 'estates', 'family',
                        'farm', 'fe', 'gmbh', 'gran',
                        'grand', 'group', 'grupo', 'hills', 'house', 'il', 'inc', 'incorporated', 'les', 'limited',
                        'limitee', 'llc', 'long', 'ltd', 'martin',
                        'merchant', 'monte', 'nuevo', 'of', 'plc', 'port', 'prod', 'productions', 'pty', 'ridge',
                        'royal', 'sa', 'sca', 'sl', 'soc',
                        'sociedade', 'sociedadsocieta', 'societe', 'spa', 'spanish', 'spirits', 'srl', 'ss',
                        'supermarkets', 'the', 'urban', 'valley', 'veuve',
                        'view', 'vignerons', 'vinedos', 'vineyard', 'vineyards', 'vinos', 'vintners', 'vit',
                        'viticultor', 'vitivinicola', 'weinbau',
                        'weinhaus', 'weinkellerei', 'wine', 'winemaker', 'wineries', 'winery', 'wines', 'winework', 'y'}

    abbreviation_dict = get_common_abbreviations()
    abbreviations = set([x.replace(".", "") for x in (abbreviation_dict.keys() | abbreviation_dict.values())])

    return static_stopwords | dynamic_stopwords | abbreviations
