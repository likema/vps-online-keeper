# -*- coding: utf-8 -*-

import logging
import re
import os.path

from BeautifulSoup import BeautifulSoup

import utils

HOST = 'billing.urpad.net'
PRODUCTS_URL = 'https://%s/clientarea.php?action=products' % HOST
PRODUCT_DETAILS_URL = 'https://%s/clientarea.php?action=productdetails' % HOST
LOGIN_URL = 'https://%s/dologin.php' % HOST
SYLOSVM_AJAX_URL = 'https://%s/clientarea.php?sylusvm_ajax=1' % HOST

SERVER_ID_CHECKER = re.compile(r'"vserverid"\s*:\s*"(\d+)"')


def servers(username, password, session, cookies_dir):
    cookie_fname = os.path.join(cookies_dir, username)
    session.cookies = utils.load_cookies_from_lwp(cookie_fname)

    res = session.get(PRODUCTS_URL, verify=False)
    res.raise_for_status()

    soup = BeautifulSoup(res.text)
    table = soup.find('table')
    if table is None:  # Not logged in?
        data = dict(username=username, password=password)
        data.update(utils.retrieve_hidden_tokens(soup,
                                                 form_action='dologin.php',
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
        yield dict(name=name, href=details.find('a')['href'])


def boot_server(session, name, href):
    url = 'https://%s/%s' % (HOST , href)
    res = session.get(url, headers=dict(Referer=PRODUCTS_URL))
    res.raise_for_status()
    soup = BeautifulSoup(res.text)
    status = soup.find('strong').find(text=True).lower()
    if status != 'offline':
        logging.info('%s is %s.', name, status)
        return

    session.get(url + '&modop=custom&a=boot')
    res.raise_for_status()

# vim: ts=4 sw=4 sts=4 et:
