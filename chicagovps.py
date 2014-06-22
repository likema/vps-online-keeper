#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
import functools
import os.path
from errno import ENOENT

import gevent
from BeautifulSoup import BeautifulSoup
from gevent import monkey

import utils

HOST = 'billing.chicagovps.net'
PRODUCTS_URL = 'https://%s/clientarea.php?action=products' % HOST
PRODUCT_DETAILS_URL = 'https://%s/clientarea.php?action=productdetails' % HOST
LOGIN_URL = 'https://%s/dologin.php' % HOST
SYLOSVM_AJAX_URL = 'https://%s/clientarea.php?sylusvm_ajax=1' % HOST

SERVER_ID_CHECKER = re.compile(r'"vserverid"\s*:\s*"(\d+)"')


def servers(username, password, session, cookies_dir):
    cookie_fname = os.path.join(cookies_dir, username)

    try:
        session.cookies = utils.load_cookies_from_lwp(cookie_fname)
        logging.info('Cookie is loaded from %s', cookie_fname)
    except Exception as e:
        if not isinstance(e, IOError) or e.errno != ENOENT:
            logging.warning("Failed to load cookies from %s, %s",
                            cookie_fname, e)

    res = session.get(PRODUCTS_URL)
    res.raise_for_status()

    soup = BeautifulSoup(res.text)
    table = soup.find('table')
    if table is None:  # Not logged in?
        data = dict(username=username, password=password)
        data.update(utils.retrieve_hidden_tokens(soup,
                                                 form_name='frmlogin',
                                                 names=('token', )))

        body = utils.login(session, LOGIN_URL, PRODUCTS_URL, **data)
        soup = BeautifulSoup(body)
        table = soup.find('table')
        if table is not None:
            utils.save_cookies_lwp(session.cookies, cookie_fname)
            logging.info('Cookie is saved to %s', cookie_fname)

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
                       data=dict(token=token, id=id_))
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

args = utils.init_args('Boot ChicagoVPS if they are offline.')
session = utils.make_session()
boot = functools.partial(boot_server, session=session)
gevent.joinall([gevent.spawn(boot, **i)
                for i in servers(args.username, args.password, session,
                                 args.cookies_dir)])

# vim: ts=4 sw=4 sts=4 et:
