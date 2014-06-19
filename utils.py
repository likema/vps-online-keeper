# -*- coding: utf-8 -*-

import argparse
import httplib
import logging

import requests
from BeautifulSoup import BeautifulSoup

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


def retrieve_hidden_tokens(session, url, **kwargs):
    if 'form_id' in kwargs:
        form_attrs = dict(id=kwargs['form_id'])
    elif 'form_name' in kwargs:
        form_attrs = dict(name=kwargs['form_name'])
    else:
        return ()

    names = kwargs.get('names')
    if not names:
        return ()

    res = session.get(url, verify=kwargs.get('verify', True))
    res.raise_for_status()
    soup = BeautifulSoup(res.text)
    form = soup.find('form', attrs=form_attrs)

    return dict([(i, hidden_input_value(form, i)) for i in names])


def login(session, url, referer, **data):
    res = session.post(url,
                       headers={'Referer': referer},
                       data=data)
    res.raise_for_status()
    return res.text


def init_args(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    return parser.parse_args()

# vim: ts=4 sw=4 sts=4 et:
