#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from timeit import default_timer as timer
import winestrings as wines

import multiprocessing
from itertools import repeat
import http_helper

vegan_friendly_output_filename = "vegan-friendly-searchresult-vinmonopolet.json"
some_vegan_products_output_filename = "some-vegan-options-searchresult-vinmonopolet.json"


def possible_name_match(vegan_company, vinmonopolet_company):
    a_name = vegan_company["dev.search_string"]
    another_name = vinmonopolet_company["dev.search_string"]
    possible_name_match = wines.lcs(a_name, another_name) >= 4 \
                          and wines.name_similarity(a_name, another_name) > 85

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

    with open(outputfile_all_vegan, mode='w', encoding='utf-8') as f:
        json.dump(all_vegan_companies, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.flush()
    print("Found {} possible vegan wine company matches".format(len(all_vegan_companies)))

    with open(outputfile_some_vegan, mode='w', encoding='utf-8') as f:
        json.dump(partly_vegan_companies, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.flush()
    print("Found {} possible matches for wine companies with some vegan options".format(len(partly_vegan_companies)))


def find_possible_matches(company_tuple_list):
    possible_name_matches = []
    vegan_company = None
    for vinmonopolet_company, barnivore_company in company_tuple_list:
        if possible_name_match(vinmonopolet_company, barnivore_company):
            possible_name_matches.append(vinmonopolet_company)
            vegan_company = barnivore_company
    if possible_name_matches:
        return (vegan_company, possible_name_matches)
    else:
        return None


def find_possible_company_matches(vegan_companies, wine_companies_at_vinmonopolet):
    dataset = []
    for vegan_company in vegan_companies:
        combinations = zip(wine_companies_at_vinmonopolet, repeat(vegan_company))
        dataset.append(combinations)

    num_agents = multiprocessing.cpu_count() - 1 or 1
    chunk_size = int(len(dataset) / num_agents + 0.5)
    with multiprocessing.Pool(processes=num_agents) as pool:
        result = pool.map(find_possible_matches, dataset, chunk_size)

        filtered_list = [x for x in result if x]  # remove empty items

        for vegan_company, vinmonopolet_companies in filtered_list:
            vegan_company_name = vegan_company["company_name"]
            # print("Searching for company '{}' ('{}') at Vinmonopolet...".format(vegan_company_name, vegan_company["dev.search_string"]))

            possible_matches = []
            for candidate in vinmonopolet_companies:
                vinmonopolet_company_name = candidate["company_name"]
                normalized_name_similarity = wines.name_similarity(vegan_company["dev.normalized_name"], candidate["dev.normalized_name"])
                search_name_similarity = wines.name_similarity(vegan_company["dev.search_string"], candidate["dev.search_string"])
                close_name_match = search_name_similarity > 0.9

                if (not close_name_match and normalized_name_similarity < 0.65) or normalized_name_similarity < 0.45:
                    print("Warning: ignoring match between companies '{}' and '{}', listed names vary too much - {:.3f}, {:.3f}".format(vegan_company_name,
                                                                                                                                        vinmonopolet_company_name,
                                                                                                                                        normalized_name_similarity,
                                                                                                                                        search_name_similarity))
                    # TODO mark as bad match, and keep in output json for manual de-marking?
                    continue

                if vegan_company["dev.countries"].isdisjoint(candidate["dev.countries"]):
                    # If countries do not match, require a very close name match
                    if close_name_match:
                        if "usa" in vegan_company["dev.countries"] or "canada" in vegan_company["dev.countries"]:
                            # Barnivore contains many of these entries, but Vinmonpolet does not, so we skip them in order to simplify manual post-processing
                            print("Skipping entry for USA or Canada company with country value mismatch")
                        else:
                            print("Warning: country mismatch for companies '{}' and '{}'".format(vegan_company_name, vinmonopolet_company_name))
                            vegan_company["dev.country_mismatch"] = True  # Mark the entry for inspection
                            possible_matches.append(candidate)
                    else:
                        print("Warning: ignoring match between companies '{}' and '{}', countries differ".format(vegan_company_name, vinmonopolet_company_name))
                else:
                    possible_matches.append(candidate)

            if len(possible_matches) > 1:
                print("Multiple possible matches for company '{}' ({}):".format(vegan_company_name, vegan_company["red_yellow_green"]))
                for candidate in possible_matches:
                    print("    '{}' ('{}' ≈ '{}')".format(candidate["company_name"],
                                                          vegan_company["dev.normalized_name"],
                                                          candidate["dev.normalized_name"]))

                best_candidate = None
                best_similarity_score = -1
                for candidate in possible_matches:
                    similarity_score = wines.name_similarity(vegan_company["dev.normalized_name"], candidate["dev.normalized_name"])
                    if similarity_score > best_similarity_score:
                        best_candidate = candidate
                        best_similarity_score = similarity_score
                    # todo OR - sort by similarity, and if top two matches are really close in similarity, do a tie break comparision in more detail

                print("Selected '{}' as the most closest match - {:.3f}".format(best_candidate["company_name"], best_similarity_score))
                vegan_company["products_found_at_vinmonopolet"] = best_candidate["products_found_at_vinmonopolet"]
                print_possible_match_detail(vegan_company, best_candidate)
            elif possible_matches:
                normalized_name_similarity = wines.name_similarity(vegan_company["dev.normalized_name"], possible_matches[0]["dev.normalized_name"])
                search_name_similarity = wines.name_similarity(vegan_company["dev.search_string"], possible_matches[0]["dev.search_string"])
                print("Possible match for company '{}': '{}' ({}) - {:.3f}, {:.3f}".format(vegan_company_name,
                                                                                           possible_matches[0]["company_name"],
                                                                                           vegan_company["red_yellow_green"],
                                                                                           normalized_name_similarity,
                                                                                           search_name_similarity))
                vegan_company["products_found_at_vinmonopolet"] = possible_matches[0]["products_found_at_vinmonopolet"]
                print_possible_match_detail(vegan_company, possible_matches[0])

        return [x[0] for x in filtered_list]  # barnivore companies with added data


def print_possible_match_detail(vegan_company, vinmonopolet_company):
    url = vegan_company["url"].strip()
    print("  {} - \"{}\"".format(url, http_helper.get_title(url)))

    print("  {}".format(vinmonopolet_company["products_found_at_vinmonopolet"][0]["Vareurl"]))
    print("  {} products found".format(len(vinmonopolet_company["products_found_at_vinmonopolet"])))


if __name__ == "__main__":
    start = timer()

    wine_companies_at_vinmonopolet = wines.load_wine_companies_from_vinmonopolet('produkter.csv')
    wine_companies_from_barnivore = wines.load_companies_from_barnivore('wine.json')
    print("Using {} wine companies at Vinmonopolet, and {} listed in Barnivore".format(
        len(wine_companies_at_vinmonopolet), len(wine_companies_from_barnivore)))

    stopwords = wines.create_stopword_list(wine_companies_from_barnivore, wine_companies_at_vinmonopolet)
    wine_companies_at_vinmonopolet = wines.add_normalized_names(wine_companies_at_vinmonopolet, stopwords)
    wine_companies_from_barnivore = wines.add_normalized_names(wine_companies_from_barnivore, stopwords)

    vegan_companies_at_vinmonopolet = find_possible_company_matches(wine_companies_from_barnivore, wine_companies_at_vinmonopolet)

    write_result_file(vegan_companies_at_vinmonopolet, vegan_friendly_output_filename, some_vegan_products_output_filename)

    end = timer()
    print("Total time usage: {}s".format(int(end - start + 0.5)))
