from urllib.parse import urlparse

from flask import Flask, render_template, request
from markupsafe import escape

app = Flask(__name__)

#https://www.dbnl.org/nieuws/xml.php?id=vond001gysb01

#https://www.dbnl.org/nieuws/xml.php?id=vond001gysb01


def parse_xml(url):
    request.get(url)
    return ''

@app.route("/", methods=['GET', 'POST'])
def hello_world():
    if request.method == 'GET':
        return render_template('index.html')
    if request.method == 'POST':
        todo = request.form.get('url')
        url = urlparse(todo)
        if url.hostname is None:
            return render_template('index.html')
        if not '=' in url.query:
            return render_template('index.html')
        xml_id = escape(url.query.split('=')[-1])
        to_parse = f'https://www.dbnl.org/nieuws/xml.php?id={xml_id}'

        return render_template('index.html')

