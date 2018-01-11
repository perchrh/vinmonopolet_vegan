def import_products_from_vinmonopolet(filename):
    import csv
    import sys
    with open(filename, 'r', newline='', encoding='iso-8859-1') as csvfile:
        wine_reader = csv.DictReader(csvfile, delimiter=';')
        try:
            return list(wine_reader)  # read it all into memory
        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(filename, wine_reader.line_num, e))


def import_products_from_barnivore(partialOnly):
    import json
    companies = list()
    with open('wine.json', encoding='utf-8') as file:
        for candidate in json.loads(file.read()):
            candidate['company']['dev.countries'] = {translate_country_name(candidate['company']['country'].lower())}
            status = candidate['company']['status']
            if (status == 'Has Some Vegan Options' and partialOnly) or (status == 'Vegan Friendly' and not partialOnly):
                companies.append(candidate)

    return companies


def post_process_vinmonopolet_data(export_data):
    import dateutil.parser

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
        product["Datotid"] = dateutil.parser.parse(row["Datotid"].replace(";", "."))
        product["ProdusentSide"] = None  # mangler i exporten?
        product["ProduktBilde"] = "https://bilder.vinmonopolet.no/cache/600x600-0/%s-1.jpg" % (product["Varenummer"])

        products.append(product)

    return products


import unicodedata
import string


def remove_diacritics(s):
    return ''.join(x for x in unicodedata.normalize('NFKD', s) if x in string.printable)


from difflib import SequenceMatcher


def LongestCommonSubstringSize(S1, S2):
    cleanString1 = cleanString(S1)
    cleanString2 = cleanString(S2)
    matcher = SequenceMatcher(None, cleanString1, cleanString2)
    match = matcher.find_longest_match(0, len(cleanString1), 0, len(cleanString2))
    return match.size


def cleanString(S1):
    return S1.lower().strip()


def calculateStringSimilarityPercentage(S1, S2):
    cleanString1 = cleanString(S1)
    cleanString2 = cleanString(S2)
    return SequenceMatcher(None, cleanString1, cleanString2).ratio() * 100


def add_normalized_names(company_list):
    # TODO instead generate a list of the most frequent words in company names in all lists and use those as the stop words?
    # In any case add the n% most common words as stop words

    generic_name_exclude_list = {"winery", "company", "pty", "ltd", "vineyard", "vineyards", "estate", "estates", "plc",
                                 "cellar",
                                 "winemaker", "group", "international", "wines", "limited", "agricola", "winework",
                                 "wineries", "wine",
                                 "farm", "family", "vigneron", "vign", "merchant", "at", "of", "the", "de", "du",
                                 "cellars", "vintners", "sl",
                                 "agr", "gmbh", "weinkellerei", "sa", "fe", "dr", "spa", "c", "co", "casa", "casas",
                                 "ab", "cspa", "fatt", "supermarkets", "sca",
                                 "champagne", "weingut", "weing", "weinhaus", "az,", "inc", "ag", "gebr", "gebruder",
                                 "ch", "cant", "winery", "vin", "weinbau", "distillerie", "distillery",
                                 "bros", "cast", "corp", "di", "el", "dominio", "pty", "il", "est", "srl", "das", "do",
                                 "llc", "bds", "int", "e", "and", "y", "vinos", "viticultor", "vitivinicola",
                                 "bryggeri", "brygghus", "bryghus", "brewery", "ab", "by", "azienda", "sociedade",
                                 "agricola", "les", "vignerons",
                                 "brewers", "breweries", "brewing", "brouwerij", "birras", "grupo", "vinedos",
                                 "societa", "spanish",
                                 "beer", "beer house", "brew house", "birra", "brauerei", "brasserie", "bieres",
                                 "bierbrouwerij", "abbazia"}
    generic_name_exclude_list_2 = {
        "marques", "marq",
        "agricola", "agr",
        "vigneron", "vign",
        "weingut", "weing",
        "bodega", "bod",
        "domaine", "dom",
        "champagne", "champ",
        "gebruder", "gebr",
        "brothers", "bros",
        "doctor", "dr",
        "saint", "st",
        "company", "co",
        "cantine", "cant",
        "cantina", "cant",
        "compania", "comp",
        "distilleria", "dist",
        "chateau", "ch",
        "vinicole", "vin",
        "fattoria", "fatt"
    }
    common_words = {"hills", "creek", "view", "valley", "ridge", "grand", "alta", "house", "nuevo", "gran",
                    "chateau", "monte", "mount", "veuve", "long", "port", "martin", "royal", "urban"}

    generic_name_endings = {"wines",
                            "vineyards",
                            "wine",
                            "beer",
                            "winery",
                            "brewery",
                            "spirits",
                            "coop",
                            "champagne",
                            "productions"}

    stopwords = set(generic_name_exclude_list | common_words | generic_name_exclude_list_2 | generic_name_endings)

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


