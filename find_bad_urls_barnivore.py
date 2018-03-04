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
        for company in companies:
            url = None
            if 'url' in company.keys():
                url = company["url"].strip()

            if url:
                try:
                    body = http_helper.get_webpage(url)
                except requests.exceptions.RequestException as ex:
                    print("Website retrieval error;color={};id={};{}".format(company["red_yellow_green"], company["id"], str(ex)))
            else:
                print("Missing 'url' key;color={};company;id={}".format(company["red_yellow_green"], company["id"]))
