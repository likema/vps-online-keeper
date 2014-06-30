# -*- coding: utf-8 -*-

import urlparse
import logging
import os.path

from BeautifulSoup import BeautifulSoup

import utils

HOME_URL = 'https://feathur.bluevm.com/'
VIEW_URL = 'https://feathur.bluevm.com/view.php'
LOGIN_URL = 'https://feathur.bluevm.com/index.php?action=login'


def servers(email, password, session, cookies_dir):
    cookie_fname = os.path.join(cookies_dir, email)
    session.cookies = utils.load_cookies_from_lwp(cookie_fname)

    res = session.get(HOME_URL, timeout=utils.REQUEST_TIMEOUT)
    res.raise_for_status()

    soup = BeautifulSoup(res.text)
    table = soup.find('table')
    if table is None:  # Not logged in?
        data = dict(email=email, password=password)
        data.update(utils.retrieve_hidden_tokens(soup,
                                                 form_id='form1',
                                                 names=('_CPHP_CSRF_KEY',
                                                        '_CPHP_CSRF_TOKEN')))

        soup = BeautifulSoup(utils.login(session, LOGIN_URL, HOME_URL, **data))
        table = soup.find('table')

        if table is not None:
            utils.save_cookies_lwp(session.cookies, cookie_fname)

    for tr in table.find('tbody').findAll('tr'):
        _, name, _, _, ip, service = tr.findAll('td')

        name = name.find('a').find(text=True)
        ip = ip.find('div').find(text=True)

        href = service.find('a')['href']
        id_ = urlparse.parse_qs(urlparse.urlparse(href).query)['id'][0]

        yield dict(name=name, ip=ip, id_=id_)


def server_status(session, id_):
    res = session.get(VIEW_URL, params=dict(id=id_, action='statistics'),
                      timeout=utils.REQUEST_TIMEOUT)
    res.raise_for_status()
    return res.json()['result']  # online


def boot_server(session, name, ip, id_):
    status = server_status(session, id_)
    if status != 'offline':
        logging.info('%s (%s) is %s.', name, ip, status)
        return

    res = session.get(VIEW_URL, params=dict(id=id_, action='boot'),
                      timeout=utils.REQUEST_TIMEOUT)
    res.raise_for_status()


# vim: ts=4 sw=4 sts=4 et:
