#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import winestrings as wines
import http_helper
import requests

if __name__ == "__main__":
    for source in ["wine.json", "beer.json", "liquor.json"]:
        print("*********")
        print(source)
        companies = wines.load_companies_from_barnivore(source)
        print("Loaded {} companies from Barnivore".format(len(companies)))
        missing_url, got_url = [], []
        for c in companies:  
                (got_url if ('url' in c.keys() and c["url"].strip()) else missing_url).append(c)

        for company in missing_url:
            print("Missing 'url' key;color={};company;id={}".format(company["red_yellow_green"], company["id"]))

        for company in got_url:
            try:
                print("DEBUG: fetching {}".format(company["url"]))
                body = http_helper.get_webpage(company["url"])
            except requests.exceptions.RequestException as ex:
                print("Website retrieval error;color={};id={};{}".format(company["red_yellow_green"], company["id"], str(ex)))
