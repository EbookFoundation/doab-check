#!/usr/bin/env python
# encoding: utf-8

import logging
import re
import threading
import time
from urllib.parse import quote, unquote, urlparse, urlsplit, urlunsplit

import requests

from django.conf import settings

from .models import Check, Link

HEADERS = {"User-Agent": settings.USER_AGENT}

DELAYS = {
    'oapen.org': 0.05,
    '*': 0.5,
}

logger = logging.getLogger(__name__)

class ContentTyper(object):
    """ won't make more checks faster than the DELAY set for the host """
    def __init__(self):
        self.last_call = dict()

    def content_type(self, url):
        try:
            try:
                r = requests.get(url, allow_redirects=True, headers=HEADERS)
            except UnicodeDecodeError as ude:
                # fallback for non-ascii, non-utf8 bytes in redirect location
                if 'utf-8' in str(ude):
                    (scheme, netloc, path, query, fragment) = urlsplit(url)
                    newpath = quote(unquote(path), encoding='latin1')
                    url = urlunsplit((scheme, netloc, newpath, query, fragment))
                    r = requests.get(url, allow_redirects=True, headers=HEADERS)
                    if r.status_code == 200:
                        r.status_code = 214 # unofficial status code where url is changed
            if r.status_code == 405:
                r =  requests.get(url, headers=HEADERS)
            return r
        except requests.exceptions.SSLError:
            r = requests.get(url, verify=False)
            r.status_code = 511
            return r
        except requests.exceptions.ConnectionError as ce:
            if '[Errno 8]' in str(ce) or '[Errno -2]' in str(ce):
                try:
                    r = requests.get(url, allow_redirects=False, headers=HEADERS)
                    return r
                except Exception as e:
                    pass
            elif ('TimeoutError' in str(ce) or 
                  'ConnectionTimeout' in str(ce) or 
                  '[Errno 60]' in str(ce)):
                # server didn't respond in a reasonable time
                return (524, '', '')
            elif '[Errno 111]' in str(ce) or 'Max retries' in str(ce):
                # I'm a teapot, I hate you
                return (418, '', '')
            # unexplained connection error
            logger.exception(ce)
        except Exception as e:
            # unexplained error
            logger.exception(type(e))
            logger.exception(e)
            return None

    def calc_type(self, url):
        logger.info(url)
        # is there a delay associated with the url
        netloc = urlparse(url).netloc
        delay = DELAYS.get(netloc, DELAYS.get('*'))

        # wait if necessary
        last_call = self.last_call.get(netloc)
        if last_call is not None:
            now = time.time()
            min_time_next_call = last_call + delay
            if min_time_next_call > now:
                time.sleep(min_time_next_call-now)

        self.last_call[netloc] = time.time()

        # compute the content-type
        
        return self.content_type(url)

contenttyper = ContentTyper()

RE_EBOOK_TYPES = re.compile(r'(epub|pdf|mobi)', flags=re.I)

def response_parts(response):
    ''' return code, content type, content disposition handling any missing data'''
    if response == None:
        return 0, '', ''
    if isinstance(response, tuple):
        return response
    try:
        if response.status_code == 404:
            return 404, '', ''
        cdisp = response.headers.get('content-disposition', '')
        return response.status_code, response.headers.get('content-type', ''), cdisp
    except:
        return response.status_code, '', ''
    


def type_for_url(url, response=None):
    ''' check a url to see what's there. the content-disposition header is often needed to 
        dermine the type of file i.e. pdf, epub, etc. at the end of the link '''
    if not url and not response:
        return ''

    if response:
        code, ct, disposition = response_parts(response)
        url = response.url
    else:
        code, ct, disposition = response_parts(contenttyper.calc_type(url))
    url_disp = url + disposition
    if code == 404:
        return 404, ''
    binary_type = re.search("octet-stream", ct) or re.search("application/binary", ct)
    ebook_type_match = RE_EBOOK_TYPES.search(url_disp)
    if re.search("pdf", ct):
        return code, "pdf"
    elif binary_type and ebook_type_match:
        return code, ebook_type_match.group(1).lower()
    elif re.search("text/plain", ct):
        return code, "text"
    elif re.search("text/html", ct):
        return code, "html"
    elif re.search("epub", ct):
        return code, "epub"
    elif re.search("mobi", ct):
        return code, "mobi"
    # no content-type header?
    elif ebook_type_match:
        return code, ebook_type_match.group(1).lower()

    return code, f'other; {ct}'

def check_link(link):
    ''' given a Link object, check its URL, put the result in a Check object '''
    check = Check(link=link)
    code, ct =  type_for_url(link.url)
    check.return_code = code
    check.content_type = ct
    check.save()
    check.link.recent_check = check
    check.link.save()
    return check

def check_links(queryset):
    for link in queryset:
        check = check_link(link)

def start_check_links(queryset):
    checker = threading.Thread(target=check_links, args=(queryset,), daemon=True)
    checker.start()
    return 'checker has started checking'
    
