# https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
from flask import Flask, request, render_template
from spacy import displacy
import spacy
import sqlite3

CREATE_TABLE = "CREATE TABLE entities (entity TEXT PRIMARY KEY, counts INT)"
SELECT_WHERE = "SELECT * FROM entities WHERE entity=?"
SELECT = "SELECT * FROM entities;"
INSERT = "INSERT INTO entities VALUES (?, ?)"

class DatabaseConnection(object):

    def __init__(self, filename):
        self.connection = sqlite3.connect(filename, check_same_thread=False)

    def create_schema(self):
        try:
            self.connection.execute(CREATE_TABLE)
        except sqlite3.OperationalError:
            print("Warning: 'entities' table was already created, ignoring...")

    def get(self, entity=None):
        cursor = (self.connection.execute(SELECT_WHERE, (entity,))
                  if entity is not None else self.connection.execute(SELECT))
        return cursor.fetchall()

    def add(self, entity, count):
        try:
            self.connection.execute(f"INSERT INTO entities (entity, counts) VALUES (\"{entity}\", {count}) ON CONFLICT(entity) DO UPDATE SET counts = counts + {count} where entity=\"{entity}\"")
            self.connection.commit()
        except sqlite3.IntegrityError:
            print("Warning: '%s' is already in the database, ignoring..." % entity)
            self.connection.rollback()

nlp = spacy.load("en_core_web_sm")
def ner(text):
    doc = nlp(text)
    return displacy.render(doc, style='ent'), doc.ents


app = Flask(__name__)
connection = DatabaseConnection('entities.sqlite')
connection.create_schema()


@app.route('/')
def index():
    return """
            <html>
               <body>
                  <form action = "http://localhost:5000/api" method = "post">
                     <p>Enter Text:</p>
                     <p><input type = "text" name = "text" /></p>
                     <p><input type = "submit" value = "submit" /></p>
                  </form>
                  <a href="/db">Entity Database</a>
               </body>
            </html>
            """


@app.route('/api', methods = ['GET', 'POST'])
def api():

    if request.method == 'GET':
        return """{
            "description": "Interface to the spaCy entity extractor",
            "usage": "curl -X POST  -F 'file=@input.txt' http://127.0.0.1:5000/api}\n"""

    if request.method == 'POST':
        if 'file' in request.files:
            f = request.files['file']
            if f.filename:
                text = f.read().decode('UTF-8')
                html, ents = ner(text.strip())

                for ent in ents:
                    connection.add(ent.text,1)
                return html
            return "File has no filename"
        elif 'text' in request.form.to_dict().keys():
            html, ents = ner(request.form.to_dict()['text'])
            for ent in ents:
                connection.add(ent.text,1)
            return f"{html}<a href=\"/\">Main Page</a>"
        else:
            return "Upload a file through the api or submit a text entry on the main page.\ncURL usage: curl -X POST -F 'file=@test.txt' http://127.0.0.1:5000/api"

@app.route('/db', methods = ['GET'])
def all():
    ents = connection.get()
    return render_template('entities.html', entities=ents)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
