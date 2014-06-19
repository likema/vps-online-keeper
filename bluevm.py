#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urlparse
import logging
import functools

import utils

import gevent
from BeautifulSoup import BeautifulSoup
from gevent import monkey

HOME_URL = 'https://feathur.bluevm.com/'
VIEW_URL = 'https://feathur.bluevm.com/view.php'
LOGIN_URL = 'https://feathur.bluevm.com/index.php?action=login'

def servers(email, password, session):
    data = dict(email=email, password=password)
    data.update(utils.retrieve_hidden_tokens(session, HOME_URL,
                                             form_id='form1', verify=False,
                                             names=('_CPHP_CSRF_KEY',
                                                    '_CPHP_CSRF_TOKEN')))

    soup = BeautifulSoup(utils.login(session, LOGIN_URL, HOME_URL, **data))
    table = soup.find('table')

    for tr in table.find('tbody').findAll('tr'):
        _, name, _, _, ip, service = tr.findAll('td')

        name = name.find('a').find(text=True)
        ip = ip.find('div').find(text=True)

        href = service.find('a')['href']
        id_ = urlparse.parse_qs(urlparse.urlparse(href).query)['id'][0]

        yield dict(name=name, ip=ip, id_=id_)


def server_status(session, id_):
    res = session.get(VIEW_URL, params=dict(id=id_, action='statistics'))
    res.raise_for_status()
    return res.json()['result']  # online


def boot_server(session, name, ip, id_):
    status = server_status(session, id_)
    if status != 'offline':
        logging.info('%s (%s) is %s', name, ip, status)
        return

    res = session.get(VIEW_URL, params=dict(id=id_, action='boot'))
    res.raise_for_status()


monkey.patch_all(thread=False, select=False)
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

args = utils.init_args('Boot BlueVM VPS if they are offline.')
session = utils.make_session()
boot = functools.partial(boot_server, session=session)
gevent.joinall([gevent.spawn(boot, **i)
                for i in servers(args.username, args.password, session)])

# vim: ts=4 sw=4 sts=4 et:
