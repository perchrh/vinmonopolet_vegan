#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import multiprocessing
import logging
from logging.handlers import QueueHandler, QueueListener

import winestrings as wines
import http_helper
import requests

# multiprocessor logging courtesy of https://stackoverflow.com/a/34964369/788913

def worker_init(q):
    # all records from worker processes go to qh and then into q
    qh = QueueHandler(q)
    logger = logging.getLogger()
    logger.setLevel(logging.WARN)
    logger.addHandler(qh)


def logger_init():
    q = multiprocessing.Queue()
    # this is the handler for all log records
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(asctime)s - %(process)s - %(message)s"))

    # ql gets records from the queue and sends them to the handler
    ql = QueueListener(q, handler)
    ql.start()

    logger = logging.getLogger()
    logger.setLevel(logging.WARN)
    # add the handler to the logger so records from this process are handled
    logger.addHandler(handler)

    return ql, q


def visit_company_site(company):
    try:
        logging.debug("fetching {}".format(company["url"]))
        http_helper.get_webpage(company["url"], company["id"], company["company_name"])
    except requests.exceptions.RequestException as ex:
        logging.error("Website retrieval error;{};{};{};{}".format(company["red_yellow_green"],
                                                           company["company_name"],
                                                           company["id"],
                                                           str(ex)))


if __name__ == "__main__":
    q_listener, q = logger_init()

    for source in ["wine.json", "beer.json", "liquor.json"]:
        logging.info("*********")
        logging.info(source)
        companies = wines.load_companies_from_barnivore(source)
        logging.info("Loaded {} companies from Barnivore".format(len(companies)))
        missing_url, got_url = [], []
        for c in companies:
            (got_url if ('url' in c.keys() and c["url"].strip()) else missing_url).append(c)

        for company in missing_url:
            logging.error("Missing 'url' key;{};{};{}".format(company["red_yellow_green"],
                                                      company["company_name"],
                                                      company["id"]))

        num_agents = multiprocessing.cpu_count() - 1 or 1
        chunk_size = int(len(got_url) / num_agents + 0.5)
        with multiprocessing.Pool(num_agents, worker_init, [q]) as pool:
            result = pool.map(visit_company_site, got_url, chunk_size)
