13/07/2015 Web Service by Nicholas Verstegen developed for use with Peruse-a-rue Liquid Galaxy application

*****************************************

INSTALL

Requires web.py, mysqdb and mysql-server

$ sudo apt-get install python-setuptools
$ sudo easy_install web.py

$ sudo apt-get install python-mysqldb

$ sudo apt-get install mysql-server

*****************************************

DATABASE SETUP

CREATE DATABASE panoramas;

User and password are set at the top of poi-web-service.py with USER and PW constants.

*****************************************

USE

Port in use should be shown on console on start-up.

/add?id=pano_id&heading=pano_heading&lat=pano_lat&lng=pano_lng&title=pano_title&provider=pano_provider

/add - shows a form for input of a url to a json file to add a large number of panos. Currently expects each pano to have a 'yaw' and 'id'.

/remove?id=pano_id

/random - will select randomly from all panoramas added

/poi - lists all tables in the database

/poi?category=poi_category - json dump of the selected category

/poi?catergory=poi_category&id=pano_id - adds the panorama to the category