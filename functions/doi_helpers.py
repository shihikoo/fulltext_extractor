#!/usr/bin/env python
# coding: utf-8

from bs4 import BeautifulSoup
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from functions.get_request import get_request
import re

def retrive_metadata_with_doi(doi, timeout = (10,60)):
    output = {'error':None,
              'status': None,
              'xml':None}
    
    baseurl = 'https://doi.org/'
# Create headers 
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36",
        'Accept-Language': "en,en-US;q=0,5",
        'Accept': "text/html,application/pdf,application/xhtml+xml,application/xml,text/plain,text/xml,text/json",
        'mailto': "shihikoo@gmail.com",
        'Accept-Encoding': 'gzip, deflate, compress',
        'Accept-Charset': 'utf-8, iso-8859-1;q=0.5, *;q=0.1'}
# Create http session
    http = requests.Session()
    http.headers.update(headers)
    retry_strategy = Retry(
        total=3,
        status_forcelist=[500, 502, 503, 504],
        method_whitelist=["GET"],
        backoff_factor=1,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http.mount('', adapter)
# Create timeout
    timeout = (10,60)
    
    url = f'{baseurl}{doi}'
    
    r = get_request(url, http, headers, timeout)
    
    output['status'] = r['status_code']
    output['error'] = r['error']
    
    if r['status_code'] == 200:
        output['xml'] = r['text']
    
    return output

def parse_fulltextlink_from_doimetadata(xml):
    soup = BeautifulSoup(xml, features="html.parser")
    output = []
    
    pdfLinks = soup.find_all('meta', attrs={'name': re.compile('^citation_pdf')})
    for link in pdfLinks:
        if link.get('content') != '':
            output.append({'URL':link.get('content')
                           , 'content-type':'application/pdf'
                }
                )

    htmlLinks = soup.find_all('meta', attrs={'name': re.compile('^citation_full')})
    for link in htmlLinks:
        if link.get('content') != '':
                        output.append({'URL':link.get('content')
                           , 'content-type':'text/html'
                }
                )     
                
    return output

def extract_fulltextlink_with_doi(doi, timeout = (10,60)):
    metadata = retrive_metadata_with_doi(doi, timeout = timeout)
    if metadata['xml'] != None:
        output = parse_fulltextlink_from_doimetadata(metadata['xml'])
    else:
        return None
    
    if len(output) == 0:
        return None
    
    return output

