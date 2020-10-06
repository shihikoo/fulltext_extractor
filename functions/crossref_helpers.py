#!/usr/bin/env python
# coding: utf-8

from bs4 import BeautifulSoup
import pandas as pd
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from functions.get_request import get_request
import json
import copy

def retrive_crossref_api_metadata_file(doi, timeout = (10,60)):
    output = {'status_code': None,
              'error': None,
              'output': None}
    
    baseUrl = "http://api.crossref.org/works/"
    email = "shihikoo@gmail.com"
 # create a header to interact with the crossref API and server appropriately
    headers = {'mailto': email, 
               'X-Rate-Limit-Limit' : '50',
               'X-Rate-Limit-Interval': '1s'}
    
    # Creat http session
    http = requests.Session()
    http.headers.update(headers)
    retry_strategy = Retry(
        total=3,
        status_forcelist=[404, 429, 500, 502, 503, 504],
        method_whitelist=["GET"],
        backoff_factor=1,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http.mount(baseUrl, adapter)
    
    url = f'{baseUrl}{doi}'
    
    r = get_request(url, http, headers, timeout)
    output['status_code'] = r['status_code']
    output['error'] = r['error']
    if r['status_code'] == 200:
        output['output'] = r['text']
        
    return output

def wiley_adjustment(link_list):  
    wiley_link_list = [link for link in link_list if ('https://onlinelibrary.wiley.com/doi/pdf/' in link['URL'])]
    # print(link_list)
    if wiley_link_list:
        new_wiley_link = copy.copy(wiley_link_list[0])
        new_wiley_link['URL'] = new_wiley_link['URL'].replace("/pdf/","/pdfdirect/")
        link_list.append(new_wiley_link)
    # print(link_list)
    return link_list


def parse_crossref_api_metadata_file(jsoninput, only_textmining = False, only_pdf = False):
    link_list = []
    
    if jsoninput is None:
        return None
    
    message = json.loads(jsoninput)['message']
    
    if not 'link' in message:
        return None
    
    link_list = message['link']
    
    link_list = [link for link in link_list if ('https://syndication.highwire.org' not in link['URL'])]
    
    link_list = wiley_adjustment(link_list)
    
    if only_pdf and len(link_list) > 0:
        link_list = [link for link in link_list if ((link['content-type'] == 'application/pdf') or (link['content-type'] == 'unspecified'))]
    if only_textmining and len(link_list) > 0:
        link_list = [link for link in link_list if link['intended-application'] == 'text-mining']
    else:
        pdflinklist = [link for link in link_list if link['intended-application'] == 'text-mining']
        if len(pdflinklist) > 0:
            link_list = pdflinklist
            
    if len(link_list) == 0:
        return None
    
    return link_list

def retrive_crossref_fulltextlink_json(doi, timeout = (10,60), only_textmining = False, only_pdf = False):
    jsonoutput = retrive_crossref_api_metadata_file(doi, timeout = timeout)
    if jsonoutput['output'] == None:
        return None
    link_list = parse_crossref_api_metadata_file(jsonoutput['output'], only_textmining = only_textmining, only_pdf = only_pdf)
    return(link_list)

def retrive_crossref_metaData_xml(doi, timeout = (10,60)):
    output = {'status_code': None,
              'error': None,
              'output': None}
    
    baseUrl = "https://dx.doi.org/"
    email = "shihikoo@gmail.com"
    # create a header to interact with the crossref API and server appropriately
    headers = {'Accept': 'application/vnd.crossref.unixsd+xml',
               'mailto': email, 
               'X-Rate-Limit-Limit' : '50',
               'X-Rate-Limit-Interval': '1s'}
    
    # Creat http session
    http = requests.Session()
    http.headers.update(headers)
    retry_strategy = Retry(
        total=3,
        status_code_forcelist=[404, 429, 500, 502, 503, 504],
        method_whitelist=["GET"],
        backoff_factor=1,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http.mount(baseUrl, adapter)
    
    url = f'{baseUrl}{doi}'
    
    r = get_request(url, http, headers, timeout)
    if r['status_code'] == 200:
        output['status_code'] = r['status_code']
        output['error'] = r['error']
        output['output'] = r['text']
    
    return output

# function that parse crossref xml
def crossref_xml_parser(xml):
    output = { 'TDMLinks':None,
                'linkSource': None
    }
    
    if xml is not None:
        soup = BeautifulSoup(xml, features="html.parser")
        
        # now get the full text links
        collectionsNode = soup.find_all('collection') 
        link_list = []
        if collectionsNode:
            # loop through each collection and see if there is a "property" attribute
            for collection in collectionsNode:
                if collection.has_attr('property'):
                    # TDM agreements ask that we use the links with these set attributres
                    if collection['property'] in ['text-mining']:
                        # when the attribute is appropriate, look for the links which are in 'resource' tags
                        resources = collection.find_all('resource')
                        # for each link, add it to our holding list, stripped of new lines etc
                        for resource in resources:
                            link_list.append(resource.text.strip())
                        output['linkSource'] = "TDM"
                    # this part is temeprately ignore the TDM agreements
                    else:
                        resources = collection.find_all('resource')
                        for resource in resources:
                            link_list.append(resource.text.strip())
                        output['linkSource'] = "Non-TDM"
        else:
        # here we retrive all teh links even they are not in the collection 
            pass    
  #          resources = soup.find_all('resource')
  #          for resource in resources:
  #              link_list.append(resource.text.strip())
  #          output['linkSource'] = ("Not in collection")
        
        link_list = pd.unique(link_list).tolist()
        if(len(link_list) > 0):
            output['TDMLinks'] = link_list
        
    return output
        

