#!/usr/bin/env python
# coding: utf-8

# ### Request Functions

from requests.exceptions import HTTPError
#from requests.exceptions import Timeout
from requests.exceptions import ConnectionError
# This function allow to ping a request regardless of input and output, getting a standard output.
def get_request(url, http, headers, timeout):
    response_d = {}
    status_code = None
    headers = None
    text = None
    r_url = None
    content = None

    # we're going to set up a try except system so that the mosts common errors call standard outputs which we can work in to our output.
    try:
        r = http.get(url, headers = headers, timeout = timeout, allow_redirects = True, stream = True)
        r.raise_for_status()
        #now we have a set of multiple exceptions that might occur
    except HTTPError as err:
 #       print(f"HTTP error occurred:\n{err}")
        status_code = r.status_code
        exception = err
    except Exception as err:
        # print(f'Another sort of error occured: \n{err}')
        exception = err
    except timeout:
        # print('Request timed out')
        exception = 'timeout'
    except ConnectionError as ce:
        # print(f'Max Retries error:\n{ce}')
        exception = ce
    else:
        # print('No Exceptions Occured')
        exception = None
        status_code = r.status_code
        headers = r.headers
        text = r.text
        r_url = r.url
        content = r.content

    finally:
        response_d.update({'status_code':status_code, 'headers':headers, 'text':text, 'url':r_url, 'error':exception, 'content': content})

    return response_d 