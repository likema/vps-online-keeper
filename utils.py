# -*- coding: utf-8 -*-

import argparse
import httplib
import logging
import cookielib
import sys
import os.path
from errno import ENOENT

import requests

USER_AGENT = 'Mozilla/5.0'


def enable_requests_debug():
    httplib.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def make_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': USER_AGENT,
    })
    return session


def hidden_input_value(form, name):
    return form.find('input', attrs=dict(type='hidden', name=name))['value']


def retrieve_hidden_tokens(soup, **kwargs):
    if 'form_id' in kwargs:
        form_attrs = dict(id=kwargs['form_id'])
    elif 'form_name' in kwargs:
        form_attrs = dict(name=kwargs['form_name'])
    else:
        return ()

    names = kwargs.get('names')
    if not names:
        return ()

    form = soup.find('form', attrs=form_attrs)
    return dict([(i, hidden_input_value(form, i)) for i in names])


def save_cookies_lwp(cookiejar, fname):
    lwp_cookiejar = cookielib.LWPCookieJar()

    for i in cookiejar:
        args = dict(vars(i).items())
        args['rest'] = args['_rest']
        del args['_rest']
        lwp_cookiejar.set_cookie(cookielib.Cookie(**args))

    lwp_cookiejar.save(fname, ignore_discard=True)
    logging.info('Cookie is saved to %s', fname)


def load_cookies_from_lwp(fname):
    lwp_cookiejar = cookielib.LWPCookieJar()

    try:
        lwp_cookiejar.load(fname, ignore_discard=True)
        logging.info('Cookie is loaded from %s', fname)
    except Exception as e:
        if not isinstance(e, IOError) or e.errno != ENOENT:
            logging.warning("Failed to load cookies from %s, %s", fname, e)

    return lwp_cookiejar


def login(session, url, referer, **data):
    res = session.post(url,
                       headers={'Referer': referer},
                       data=data)
    res.raise_for_status()
    return res.text


def init_args(description):
    cookies_dir = os.path.join(os.path.dirname(sys.argv[0]), 'cookies')
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-c', '--cookies-dir', default=cookies_dir)
    return parser.parse_args()

# vim: ts=4 sw=4 sts=4 et:
