from flask import Flask, render_template, request
from markupsafe import escape
from urllib.parse import urlparse
from lxml import etree
import requests

app = Flask(__name__)

#https://www.dbnl.org/nieuws/xml.php?id=vond001gysb01
#https://www.dbnl.org/nieuws/xml.php?id=vond001gysb01

'''
<pb> elementen inclusief attributen ('<pb.*?>')
<hi> elementen inclusief attributen, exclusief inhoud ('<hi.*?>' + '<hi.*?\n.*?>' + '</hi>')
"rend" attributen inclusief waardes (' rend=".*?"')
<xptr> elementen inclusief attributen ('<xptr.*?>')
<note> elementen inclusief attributen en inclusief inhoud ('<note.*?</note>' + '<note.*?\n.*?</note>' + '<note.*?\n.*?\n.*?</note>' + '<note.*?\n.*?\n.*?\n.*?</note>' (in die volgorde))
'''


default_params = {'pb' : False,
                  'hi' : False,
                  'rend' : False,
                  'xptr' : False,   
                  'note': False}

def parse_xml(url, params=default_params):
    req = requests.get(url)
    data = etree.fromstring(req.content)

    if params.get('pb'):
        '''
        <pb> elementen inclusief attributen ('<pb.*?>')'''

    if params.get('hi'):
        '''
        <hi> elementen inclusief attributen, exclusief inhoud ('<hi.*?>' + '<hi.*?\n.*?>' + '</hi>')'''

    if params.get('rend'):
        '''
        "rend" attributen inclusief waardes (' rend=".*?"')'''

    if params.get('xptr'):
        ''' 
        <xptr> elementen inclusief attributen ('<xptr.*?>')'''


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
        print(to_parse)
        parse_xml(to_parse)

        return render_template('index.html')
