#!/usr/bin/env python
# coding: utf-8

# # Fulltext Extractor
# - This notebook aims to find the full text link for a list of dois.

# # Crossref uses DOIs to search for Article Metadata
# - The metadata contains information about links to full texts and licenses
# - We will use the Python "requests" library which will return the response as an xml

# In[1]:  Imports and settings
import pandas as pd 
import numpy as np
import os
import datetime
import warnings
from timeit import default_timer as timer
import sys
import getopt

from functions import crossref_helpers
from functions import fulltext_download
from functions import doi_helpers
from functions import pmc_helpers
from functions import ftp_download


def usage(name):
  print ('''
Usage: python {0} -i filename.csv [Input list of ids,dois]  -o output directory [Optional] -f

OPTIONS
  -h, --help:       Print this usage message
  -i:       input csv file path
  -o:  output directory
  -f: force rerun, ingore the picle file
'''.format(name))
    
def find_extention(filepath):
    if filepath is None:
        return(False)
        
    file,extention = os.path.splitext(filepath)
    return(extention)

def process(inputFilename
            , outputdirectory = ""
            , onlyPdf = True
            , ignore_errors = False     
            , rerun = False
        ):
    warnings.simplefilter(action='ignore', category=FutureWarning)
    
    # In[2]:  Read in data
    print(datetime.datetime.now())
    start = timer()
    
    projectName = os.path.splitext(os.path.basename(inputFilename))[0]
    
    if outputdirectory == "":
        outputFolder = f"{projectName}/"
    else:
        outputFolder = outputdirectory
        
    os.makedirs(outputFolder, exist_ok=True)
    
    fulltextOutputFolder = f'{outputFolder}full_texts/'
    # open(fulltextOutputFolder)
    os.makedirs(fulltextOutputFolder, exist_ok=True)
    
    # If this project has already run and has saved file, then read the saved file
    projectMetadataFilename = f'{outputFolder}{projectName} myDF.csv'
    pickleDFFilename = f'{outputFolder}{projectName} myDF.pkl'
    if (os.path.exists(pickleDFFilename)) & (rerun != True):
        myDF = pd.read_pickle(pickleDFFilename)
    else:
        myDF = pd.read_csv(inputFilename)[['Id','DOI']]
        # myDF = myDF.rename(columns={'Manual Tags':'Id'})     
        myDF.to_pickle(pickleDFFilename)
    
    print(f'Total of {len(myDF)} studies loaded. ')
    print(f'{sum(myDF["DOI"].notna())} studies have DOIs.')   
    
    # Create columns if not exists already
    if('pmcid' not in myDF):
        myDF['pmcid'] = None
        myDF['pmclink'] = None
    
    if('CrossrefLinks' not in myDF):
        myDF['CrossrefLinks'] = None
        
    if('Filepath' not in myDF):
        myDF['Filepath'] = None
        myDF['FileSource'] = None
        
    if('crossref_status_code' not in myDF):
        myDF['crossref_status_code'] = None
        myDF['crossref_error'] = None
        
    if('pmc_status_code' not in myDF):
        myDF['pmc_status_code'] = None
        myDF['pmc_error'] = None
        
    if('doi_status_code' not in myDF):
        myDF['doi_status_code'] = None
        myDF['doi_error'] = None  
        
    n_start = sum(myDF["Filepath"].notna())
    print(f'{n_start} publications already have pdfs.')
    
    # In[3]: convert doi to pmcids if possible and find pmc ftp links
    index = (myDF['pmcid'].isna()) & (myDF['DOI'].notna())
    if len(index) > 0:
        myDF.at[index,'pmcid'] = myDF.loc[index,'DOI'].replace(np.nan,"").apply(pmc_helpers.doi_to_pmcid)
      #  myDF.at[index,'pmclink'] = myDF.loc[index,'pmcid'].apply(pmc_helpers.construct_pmc_fulltext_pdf_link)
        myDF.at[index,'pmclink'] = myDF.loc[index,'pmcid'].apply(pmc_helpers.find_pmc_fulltext_pdf_ftplink)
        myDF.to_pickle(pickleDFFilename)
    
    print(f'{sum(myDF["pmcid"].notna())} publications have pmcid')
    
    # Download full text from pmc ftp pdf links
    index = myDF[(myDF['Filepath'].isna()) & (myDF['pmclink'].notna()) & (myDF['pmclink'].apply(find_extention) != '.gz')].index.tolist()
    
    if len(index) > 0:
        myDF.at[index,['Filepath','FileSource','pmc_status_code','pmc_error']] = myDF.loc[index,['pmclink', 'Id']].apply(fulltext_download.download_file_from_pmc_nonzip_links, subfolder = '',  outputFolder = fulltextOutputFolder, onlyPdf = onlyPdf, axis = 1)
        myDF.to_pickle(pickleDFFilename)

    # Download full text from ftp pmc zip links        
    index = myDF[(myDF['Filepath'].isna()) & (myDF['pmclink'].notna()) & (myDF['pmclink'].apply(find_extention) == '.gz')].index.tolist() 
    if len(index) > 0:
        global pmc 
        pmc = ftp_download.connect()
        
        for iindex in index:
            myDF.at[iindex,['Filepath','FileSource','pmc_status_code','pmc_error']] = fulltext_download.download_file_from_pmc_ftpzip(pmc, myDF.loc[iindex,['pmclink', 'Id']], subfolder = '', outputFolder = fulltextOutputFolder, onlyPdf = True, sleepTime= 0.3)
        
        ftp_download.disconnect()
        myDF.to_pickle(pickleDFFilename)
    
    # For those with pmcid but can't download pdf, construct fulltext http pdf link
    index = myDF[(myDF['Filepath'].isna()) & (myDF['pmcid'].notna())].index.tolist()
    if len(index) > 0:
        myDF.at[index,'pmclink'] = myDF.loc[index,'pmcid'].apply(pmc_helpers.construct_pmc_fulltext_pdf_link)
        
        myDF.at[index,['Filepath','FileSource','pmc_status_code','pmc_error']] = myDF.loc[index,['pmclink', 'Id']].apply(fulltext_download.download_file_from_pmc_nonzip_links, subfolder = '',  outputFolder = fulltextOutputFolder, onlyPdf = onlyPdf, axis = 1)
        myDF.to_pickle(pickleDFFilename)

    # myDF.to_pickle(pickleDFFilename)
    
    print(f'pdf downloaded = {sum(myDF["FileSource"] == "pmc")} pmc links')
    
    # In[4]: retrive crossref full text links
    index = (myDF['Filepath'].isna()) & (myDF['CrossrefLinks'].isna()) & (myDF['DOI'].notna())
    if len(index) > 0:
        myDF.at[index, 'CrossrefLinks'] = myDF.loc[index, 'DOI'].apply(crossref_helpers.retrive_crossref_fulltextlink_json, only_pdf = onlyPdf)
    
    myDF.to_pickle(pickleDFFilename)
    
    print(f'There are {sum(myDF["CrossrefLinks"].notna())} studies with crossref link.')
     
    index = myDF[(myDF['Filepath'].isna()) & (myDF['CrossrefLinks'].notna())].index.tolist()
    if len(index) > 0: 
        myDF.at[index,['Filepath','FileSource','crossref_status_code','crossref_error']] = myDF.loc[index,['CrossrefLinks', 'Id']].apply(fulltext_download.download_file_from_crossrefjson_links, subfolder = '',  outputFolder = fulltextOutputFolder, onlyPdf = onlyPdf, axis = 1)
        
    myDF.to_pickle(pickleDFFilename)
    
    print(f'pdf downloaded = {sum(myDF["FileSource"] == "crossref")} from crossref links')
    
    # In[5]: extract full text links with doi
    if('DoiLinks' not in myDF):
        myDF['DoiLinks'] = None
    
    index = (myDF['Filepath'].isna()) & (myDF['DOI'].notna())
    if len(index) > 0:
        myDF.at[index,'DoiLinks'] = myDF.loc[index,'DOI'].apply(doi_helpers.extract_fulltextlink_with_doi)
    
    myDF.to_pickle(pickleDFFilename)
    
    print(f'Valid metadata extracted for {sum(myDF["DoiLinks"].notna())} dois')
    
    # download full text from doi full text links
    index = (myDF['Filepath'].isna()) & (myDF['DoiLinks'].notna())
    if len(index) > 0:
        myDF.at[index,['Filepath','FileSource','doi_status_code','doi_error']] = myDF.loc[index,['DoiLinks', 'Id']].apply(fulltext_download.download_file_from_doi_links, subfolder = '',  outputFolder = fulltextOutputFolder, onlyPdf = onlyPdf, axis = 1)
       
    myDF.to_pickle(pickleDFFilename)
    print(f'pdf downloaded = {sum(myDF["FileSource"] == "doi")} Doi sourced links')
    
    # In[8]: 
    index = myDF['Filepath'].notna()
    myDF.at[index,'Filetype'] = myDF.loc[index,'Filepath'].apply(lambda x: os.path.splitext(x)[-1].replace('.',''))
    
    myDF.to_pickle(pickleDFFilename)
    myDF.to_csv(projectMetadataFilename, header = True)
    
    print('---------------------')
    n_end = sum(myDF["Filepath"].notna())
    print(f'Total number of pdfs downloaded: {n_end}')
    print(f'Performance: {sum(myDF["Filepath"].notna())/len(myDF)}')
    
    print(f'{n_end - n_start} new pdfs.')
    
    print(datetime.datetime.now())
    end = timer()
    print(f'{(end - start)/3600} hours used')
    print('---------------------')
       

       
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hi:o:', ['help', 'input=', 'output=','force_rerun','extra'])
    except getopt.GetoptError:
        usage(sys.argv[0])
        sys.exit(1)
        
    outputdirectory = ""
    rerun = False
    onlyPdf = True
    
    for opt, arg, in opts:
        if opt in ('-h', '--help'):
            usage(sys.argv[0])
            sys.exit(0)
        elif opt in ('-i', '--input'):
            inputFilename = arg
        elif opt in ('-o', '--output'):
            outputdirectory = arg
        elif opt in ('-f', '--force_rerun'):
            rerun = True
        elif opt in ('--extra'):
            onlyPdf = False
    
    if 'inputFilename' not in locals():
        usage(sys.argv[0])
        sys.exit(1)
    
    if os.path.splitext(os.path.basename(inputFilename))[1] != '.csv':
        print("Input data asks for a csv data.")
        usage(sys.argv[0])
        sys.exit(2)    
    
    process(inputFilename, outputdirectory = outputdirectory, rerun = rerun, onlyPdf = onlyPdf)