def possible_name_match(a_company, another_company):
    a_name = a_company["dev.normalized_name"]
    another_name = another_company["dev.normalized_name"]
    possible_name_match = LongestCommonSubstringSize(a_name, another_name) > 4 and calculateStringSimilarityPercentage(
        a_name, another_name) > 80
    if possible_name_match:
        if a_company["dev.countries"].isdisjoint(another_company["dev.countries"]):
            close_name_match = LongestCommonSubstringSize(a_name,
                                                          another_name) > 6 and calculateStringSimilarityPercentage(
                a_name, another_name) > 90
            if close_name_match:
                print("Warning: country mismatch for companies '{}' and '{}'".format(a_company["company_name"],
                                                                                     another_company["company_name"]))
            return close_name_match

    return possible_name_match


if __name__ == "__main__":
    from timeit import default_timer as timer

    start = timer()

    products = import_products_from_vinmonopolet('produkter.csv')
    products = post_process_vinmonopolet_data(products)

    wine_companies_at_vinmonopolet = create_company_list_from_vinmonpolet(products)
    wine_companies_at_vinmonopolet = add_normalized_names(wine_companies_at_vinmonopolet)

    vegan_companies = import_products_from_barnivore(False)
    vegan_companies = add_normalized_names(vegan_companies)

    print("Found {} wine companies at Vinmonopolet, and {} listed in Barnivore".format(
        len(wine_companies_at_vinmonopolet), len(vegan_companies)))

    match_count = 0
    for vegan_company in vegan_companies:
        for vinmonopolet_company in wine_companies_at_vinmonopolet:
            if possible_name_match(vegan_company["company"], vinmonopolet_company["company"]):
                print("Possible match between '{}' and '{} ('{}' ~= '{}')'".format(
                    vegan_company["company"]["company_name"],
                    vinmonopolet_company["company"]["company_name"],
                    vegan_company["company"]["dev.normalized_name"],
                    vinmonopolet_company["company"]["dev.normalized_name"]))
                match_count += 1
                if "products_found_at_vinmonopolet" in vegan_company["company"]:
                    # Exists already, consider overwriting the old entry, if the new match is better
                    # TODO check similarity of original name or normalized name?
                    old_similarity = calculateStringSimilarityPercentage(vegan_company["company"]["company_name"], vegan_company["company"]["products_found_at_vinmonopolet"][0]["Produsent"])
                    new_similarity = calculateStringSimilarityPercentage(vegan_company["company"]["company_name"],
                                                                         vinmonopolet_company["company"]["company_name"])
                    if new_similarity > old_similarity:
                        #Overwrite it
                        print("Warning overwrite of results for company {}".format(vegan_company["company"]["company_name"]))
                        vegan_company["company"]["products_found_at_vinmonopolet"] = vinmonopolet_company["company"]["products_found_at_vinmonopolet"]
                else:
                    # doesn't exist yet, just add it
                    vegan_company["company"]["products_found_at_vinmonopolet"] = vinmonopolet_company["company"]["products_found_at_vinmonopolet"]

    end = timer()

    print("Found {} possible company matches in {}s".format(match_count, int(end - start + 0.5)))
