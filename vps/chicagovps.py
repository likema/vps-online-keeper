# -*- coding: utf-8 -*-

import logging
import re
import os.path

from BeautifulSoup import BeautifulSoup

import utils

HOST = 'billing.chicagovps.net'
PRODUCTS_URL = 'https://%s/clientarea.php?action=products' % HOST
PRODUCT_DETAILS_URL = 'https://%s/clientarea.php?action=productdetails' % HOST
LOGIN_URL = 'https://%s/dologin.php' % HOST
SYLOSVM_AJAX_URL = 'https://%s/clientarea.php?sylusvm_ajax=1' % HOST

SERVER_ID_CHECKER = re.compile(r'"vserverid"\s*:\s*"(\d+)"')


def servers(username, password, session, cookies_dir):
    cookie_fname = os.path.join(cookies_dir, username)
    session.cookies = utils.load_cookies_from_lwp(cookie_fname)

    res = session.get(PRODUCTS_URL, timeout=utils.REQUEST_TIMEOUT)
    res.raise_for_status()

    soup = BeautifulSoup(res.text)
    table = soup.find('table')
    if table is None:  # Not logged in?
        data = dict(username=username, password=password, rememberme='on')
        data.update(utils.retrieve_hidden_tokens(soup,
                                                 form_name='frmlogin',
                                                 names=('token', )))

        body = utils.login(session, LOGIN_URL, PRODUCTS_URL, **data)
        soup = BeautifulSoup(body)
        table = soup.find('table')
        if table is not None:
            utils.save_cookies_lwp(session.cookies, cookie_fname)

    for tr in table.find('tbody').findAll('tr'):
        service, _, _, _, status, details = tr.findAll('td')
        if status.find(text=True).lower() != 'active':
            continue

        name = service.find('a').find(text=True)
        form = details.find('form')
        token = utils.hidden_input_value(form, 'token')
        id_ = utils.hidden_input_value(form, 'id')
        yield dict(name=name, token=token, id_=id_)


def boot_server(session, name, token, id_):
    res = session.post(PRODUCT_DETAILS_URL,
                       headers=dict(Referer=PRODUCTS_URL),
                       data=dict(token=token, id=id_),
                       timeout=utils.REQUEST_TIMEOUT)
    res.raise_for_status()
    soup = BeautifulSoup(res.text)
    solus_status = soup.find('td', attrs=dict(id='solus_status'))
    solus_status_strong = solus_status.find('strong')
    solus_status_text = solus_status_strong.find(text=True).lower()
    if solus_status_text != 'offline':
        logging.info('%s is %s.', name, solus_status_text)
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
                                 id=id_),
                       timeout=utils.REQUEST_TIMEOUT)
    res.raise_for_status()
    body = res.json()
    if body.get('success'):
        logging.info('%s is booted: %s', name, body.get('result'))
    else:
        logging.error('Failed to boot %s, %s', name, body)


# vim: ts=4 sw=4 sts=4 et:
