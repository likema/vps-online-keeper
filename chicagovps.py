#!/usr/bin/python

import logging
import httplib
import re

import requests
import gevent
from BeautifulSoup import BeautifulSoup
from gevent import monkey

USER_AGENT = 'Mozilla/5.0'
USERNAME = ''
PASSWORD = ''

HOST = 'billing.chicagovps.net'
PRODUCTS_URL = 'https://%s/clientarea.php?action=products' % HOST
PRODUCT_DETAILS_URL = 'https://%s/clientarea.php?action=productdetails' % HOST
LOGIN_URL = 'https://%s/dologin.php' % HOST
SYLOSVM_AJAX_URL = 'https://%s/clientarea.php?sylusvm_ajax=1' % HOST

SERVER_ID_CHECKER = re.compile(r'"vserverid"\s*:\s*"(\d+)"')


def enable_requests_debug():
    httplib.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def hidden_input_value(form, name):
    return form.find('input', attrs=dict(type='hidden', name=name))['value']


def retrieve_token(session):
    res = session.get(PRODUCTS_URL)
    res.raise_for_status()
    soup = BeautifulSoup(res.text)
    form = soup.find('form', attrs=dict(name='frmlogin'))
    return hidden_input_value(form, 'token')


def login(session, token, username, password):
    res = session.post(LOGIN_URL,
                       headers=dict(Referer=PRODUCTS_URL),
                       data=dict(token=token,
                                 username=username,
                                 password=password))
    res.raise_for_status()
    return res.text


def servers(session):
    soup = BeautifulSoup(login(session, retrieve_token(session),
                               USERNAME, PASSWORD))
    for tr in soup.find('table').find('tbody').findAll('tr'):
        service, _, _, _, status, details = tr.findAll('td')
        if status.find(text=True).lower() != 'active':
            continue

        name = service.find('a').find(text=True)
        form = details.find('form')
        token = hidden_input_value(form, 'token')
        id_ = hidden_input_value(form, 'id')
        yield dict(name=name, token=token, id_=id_)


def boot_server(name, token, id_):
    res = session.post(PRODUCT_DETAILS_URL,
                       headers=dict(Referer=PRODUCTS_URL),
                       data=dict(token=token, id=id_))
    res.raise_for_status()
    soup = BeautifulSoup(res.text)
    solus_status = soup.find('td', attrs=dict(id='solus_status'))
    solus_status_strong = solus_status.find('strong')
    solus_status_text = solus_status_strong.find(text=True).lower()
    if solus_status_text != 'offline':
        logging.info('%s is %s', name, solus_status_text)
        return

    m = SERVER_ID_CHECKER.search(res.text)
    if m:
        server_id = m.group(1)
    else:
        logging.error('Unable to find server_id of %s', name)
        return

    res = session.post(SYLOSVM_AJAX_URL,
                       headers={
                           'Referer': PRODUCT_DETAILS_URL,
                           'X-Requested-With': 'XMLHttpRequest'
                       },
                       data=dict(sylusvm_act='sylusvm_boot',
                                 vserverid=server_id,
                                 id=id_))
    res.raise_for_status()
    body = res.json()
    if body.get('success'):
        logging.info('%s is booted: %s', name, body.get('result'))
    else:
        logging.error('Failed to boot %s, %s', name, body)


monkey.patch_all(thread=False, select=False)
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

session = requests.Session()
session.headers.update({
    'User-Agent': USER_AGENT,
})

gevent.joinall([gevent.spawn(boot_server, **i) for i in servers(session)])

# vim: ts=4 sw=4 sts=4 et:
