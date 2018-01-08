
def import_products_from_csv(filename):
        import csv
        import sys
        data={}
        with open(filename, 'r', newline='', encoding='iso-8859-1') as csvfile:
            wine_reader = csv.DictReader(csvfile, delimiter=';')
            try:
                return list(wine_reader)
            except csv.Error as e:
                sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))


def search_export_for_company_name_variations(export_data, company_name):
    for row in export_data:
        #Datotid;Varenummer;Varenavn;Volum;Pris;Literpris;Varetype;Produktutvalg;Butikkategori;
        #Fylde;Friskhet;Garvestoffer;Bitterhet;Sodme;Farge;Lukt;Smak;Passertil01;Passertil02;Passertil03;
        #Land;Distrikt;Underdistrikt;
        #Argang;Rastoff;Metode;Alkohol;Sukker;Syre;Lagringsgrad;
        #Produsent;Grossist;Distributor;
        #Emballasjetype;Korktype;Vareurl

        wine_properties = row
        wine_properties["Lagerstatus"] = row["Produktutvalg"] # mangler i exporten?
        wine_properties["ProdusentSide"] = None # mangler i exporten?
        wine_properties["ProduktBilde"] = "https://bilder.vinmonopolet.no/cache/600x600-0/%s-1.jpg" % (wine_properties["Varenummer"])

        if wine_properties["Produsent"] == company_name:
            print(row)


if __name__ == "__main__":
    products = import_products_from_csv('produkter.csv')
    wine_products = [x for x in products if "vin" in x["Varetype"] or "Champagne" in x["Varetype"]]

    wine_companies = {}
    for product in wine_products:
        produsent = product["Produsent"]
        if not produsent in wine_companies:
            wine_companies[ produsent ] = []
        wine_companies[produsent].append(product)

    print("Det er {} produsenter i csv-fila".format(len(wine_companies)))

    #search_export_for_company_name_variations(products, "Tommasi")
