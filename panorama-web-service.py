import web
import sys
from web import form
import json
import MySQLdb
import urllib
import time
import yaml
import os.path

# Load and parse the config.yaml file
if os.path.isfile('config.yaml'):
	stream = file('config.yaml', 'r')
else:
	web.debug("config.yaml is missing. Please provide a config file in the panorama-webservice directory. config-sample.yaml is supplied as an example.")
	raise ConfigMissing
config = yaml.load(stream)

# Set location of html templates
render = web.template.render('templates/')

# Connect urls to functions
urls = (
		'/random', 'random',
		'/add', 'add',
		'/remove', 'remove',
		'/addtocategory', 'addToCategory',
		'/removefromcategory', 'removeFromCategory',
		'/category', 'category',
		'/addbyurl', 'addByUrl',
		'/addbypaste', 'addByPaste',
		'/edit', 'edit',
		'/editpano', 'editPano',
		'/all', 'all'
	)

# Define forms
checkForm = form.Form(form.Textbox("Pano id"),
						 form.Textbox("Heading"),
						 form.Textbox("Lat"),
						 form.Textbox("Lng"),
						 form.Textbox("Title"),
						 form.Textbox("Owner"))
urlAdderForm = form.Form(form.Textbox('Json url:'))

# Connect to the database
db = web.database(dbn='mysql', user=config['user'], pw=config['password'], db=config['database'])

# Check if panoramas table exists
dbResult = db.query("SELECT COUNT(*) AS total FROM information_schema.tables WHERE table_name='panoramas'")
if dbResult[0].total == 0:
	# Create panoramas table
	db.query("""CREATE TABLE panoramas (
		id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
		gmaps_id VARCHAR(22),
		heading SMALLINT,
		lat FLOAT(9, 6),
		lng FLOAT(9, 6),
		title VARCHAR(255),
		owner VARCHAR(255),
		provider VARCHAR(255),
		qa_status VARCHAR(11), # Either 'checked' or 'not_checked'
		date_added DATE
		);""")

# Check if categories table exists
dbResult = db.query("SELECT COUNT(*) AS total FROM information_schema.tables WHERE table_name='categories'")
if dbResult[0].total == 0:
	# Create categories table
	db.query("""CREATE TABLE categories (
		id INT NOT NULL,
		FOREIGN KEY (id) REFERENCES panoramas(id),
		category_name VARCHAR(255) NOT NULL, 
		CONSTRAINT poi_id PRIMARY KEY (id, category_name)
		);""")

# Selects a random panorama from the panoramas table
class random:
	def GET(self):
		dbResult = db.query('SELECT * FROM panoramas ORDER BY RAND() LIMIT 1;')
		jsonArray = []
		for result in dbResult:
			jsonArray.append({'identifier': result.gmaps_id,
				'heading': result.heading,
				'lat': result.lat,
				'lng': result.lng,
				'title': result.title,
				'owner': result.owner,
				'qa_status': result.qa_status})
		jsonResult = {'result':jsonArray}
		web.header('Content-Type', 'application/json')
		return json.dumps(jsonResult)

# Adds a panorama to the panoramas table. 
# The check flag will determine if the check tools is used,
# Else the panorama is sent stright to the database
class add:
	def GET(self):
		webInput = web.input(check="false", id="", heading=0, lat=None, lng=None, title=None, owner=None, qa_status="not_checked", date_added=time.strftime("%Y/%m/%d"))
		if webInput.check=="true":
			# Build the checking tool form
			form = checkForm()
			form.get("Title").value = webInput.title
			form.get("Owner").value = webInput.owner

			return render.checkPano(checkForm, gmaps_id=webInput.id, heading=webInput.heading)
		
		elif webInput.id=="":
			web.ctx.status = '400 Bad Request'
			return 'explicit 400'

		else:
			db.insert('panoramas', gmaps_id=webInput.id, heading=webInput.heading, lat=webInput.lat, lng=webInput.lng, title=webInput.title, owner=webInput.owner, qa_status=webInput.qa_status, date_added=time.strftime("%Y/%m/%d"))

	# Handle data sent from the check tool				
	def POST(self):
		form = checkForm()
		if form.validates():
			db.insert('panoramas', gmaps_id=form['Pano id'].value, heading=form['Heading'].value, lat=form['Lat'].value, lng=form['Lng'].value, title=form['Title'].value, owner=form['Owner'].value, qa_status="checked", date_added=time.strftime("%Y/%m/%d"))	
		else:
			pass

