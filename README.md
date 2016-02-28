Panorama Web Service
============
19/08/2015 Web Service by Nicholas Verstegen developed for use with Peruse-a-rue Liquid Galaxy application

### INSTALL

Requires web.py, mysqdb and mysql-server.
PyYAML is provided but must be installed.

The following commands for setup were run on Ubuntu:

	$ sudo apt-get install python-setuptools
	$ sudo easy_install web.py

	$ sudo apt-get install python-mysqldb

	$ sudo apt-get install mysql-server

Move to ./panorama-webservice/PyYAML-3.11 then
	$ sudo python setup.py install

### DATABASE SETUP

	$ CREATE DATABASE panoramas;

### CONFIG

User, password and name for database are set in config.yaml.
Web service will crash without a config.yaml file present in the panoramas-webservice dir.
config-sample.yaml is supplied as an example.

### USE

The webservice is run with the python interpreter:

	$ python ./panorama-web-service.py

Port in use should be shown on console on start-up.

/add and checking tool

	New panoramas can be added to the database one by one with the /add url. Pass the arguments id, heading, lat, lng, title, provider and qa_status with GET. id is compolsory, heading will be set to 0 as default and other attributes will be NULL if not set. Set qa_status argument to 'not_checked' if it needs to be looked over later otherwise set it to 'checked' if you're confident it is correct. qa_status defaults to 'not_checked'.

	Set the 'check' argument to 'true' to display the checking tool. This displays a panorama view and form for adjusting/finding information before submitting. Entering panos with the checking tool submit button will automatically make the 'checked'.

/addbyurl

	Serves a form for input of a url to a json file to add a large number of panos. Currently expects each pano to have a 'yaw' and 'id'. i.e. {result:[{id:"id", yaw:"yaw"}, {id:"id", yaw:"yaw"}, ......]}
	Panos entered this was are marked as 'not_checked'.

/addpaste

	Not yet implemented.

/all

	Returns JSON for all the panoramas in the database.

/edit
	
	Shows a list of all panoramas or if onlyNotChecked=true then a list of all unchecked panos. The 'Edit' button on each pano will open the checking tool for that pano. Use 'Replace' or 'Remove' buttons. Replaced panos will become 'checked'.

/remove

	Provide the an id argument via GET and panoramas with this id will be removed from the database.

/random 

	Will select randomly from all panoramas in the database

/category

	Provide a category argument via GET. JSON for all panoramas in the specified category will be returned.

/removefromcategory

	Provide a category and id argument via GET. The specified panorama will be removed from the specified category.

/addtocategory

	Provide a category and id argument via GET. The specified panorama will be added to the specified category.
