#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  4 21:07:59 2020

@example doi_to_pmci('doi:https://doi.org/10.2807/1560-7917.ES.2020.25.14.20200409c','myeamil@example.com')

@author: jliao
"""

import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from functions.get_request import get_request
import json
from bs4 import BeautifulSoup

def doi_sourced(doi, email='', timeout = (10,60)):
    output = {'status': None,
              'error': None,
              'output': None}
        
    doi = doi.replace('doi:','').replace('https://doi.org/','').replace('http://dx.doi.org/','')
    baseUrl = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool=syrf&email={email}&format=json&ids="
    url = f'{baseUrl}{doi}'
 # create a header to interact with the crossref API and server appropriately
    headers = {'mailto': email}
    # Creat http session
    http = requests.Session()
    http.headers.update(headers)
    retry_strategy = Retry(
        total=1,
        status_forcelist=[404, 429, 500, 502, 503, 504],
        method_whitelist=["GET"],
        backoff_factor=1,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http.mount(baseUrl, adapter)
        
    r = get_request(url, http, headers, timeout)
    output['status_code'] = r['status_code']
    output['error'] = r['error']
    if r['status_code'] == 200:
        output['output'] = r['text']
        
    return output

def doi_parser(doi_converter_json_output):    
    records = json.loads(doi_converter_json_output)['records']
        
    return records[0]

def doi_to_pmcid(doi, email='', timeout = (10,60)):
    if doi is None or doi == '':
        return None
    r = doi_sourced(doi, email, timeout = timeout)
    if r['output'] is not None:
        ids = doi_parser(r['output'])
    else:
        return None
    
    if 'pmcid' in ids: 
        pmcid= ids['pmcid']
    else:
        pmcid = None
    return(pmcid)

def construct_pmc_fulltext_pdf_link(pmcid):
    if pmcid is None:
        return None
    
    return  f'https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf'

def find_pmc_fulltext_pdf_ftplink(pmcid, email='',timeout=(10,60)):
    if pmcid is None:
        return None
    
    output = None
        
    baseUrl = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id="
    url = f'{baseUrl}{pmcid}'
 # create a header to interact with the crossref API and server appropriately
    headers = {'mailto': email}
    # Creat http session
    http = requests.Session()
    http.headers.update(headers)
    retry_strategy = Retry(
        total=1,
        status_forcelist=[404, 429, 500, 502, 503, 504],
        method_whitelist=["GET"],
        backoff_factor=1,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http.mount(baseUrl, adapter)
        
    r = get_request(url, http, headers, timeout)
    if r['status_code'] != 200:
        return output
    
    soup = BeautifulSoup(r['text'], 'html.parser')
    links = soup.find_all('link')
    
    links = [link for link in links if (link['format'] == 'tgz') ]

    if len(links) == 0:
        return construct_pmc_fulltext_pdf_link(pmcid) 
    print(links)
    output = links[0]['href']
    
    return output