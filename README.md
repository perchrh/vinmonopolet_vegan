Finds vegan wines in Vinmonopolet's product list, using the Barnivore API (http://barnivore.com/old-api).
Employs fuzzy matching, as the manufacturer names in the databases don't always match, because of abbreviations and omissions of certain generic words
in the full company name.

Uses python 3.x.

Install it like this (Ubuntu/Debian):
    
    sudo apt-get install python3

Or for Mac:
Install homebrew, then
 
    brew install python3
    
Then install required dependencies:

    pip3 install beautifulsoup4 --upgrade
    pip3 install requests --upgrade
    pip3 install fuzzywuzzy[speedup] --upgrade

Get the updated wine.json from http://barnivore.com/wine.json \
It may have encoding errors, invalid utf-8 in it. 

Fix it with this command: 
     
    iconv --verbose -f utf-8 -t utf-8//ignore wine.json > winenew.json && mv winenew.json wine.json

Get the updated product list from Vinmonopolet, described at
https://www.vinmonopolet.no/datadeling/csv,  available at
https://www.vinmonopolet.no/medias/sys_master/products/products/hbc/hb0/8834253127710/produkter.csv

Run

    python3 vegan_wine_search.py

and validate the resulting list in the json files

Tips for validating the list
----

The list will include false positives because of the intentional fuzzy matching of manufacturers' names.
Regexp-search for Varenavn|manufacturer_name in the json file to highlight these fields.
Then for each company's wine list check if there is a name mismatch.
Also check for when countries don't match exactly (dev.country_mismatch = true entries). 
Then delete bad ones.

After that, parse the json using generatehtml.py to produce a human-readable HTML page
