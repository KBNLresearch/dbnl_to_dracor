#!/usr/bin/env python3

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
import pprint

default_params = {'pb' : False,
                  'hi' : False,
                  'rend' : False,
                  'xptr' : False,   
                  'note': False}

default_url = 'https://www.dbnl.org/nieuws/xml.php?id=vond001gysb01'

def parse_xml(url=default_url, params=default_params):
    req = requests.get(url)
    parser = etree.XMLParser(remove_blank_text=True)
    data = req.content

    #print(data.decode('utf-8'))
    formatted_xml = ''

    xml_data = etree.fromstring(data,
                                parser=parser)

    data = data.decode('utf-8')
    ndata = ''

    for l in data.split('\r'):
        if not l.lstrip().startswith('<'):
            ndata += ' ' + l.strip()
        else:
            if ndata.endswith('>'):
                ndata += '\n' + l.strip()
            else:
                ndata += l.strip()

    xml = etree.fromstring(ndata.encode())
    formatted_xml = etree.tostring(xml,
                                   pretty_print = True,
                                   encoding = 'utf-8').decode()
    if params.get('pb'):
        '''
        <pb> elementen inclusief attributen ('<pb.*?>')'''
        pass

    if params.get('hi'):
        '''
        <hi> elementen inclusief attributen, exclusief inhoud ('<hi.*?>' + '<hi.*?\n.*?>' + '</hi>')'''
        pass

    if params.get('rend'):
        '''
        "rend" attributen inclusief waardes (' rend=".*?"')'''
        pass

    if params.get('xptr'):
        ''' 
        <xptr> elementen inclusief attributen ('<xptr.*?>')'''
        pass


    return formatted_xml

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')

    if request.method == 'POST':
        todo = request.form.get('url')
        operation = request.form.getlist('op')

        opdict = default_params.copy()
        for op in operation:
            opdict[op] = True

        url = urlparse(todo)

        if url.hostname is None:
            return render_template('index.html')
        if not '=' in url.query:
            return render_template('index.html')

        try:
            xml_id = escape(url.query.split('=')[-1])
        except:
            return render_template('index.html')

        to_parse = f'https://www.dbnl.org/nieuws/xml.php?id={xml_id}'
        xml_data = parse_xml(to_parse, opdict)
        print(opdict)

        return render_template('index.html', xml_data = xml_data)

if __name__ == '__main__':
    p = default_params
    p['pb'] = True
    print(parse_xml())
    app.run()
