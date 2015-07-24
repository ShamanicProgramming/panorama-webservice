import web
from web import form
import json
import MySQLdb
import urllib

USER = 'root'
PW = ''

render = web.template.render('templates/')

urls = (
		'/random', 'random',
		'/add', 'add',
		'/remove', 'remove',
		'/poi', 'poi'
	)

db = web.database(dbn='mysql', user=USER, pw=PW, db='panoramas')
dbResult = db.query("SELECT COUNT(*) AS total FROM information_schema.tables WHERE table_name='panorama'")
if dbResult[0].total == 0:
	db.query("""CREATE TABLE panorama (
		id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
		gmaps_id VARCHAR(22),
		heading SMALLINT,
		lat FLOAT(9, 6),
		lng FLOAT(9, 6),
		title VARCHAR(128),
		provider VARCHAR(128)
		);""")

adderForm = form.Form(form.Textbox('Json url:'))

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

class random:
	def GET(self):
		dbResult = db.query('SELECT * FROM panorama ORDER BY RAND() LIMIT 1;')
		jsonArray = []
		for result in dbResult:
			jsonArray.append({'identifier': result.gmaps_id,
				'heading': result.heading,
				'lat': result.lat,
				'lng': result.lng,
				'title': result.title,
				'provider': result.provider})
		jsonResult = {'result':jsonArray}
		web.header('Content-Type', 'application/json')
		return json.dumps(jsonResult)

class add:
	def GET(self):
		getInput = web.input(id="no data")
		if getInput.id == "no data":
			form = adderForm()
			return render.addPanoForm(form)
		else:
			db.insert('panorama', gmaps_id=getInput.id, heading=getInput.heading, lat=getInput.lat, lng=getInput.lng, title=getInput.title, provider=getInput.provider)

	def POST(self):
		form = adderForm()
		if not form.validates():
			return render.addPanoForm(form)
		else:
			url = form['Json url:'].value
			response = urllib.urlopen(url)
			data = json.loads(response.read())
			for result in data['result']:
				db.insert('panorama', gmaps_id=result['id'], heading=result['yaw'])

class remove:
	def GET(self):
		getInput = web.input()
		#Find pano to delete
		dbResult = db.query("SELECT id FROM panorama WHERE gmaps_id='"+ getInput.id +"'")
		panoId = dbResult[0].id
		#Get list of all tables 
		dbResult = db.query("SELECT table_name FROM information_schema.tables WHERE table_schema='panoramas';")
		for result in dbResult:
			#Delete pano from categories first
			if result.table_name != 'panorama':
				db.delete(result.table_name, where="id='" +str(panoId)+ "'")
				#Delete category if no rows left
				dbResult2 = db.query("SELECT COUNT(*) AS total FROM " + result.table_name)
				if dbResult2[0].total == 0:
					db.query("DROP TABLES "+ result.table_name)
		db.delete("panorama", where="id='" +str(panoId)+ "'")

class poi:
	def GET(self):
		getInput = web.input(category='no data', id='no data')
		if getInput.category == 'no data':
			#List all tables
			tables = []
			dbResult = db.query("SELECT table_name FROM information_schema.tables WHERE table_schema='panoramas';")
			for table in dbResult:
				tables.append(table.table_name)
			return tables
		elif getInput.id == 'no data':
			#Return panoramas in the category
			dbResult = db.query("SELECT * FROM panorama INNER JOIN "+ getInput.category +" ON panorama.id="+ getInput.category +".id;")
			jsonArray = []
			for result in dbResult:
				jsonArray.append({'identifier': result.gmaps_id,
					'heading': result.heading,
					'lat': result.lat,
					'lng': result.lng,
					'title': result.title,
					'provider': result.provider})
			jsonResult = {'result':jsonArray}
			web.header('Content-Type', 'application/json')
			return json.dumps(jsonResult)

		else:
			#Add pano to the category
			dbResult = db.query("SELECT COUNT(*) AS total FROM information_schema.tables WHERE table_name='"+ getInput.category +"'")
			if dbResult[0].total == 0:
				#Add category
				db.query("CREATE TABLE " + getInput.category + " ( id INT NOT NULL, FOREIGN KEY (id) REFERENCES panorama(id) );")
			dbResult = db.query("SELECT id FROM panorama WHERE gmaps_id='"+ getInput.id +"';")
			if dbResult:
				db.insert(getInput.category, id=dbResult[0].id)

if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()