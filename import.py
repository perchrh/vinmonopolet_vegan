def import_products_from_vinmonopolet(filename):
    import csv
    import sys
    with open(filename, 'r', newline='', encoding='iso-8859-1') as csvfile:
        wine_reader = csv.DictReader(csvfile, delimiter=';')
        try:
            return list(wine_reader)  # read it all into memory
        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(filename, wine_reader.line_num, e))


import json
def import_products_from_barnivore(partialOnly):
    companies = list()
    with open('wine.json', encoding='utf-8') as file:
        for candidate in json.loads(file.read()):
            country = candidate['company']['country']
            if (country == 'USA') or (
                    country == 'Canada'):  # Too much non-matching data on USA and Canada wines, few of them available at Vinmonopolet
                print("Skipping wine for country =", country, "company =", candidate['company']['company_name'])
                continue

            status = candidate['company']['status']
            if (status == 'Has Some Vegan Options' and partialOnly) or (status == 'Vegan Friendly' and not partialOnly):
                companies.append(candidate)

    return companies

def search_export_for_company_name_variations(export_data, company_name):
    import dateutil.parser

    for row in export_data:
        # Headers are:
        # Datotid;Varenummer;Varenavn;Volum;Pris;Literpris;Varetype;Produktutvalg;Butikkategori;
        # Fylde;Friskhet;Garvestoffer;Bitterhet;Sodme;Farge;Lukt;Smak;Passertil01;Passertil02;Passertil03;
        # Land;Distrikt;Underdistrikt;
        # Argang;Rastoff;Metode;Alkohol;Sukker;Syre;Lagringsgrad;
        # Produsent;Grossist;Distributor;
        # Emballasjetype;Korktype;Vareurl

        wine_properties = row
        wine_properties["Lagerstatus"] = row["Produktutvalg"]  # mangler i exporten?
        wine_properties["Datotid"] = dateutil.parser.parse(row["Datotid"].replace(";", "."))
        wine_properties["ProdusentSide"] = None  # mangler i exporten?
        wine_properties["ProduktBilde"] = "https://bilder.vinmonopolet.no/cache/600x600-0/%s-1.jpg" % (
            wine_properties["Varenummer"])

        if wine_properties["Produsent"] == company_name:
            print(row)


import unicodedata
import string
def remove_diacritics(s):
    return ''.join(x for x in unicodedata.normalize('NFKD', s) if x in string.printable)

def add_normalized_names(company_list):
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
                                 "bryggeri", "brygghus", "bryghus", "brewery", "ab", "by", "azienda", "sociedade", "agricola"
                                 "brewers", "breweries", "brewing", "brouwerij", "birras", "grupo", "vinedos", "societa",
                                 "beer", "beer house", "brew house", "birra", "brauerei", "brasserie", "bieres",
                                 "bierbrouwerij", "abbazia"}
    generic_name_exclude_list_2 = {
        "marques", "marq.",
        "agricola", "agr.",
        "vigneron", "vign.",
        "weingut", "weing.",
        "bodega", "bod.",
        "domaine", "dom.",
        "champagne", "champ.",
        "gebruder", "gebr.",
        "brothers", "bros.",
        "doctor", "dr.",
        "saint", "st.",
        "company", "co.",
        "cantine", "cant.",
        "cantina", "cant.",
        "compania", "comp.",
        "distilleria", "dist.",
        "chateau", "ch.",
        "vinicole", "vin.",
        "fattoria", "fatt."
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

    for company_name in company_list:
        name_parts = company_name.strip().lower().replace(".", "").replace(",", "").split(" ")
        normalized_name_parts = [x for x in name_parts if not x in stopwords and len(x) > 2]
        normalized_name = remove_diacritics(" ".join(normalized_name_parts))
        print("original, normalized name = '{}', '{}'".format(company_name, normalized_name))

        # TODO bytt datastruktur til en dict som har company med name og normalized name etc
        # company_list[company_name]["dev.normalized_name"] = normalized_name

    return company_list

if __name__ == "__main__":
    products = import_products_from_vinmonopolet('produkter.csv')
    wine_products = [x for x in products if "vin" in x["Varetype"] or "Champagne" in x["Varetype"]]

    wine_companies = {}
    for product in wine_products:
        produsent = product["Produsent"]
        if not produsent in wine_companies:
            wine_companies[produsent] = []
        wine_companies[produsent].append(product)

    # TODO search list for normalized names matched
    wine_companies = add_normalized_names(wine_companies)

    vegan_companies = import_products_from_barnivore(False)
    vegan_companies_normalized = add_normalized_names([x["company"]["company_name"] for x in vegan_companies])

    #print("Det er {} produsenter i csv-fila".format(len(wine_companies)))

    #search_export_for_company_name_variations(products, "Tommasi")
