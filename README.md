# vps-online-keeper

The cheap VPS (Virtual private server) would go offline silently sometimes. The utility script will boot VPS if it is offline.

Currently, it supports

* [ChicagoVPS](http://www.chicagovps.net/)
* [BlueVM](https://www.bluevm.com/)

## Installation

Install by pip:

	pip install vps-online-keeper

or download the latest version from github:

	git clone git://github.com/likema/vps-online-keeper.git
	cd vps-online-keeper

## Usage

boot\_vps command line arguments:

* -t|--type {chicagovps,bluevm} The type of VPS
* -u|--username USERNAME        The username of VPS client area
* -p|--password PASSWORD        The password of VPS client area
* -c|--cookies-dir COOKIES\_DIR  The directory to store http cookies, default: cookies

e.g.

	./boot_vps -t chicagovps -u <username> -p <password>
