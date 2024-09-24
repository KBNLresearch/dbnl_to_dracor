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
    xml = etree.fromstring(data, parser=parser)
    formatted_xml = etree.tostring(xml,
                                   pretty_print = True,
                                   encoding = 'utf-8').decode()
    stats = len(formatted_xml)
    if params.get('pb'):
        '''
        <pb> elementen inclusief attributen ('<pb.*?>')'''
        to_remove = set()
        for i in xml.iter():
            if str(i.tag).startswith('pb'):
                to_remove.add(str(i.tag))

        for elm in to_remove:
            etree.strip_tags(xml, elm)

    if params.get('hi'):
        '''
        <hi> elementen inclusief attributen, exclusief inhoud ('<hi.*?>' + '<hi.*?\n.*?>' + '</hi>')'''
        to_remove = set()
        for i in xml.iter():
            if str(i.tag).startswith('hi'):
                to_remove.add(str(i.tag))

        for elm in to_remove:
            etree.strip_tags(xml, elm)

    if params.get('rend'):
        '''
        "rend" attributen inclusief waardes (' rend=".*?"')'''
        for elem in xml.iter():
            if 'rend' in elem.attrib:
                del elem.attrib['rend']

    if params.get('xptr'):
        ''' 
        <xptr> elementen inclusief attributen ('<xptr.*?>')'''
        to_remove = set()
        for i in xml.iter():
            if str(i.tag).startswith('xptr'):
                to_remove.add(str(i.tag))

        for elm in to_remove:
            etree.strip_tags(xml, elm)


    if params.get('note'):
        to_remove = set()
        for i in xml.iter():
            if str(i.tag).startswith('note'):
                to_remove.add(str(i.tag))

        for elm in to_remove:
            etree.strip_tags(xml, elm)

        for elem in xml.iter():
            if 'note' in elem.attrib:
                del elem.attrib['note']


    formatted_xml = etree.tostring(xml,
                                   pretty_print = True,
                                   encoding = 'utf-8').decode()
    stats1 = len(formatted_xml)
    return formatted_xml, stats - stats1

@app.route("/", methods=['GET', 'POST'])
def index():
    opdict = default_params.copy()
    opdict['stats'] = 0
    if request.method == 'GET':
        return render_template('index.html', opdict=opdict)

    if request.method == 'POST':
        todo = request.form.get('url')
        operation = request.form.getlist('op')

        for op in operation:
            opdict[op] = True

        url = urlparse(todo)

        if url.hostname is None:
            return render_template('index.html', opdict=opdict)
        if not '=' in url.query:
            return render_template('index.html', opdict=opdict)

        try:
            xml_id = escape(url.query.split('=')[-1])
        except:
            return render_template('index.html', opdict=opdict)

        to_parse = f'https://www.dbnl.org/nieuws/xml.php?id={xml_id}'
        xml_data, stats = parse_xml(to_parse, opdict)
        opdict['stats'] = stats
        return render_template('index.html',
                               xml_data=xml_data,
                               opdict=opdict)

if __name__ == '__main__':
    app.run()