# addByUrl expects a url that point to json with {result:[{id:"id", yaw:"yaw"}]}
class addByUrl:
	def GET(self):
		form = urlAdderForm()
		return render.addPanoByUrl(form)

	def POST(self):
		form = urlAdderForm()
		if not form.validates():
			return render.addPanoByUrl(form)
		else:
			url = form['Json url:'].value
			response = urllib.urlopen(url)
			data = json.loads(response.read())
			for result in data['result']:
				db.insert('panoramas', gmaps_id=result['id'], heading=result['yaw'], qa_status="not_checked", date_added=time.strftime("%Y/%m/%d"))

class addByPaste:
	def GET(self):
		pass

class category:
	def GET(self):
		webInput = web.input()
		dbResult = db.query("SELECT * FROM panoramas INNER JOIN categories ON panoramas.id=categories.id WHERE categories.category_name=$category", vars={'category':webInput.category})
		jsonArray = []
		for result in dbResult:
			jsonArray.append({'identifier':result.gmaps_id,
				'heading': result.heading,
				'lat': result.lat,
				'lng': result.lng,
				'title': result.title,
				'owner': result.owner,
				'qa_status': result.qa_status})
		jsonResult = {'result':jsonArray}
		web.header('Content-Type', 'application/json')
		return json.dumps(jsonResult)

class all:
	def GET(self):
		webInput = web.input()
		dbResult = db.select("panoramas")
		jsonArray = []
		for result in dbResult:
			jsonArray.append({'identifier':result.gmaps_id,
				'heading': result.heading,
				'lat': result.lat,
				'lng': result.lng,
				'title': result.title,
				'owner': result.owner,
				'qa_status': result.qa_status})
		jsonResult = {'result':jsonArray}
		web.header('Content-Type', 'application/json')
		return json.dumps(jsonResult)

class removeFromCategory:
	def GET(self):
		webInput = web.input(category='no data', id='no data')
		if webInput.category == 'no data' or webInput.id == 'no data':
			web.ctx.status = '400 Bad Request'
			return 'explicit 400'
		else:
			dbResult = db.select('panoramas', where="gmaps_id = $id", vars={'id':webInput.id})
			panoId = dbResult[0].id # Database id
			db.delete('categories', where="id=$id AND category_name=$category", vars={'id':panoId, 'category':webInput.category})

class addToCategory:
	def GET(self):
		webInput = web.input(category='no data', id='no data')
		if webInput.category == 'no data' or webInput.id == 'no data':
			web.ctx.status = '400 Bad Request'
			return 'explicit 400'
		else:
			dbResult = db.select('panoramas', where="gmaps_id = $id", vars={'id':webInput.id})
			panoId = dbResult[0].id # Database id
			db.insert('categories', id=panoId, category_name=webInput.category)

class edit:
	def GET(self):
		webInput = web.input(onlyNotChecked='false')
		form = checkForm()
		if webInput.onlyNotChecked == 'true':
			dbResult = db.select('panoramas', where="qa_status = 'not_checked'")
		else:
			dbResult = db.select('panoramas')
		return render.editList(dbResult, form)

	def POST(self):
		webInput = web.input(onlyNotChecked='false')
		form = checkForm()
		if not form.validates():
			pass	
		else:
			dbResult = db.select('panoramas', where="gmaps_id = $id", vars={'id':form['Pano id'].value})
			panoId = dbResult[0].id # Database id
			if webInput.form_action == "Remove":
				db.delete('categories', where="id=$id", vars={'id':panoId})
				db.delete('panoramas', where="id=$id", vars={'id':panoId})
			elif webInput.form_action == "Replace":
				db.update('panoramas', where="id = $id", vars={'id':panoId}, gmaps_id=form['Pano id'].value, heading=form['Heading'].value, lat=form['Lat'].value, lng=form['Lng'].value, title=form['Title'].value, owner=form['Owner'].value, qa_status="checked")

		if webInput.onlyNotChecked == 'true':
			dbResult = db.select('panoramas', where="qa_status = 'not_checked'")
		else:
			dbResult = db.select('panoramas')
		return render.editList(dbResult, form)

class remove:
	def GET(self):
		webInput = web.input()
		#Find pano to delete
		dbResult = db.select('panoramas', where="gmaps_id = $id", vars={'id':webInput.id})
		panoId = dbResult[0].id # Database id
		db.delete('categories', where="id=$id", vars={'id':panoId})
		db.delete('panoramas', where="id=$id", vars={'id':panoId})

if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()