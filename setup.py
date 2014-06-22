# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='vps-online-keeper',
    version='1.0.2',
    description='Keep various VPS online',
    url='https://github.com/likema/vps-online-keeper',
    download_url=('https://github.com/likema/vps-online-keeper'
                  '/archive/master.zip'),
    author='Like Ma',
    author_email='likemartinma@gmail.com',
    license='GPLv3',
    packages=['vps'],
    scripts=['boot_vps'],
    install_requires=[
        'BeautifulSoup',
        'gevent >= 0.13.6',
        'requests >= 2.0',
    ],
    classifiers=[
        'Topic :: Utilities',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'])

# vim: ts=4 sw=4 sts=4 et:
