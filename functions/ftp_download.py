#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 10:31:49 2020

https://docs.python.org/3/library/ftplib.html
@author: jliao
"""
import ftplib
import io
import os
import sys
import tarfile
import time

def connect():
  '''Connect to the PMC OAS FTP server'''

  print('Connecting to ftp.ncbi.nlm.nih.gov')
  global pmc
  try:
    pmc = ftplib.FTP('ftp.ncbi.nlm.nih.gov')
    pmc.login()
    # pmc.cwd('/pub/pmc')
    pmc.set_pasv(True)
  except Exception as e:
    print (e)
    abort(1)
  return(pmc)

def disconnect():
  '''Disconnect from the PMC OAS FTP server'''
  global pmc
  print('Disconnecting from ftp.ncbi.nlm.nih.gov')
  pmc.close()

def reconnect():
  '''
  Disconnect and then reconnect to the PMC OAS FTP server. This is sometimes
  required because the server can intermittently throw 550 errors, indicating
  that a legitimate file does not exist. When this happens, we reconnect to the
  server and try again.
  '''
  global pmc
  time.sleep(10)
  disconnect()
  time.sleep(10)
  pmc = connect()
  return(pmc)

def rest(delay = 0.3):
  '''
  We have to be nice to the PMC servers or we may be blocked. The pause here
  ensures that we are making no more than around 3 requests per second.
  Decrease the length of the pause at your own risk.
  '''

  time.sleep(delay)

def abort(code):
    global pmc
    if pmc:
        disconnect()
    sys.exit(code)

def extract_pdf(infile, outfile, ignore):
  '''
  Download and extract an article pdf from the PMC OAS FTP Service. We make
  a maximum of four attempts to download an archive before giving up. If we
  have to give up, we either skip the file and continue downloading or abort,
  depending on the --abort-on-error command line flag.
  
  infile   -- the name of the file to download
  outfile -- the local directory in which to store the file
  '''
  global pmc
  n_attempt = 2
  try:
    attempt = 0
    while True:
      attempt += 1
      try:
        # n_requests += 1                
        with open(outfile, "wb") as lf:
            pmc.retrbinary("RETR " + infile, lf.write, 33554432)
        break
      except Exception as e:
        print('{0}, attempt {1}/{2}'.format(e, attempt,n_attempt))
        reconnect(pmc)
        if attempt > n_attempt-1:
          raise e
  except Exception as e:
    if not ignore:
      print('{0}, aborting...'.format(e))
      abort(pmc, 1) 
    else:
      print('{0}, ignoring...'.format(e))
      rest(0.3)
      return

  rest()

def files_to_extract(members, outfilename):
  '''Generates the files we want to extract from each archive'''
  
  for m in members:
    if os.path.splitext(m.name.lower())[1] == '.pdf':
        m.name = outfilename + '.pdf'
        yield m

def extract_gzip(infile, outfile, ignore = True, sleepTime = 0.3, onlyPdf = True):
  '''
  Download and extract an article archive from the PMC OAS FTP Service. We make
  a maximum of four attempts to download an archive before giving up. If we
  have to give up, we either skip the file and continue downloading or abort,
  depending on the --abort-on-error command line flag.
  
  infile   -- the name of the file to download
  outfile -- the local directory in which to store the file
  '''
  global pmc
  
  infile = infile.replace("ftp://ftp.ncbi.nlm.nih.gov","")
  directory = os.path.dirname(outfile)
  outfilename = os.path.basename(outfile)
  n_attempt = 3
  output = {'pmc_error': None,
              'pmc_status_code': None,
              'Filepath': None
             }
  
  if not os.path.exists(directory):
      os.makedirs(directory)
  
  response = io.BytesIO()
  tar = None
  extracted = False
  try:
    attempt = 0
    while True:
      attempt += 1
      try:
        pmc.retrbinary("RETR " + infile, response.write, 33554432)
        tar = tarfile.open(fileobj=io.BytesIO(response.getvalue()),mode="r:gz")                
        has_pdf = False
        for m in tar:
            if os.path.splitext(m.name.lower())[1] == '.pdf':
                outfile = outfile + ".pdf"
                has_pdf = True
        if has_pdf:
            tar.extractall(path = directory, members = files_to_extract(tar, outfilename))
            extracted = True
        break
      except Exception as e:
        print('{0}, attempt {1}/{2}'.format(e, attempt, n_attempt))
        pmc = reconnect(pmc)
        if attempt > n_attempt-1:
          raise e
  except Exception as e:
    output['error'] = e
    if not ignore:
      print('{0}, aborting...'.format(e))
      abort(pmc, 1) 
    else:
      print('{0}, ignoring...'.format(e))
      rest(sleepTime)
      return(output)
  finally:
    response.close()
    if tar:
      tar.close()
  
  rest(sleepTime)

  if extracted:
      output['Filepath'] = outfile

  return(output)

def download_files():
  '''
  Connect to the PubMed Central Open Access Subset FTP service and attempt to
  download and extract each archive listed in file_list.txt.gz
  '''
  global pmc
  
  pmc = connect()

  input_filename =  "/pub/pmc/oa_package/00/00/PMC1790863.tar.gz"
    
  output_dir = "../test/" 
  
  output_filename = output_dir + os.path.basename(input_filename)
  ignore = True
  
  extract_pdf(pmc, input_filename, output_filename, ignore)

  disconnect()

# def download_pdf_zip(input_filename, output_filename):
  # '''
  # Connect to the PubMed Central Open Access Subset FTP service and attempt to
  # download and extract each archive listed in file_list.txt.gz
  # '''
  # global pmc
  
  # pmc = connect()

  # input_filename = "/pub/pmc/oa_package/00/00/PMC1790863.tar.gz"
  # output_dir = "../test/" 
  
  # output_filename = output_dir + "text.pdf"
  # ignore = True
    
  # extract_gzip(pmc, input_filename, output_filename, ignore)
# 
  # disconnect()
