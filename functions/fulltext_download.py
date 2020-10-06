#!/usr/bin/env python
# coding: utf-8

### Http headers and downloading settings
# Before all starts, please endure you have an orcid id first and then, go to [here](https://apps.crossref.org/clickthrough/researchers/) to obgain an api key for wiley and science direct.
# This step will help the pdf retrival from wiley and science direct smoothly.

import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from functions.get_request import get_request
from functions import ftp_download
import os
from time import sleep
import pandas as pd

def download_file_from_httplink(link, subfolder, filename, timeout = (10,60), outputFolder = "output/", format_type = None, onlyPdf = False, sleepTime= 1):     
    output = {'error': None,
              'status_code': None,
              'Filepath': None
  #            'Filetype': None
             }
    email = 'shihikoo@gmail.com'
    elsevier_api_key = 'ff541d54cadc4bb517efef13cd4924e3'
    click_through_api_key = 'bd3fcb92-d5dfac5a-5e73c324-d4a26ac0'
    
    # Create headers
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36",
             'Accept-Language': "en,en-US;q=0,5",
             'Accept': "text/html,application/pdf,application/xhtml+xml,application/xml,text/plain,text/xml",
             'CR-Clickthrough-Client-Token': click_through_api_key,
             'mailto':email,
             'apikey':elsevier_api_key,
             'Accept-Encoding': 'gzip, deflate, compress',
             'Accept-Charset': 'utf-8, iso-8859-1;q=0.5, *;q=0.1'}
    
    # Create http session
    http = requests.Session()
    http.headers.update(headers)
    retry_strategy = Retry(
        total=3,
        status_forcelist=[404, 429, 500, 502, 503, 504],
        method_whitelist=["GET"],
        backoff_factor=1,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http.mount('', adapter)
        
    r = get_request(link, http, headers, timeout)
    
    output['status_code'] = r['status_code']
    output['error'] = r['error']
    
    if r['status_code'] == 200:        
        headers = r['headers']
        if(format_type is None):
            format_type = headers['Content-Type']
        ioutputFolder = f'{outputFolder}{subfolder}'
        os.makedirs(ioutputFolder, exist_ok=True)
                
        fullfilename = f'{ioutputFolder}{filename}'
        
        if ('pdf' in format_type):
            with open(f'{ioutputFolder}{filename}.pdf', 'wb') as file:
                  file.write(r['content'])
            output['Filepath'] = f'{fullfilename}.pdf'
    #        output['Filetype'] = 'pdf' 
        elif (('xml' in format_type) or ('.xml' in link)) and not onlyPdf :
            with open(f'{ioutputFolder}{filename}.xml', 'w+') as file:
                  file.write(r['text'])
            output['Filepath'] = f'{fullfilename}.xml'
     #       output['Filetype'] = 'xml' 
        elif 'html' in format_type and  not onlyPdf:
            with open(f'{ioutputFolder}{filename}.html', 'w+') as file:
                  file.write(r['text'])
            output['Filepath'] = f'{ioutputFolder}{filename}.html'
     #       output['Filetype'] = 'html' 
        elif 'plain' in format_type and  not onlyPdf:
            with open(f'{ioutputFolder}{filename}.txt', 'w+') as file:
                  file.write(r['text'])
            output['Filepath'] = f'{fullfilename}.txt'
      #      output['Filetype'] = 'txt' 
        elif 'gzip' in format_type:
            with open(f'{fullfilename}.tar.gz', 'wb') as file:
                  file.write(r['content'])
            output['Filepath'] = f'{fullfilename}.tar.gz'
         #   output['Filetype'] = 'tar'
        
        sleep(sleepTime)
            
    output =  pd.Series(output)   
    
    output = output.where(output.notnull(),None)
    
    return output

def download_file_from_crossrefjson_links(myInput, subfolder, click_through_api_key, elsevier_api_key, timeout = (10,60), outputFolder = "output/", format_type = None, onlyPdf = False, sleepTime= 1):
    
    links = myInput['CrossrefLinks']
    filename = myInput['Id']

    if onlyPdf:
        links = [link for link in links if ((link['content-type'] == 'application/pdf') | (link['content-type'] == 'unspecified'))]
    if len(links) == 0:
        return None

    for link in links:
        output = download_file_from_httplink(link['URL'], subfolder, filename, timeout = timeout, outputFolder = outputFolder, format_type = format_type, onlyPdf=onlyPdf, sleepTime=sleepTime)
        if output['Filepath']:
            break
    
    if output['Filepath'] is not None:
        output['FileSource'] = 'crossref'
    else:
        output['FileSource'] = None
        
    output.rename({"status_code":"crossref_status_code", "error":"crossref_error"},  inplace=True)

    return  output
   
def download_file_from_pmc_ftpzip(pmc, myInput, subfolder, outputFolder = "output/", onlyPdf = False, sleepTime= 1):
 
    targzFilename = myInput['pmclink']
    filename = myInput['Id']
    outputfilename = f'{outputFolder}{subfolder}{filename}'
    # fileDirectory = f'{os.path.dirname(targzFilename)}/'
    
    output = ftp_download.extract_gzip(targzFilename, outputfilename, ignore = True, sleepTime = sleepTime, onlyPdf = onlyPdf)
    
    if output['Filepath']:
        output['FileSource'] = 'pmc'
    else:
        output['FileSource'] = None
            
    return  pd.Series(output)

# def download_file_from_pmc_ftplinks(myInput, subfolder,timeout = (10,60), outputFolder = "output/", format_type = None, onlyPdf = False, sleepTime= 1):
#     '''
#     Download file from pmc file links using its http links
#     '''
  
#     link = myInput["pmclink"].replace("ftp://","http://")
    
#     output = download_file_from_httplink(link, subfolder, myInput['Id'],  timeout = timeout, outputFolder = outputFolder, format_type = format_type, onlyPdf=False, sleepTime=sleepTime)
    
#     if output['Filepath'] is None:
#         output['FileSource'] = None
#         return output

#     targzFilename = output['Filepath']
#     output['Filepath'] = None
#     filename = myInput['Id']
#     outputfilename = f'{outputFolder}{subfolder}{filename}'
#     fileDirectory = f'{os.path.dirname(targzFilename)}/'
    
#     with tarfile.open(targzFilename, "r:gz") as tar:
#         pdffiles = [tarinfo for tarinfo in tar if (tarinfo.name.endswith('.pdf'))]   
        
#         if (pdffiles is None) | (len(pdffiles) != 0):
#             tar.extractall(members=pdffiles, path = fileDirectory)     
#             downloadedpdf_filename = f'{fileDirectory}{pdffiles[0].name}'
#             outputpdf_filename = f'{outputfilename}.pdf'
#             os.rename(downloadedpdf_filename, outputpdf_filename)
#             shutil.rmtree(os.path.dirname(downloadedpdf_filename))
#             output['Filepath'] = outputpdf_filename
#         else:
#             output['Filepath'] = None
            
#     if os.path.exists(targzFilename):
#         os.remove(targzFilename) 
    
#     if output['Filepath'] is not None:
#         output['FileSource'] = 'pmc'
#     else:
#         output['FileSource'] = None
        
#     return  pd.Series(output)
    
def download_file_from_pmc_httplinks(myInput, subfolder, timeout = (10,60), outputFolder = "output/", format_type = None, onlyPdf = False, sleepTime= 1):
    link = myInput['pmclink']
    if  'ftp://' in link:
        link = myInput["pmclink"].replace("ftp://","http://")
 
    output = download_file_from_httplink(link, subfolder, myInput['Id'], timeout = timeout, outputFolder = outputFolder, format_type = format_type, onlyPdf=onlyPdf, sleepTime=sleepTime)
    
    if output['Filepath']:
        output['FileSource'] = 'pmc'
    else:
        output['FileSource'] = None
        
    output.rename({'status_code':'pmc_status_code', 'error':'pmc_error'}, inplace = True)
    
    return  output

def download_file_from_pmc_nonzip_links(myInput, subfolder, timeout = (10,60), outputFolder = "output/", format_type = None, onlyPdf = False, sleepTime= 1):
    link = myInput['pmclink']
    
    if (link is None) | ('.tar.gz' in link): 
        output = {'error': None,
              'status_code': None,
              'filepath': None,
              'filetype': None
             }
        return output
    
    if '.tar.gz' in link: 
        output = {'error': None,
              'status_code': None,
              'filepath': None,
              'filetype': None
             }
        return output
    
    link = myInput["pmclink"].replace("ftp://","http://")
 
    output = download_file_from_pmc_httplinks(myInput, subfolder, timeout = timeout, outputFolder = outputFolder, format_type = format_type, onlyPdf = onlyPdf, sleepTime= sleepTime)

    output.rename({'status_code':'pmc_status_code', 'error':'pmc_error'}, inplace = True)

    return output

def download_file_from_doi_links(myInput, subfolder, timeout = (10,60), outputFolder = "output/", format_type = None, onlyPdf = False, sleepTime= 1):

    links = myInput['DoiLinks']
    filename = myInput['Id']

    if onlyPdf:
        links = [link for link in links if ((link['content-type'] == 'application/pdf') | (link['content-type'] == 'unspecified'))]
    if len(links) == 0:
        return None

    for link in links:
        output = download_file_from_httplink(link['URL'], subfolder, filename,timeout = timeout, outputFolder = outputFolder, format_type = format_type, onlyPdf=onlyPdf, sleepTime=sleepTime)
        if output['Filepath']:
            break
    
    if output['Filepath']:
        output['FileSource'] = 'doi'
    else:
        output['FileSource'] = None
    
    output.rename({'status_code':'doi_status_code', 'error':'doi_error'}  ,  inplace=True)

    return  output

    