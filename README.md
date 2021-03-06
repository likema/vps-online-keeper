# vps-online-keeper

The cheap VPS (Virtual private server) would go offline silently sometimes. The utility script will boot VPS if it is offline.

Currently, it supports

* [ChicagoVPS](http://www.chicagovps.net/)
* [BlueVM](https://www.bluevm.com/)
* [URPad](http://urpad.net/)
* [123system](https://123systems.net/)

## Installation

Install by pip:

	pip install vps-online-keeper

or download the latest version from github:

	git clone git://github.com/likema/vps-online-keeper.git
	cd vps-online-keeper

If running source code under Debian/Ubuntu, please install dependencies by

	sudo apt-get install python-beautifulsoup python-requests python-gevent
	
## Usage

boot\_vps command line arguments:

* -t|--type {chicagovps,bluevm} The type of VPS
* -u|--username USERNAME        The username of VPS client area
* -p|--password PASSWORD        The password of VPS client area
* -c|--cookies-dir COOKIES\_DIR  The directory to store http cookies, default: cookies

e.g.

	./boot_vps -t chicagovps -u <username> -p <password>
	
For keeping your VPS online, your can add the above command into cron by
	
	crontab -e

	*/15 * * * * <srcdir>/boot_vps -t chicagovps -u <username> -p <password>
	
and it will be run every 15 minutes.
