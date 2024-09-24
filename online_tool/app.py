#!/usr/bin/env python3

import requests
import pprint

from flask import (Flask,
                  jsonify,
                  render_template,
                  request,
                  Response)

from lxml import etree
from markupsafe import escape
from urllib.parse import urlparse

app = Flask(__name__)

default_url = 'https://www.dbnl.org/nieuws/xml.php?id=vond001gysb01'

default_params = {'pb' : False,
                  'hi' : False,
                  'rend' : False,
                  'xptr' : False, 
                  'note': False,
                  'url' : default_url}


def extract_playlist(url=default_url):
    req = requests.get(url)
    parse = etree.XMLParser(remove_blank_text=True)
    data = req.content
    xml = etree.fromstring(data,parser=parse)

    for item in xml.iter():
        print(item.attrib, item.tag, item.text)


def parse_xml(url=default_url, params=default_params):
    req = requests.get(url)
    parser = etree.XMLParser(remove_blank_text=True)
    data = req.content
    xml = etree.fromstring(data, parser=parser)
    formatted_xml = etree.tostring(xml,
                                   pretty_print = True,
                                   encoding = 'utf-8').decode()
    start_len = len(formatted_xml)
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
    end_len = len(formatted_xml)
    return formatted_xml, start_len - end_len


@app.route("/batch", methods=['GET'])
def batch():
    ''' 
        For batch handling use this, default operation == remove.

        /batch/?todo=groo001adam01 == /batch/?operation=remove&todo=groo001adam01
        /batch/?operation=playerslist&todo=groo001adam01

        We will handle one xml at the time, so the response is one xml.
    '''

    opdict = default_params
    for i in opdict:
        if type(opdict[i]) == bool:
            opdict[i] = not opdict[i]
    todo = request.args.get('todo') or ''
    operation = request.args.get('operation') or 'remove'

    if not todo:
        return 'Missing argument todo, /batch/?todo=heyn003vrie01'

    if operation == 'remove': 
        to_parse = f'https://www.dbnl.org/nieuws/xml.php?id={todo}'
        xml_data, stats = parse_xml(to_parse, opdict)
        return Response(xml_data, mimetype='text/xml')

    return 'You should not be seeing this..'


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
        opdict['url'] = to_parse
        return render_template('index.html',
                               xml_data=xml_data,
                               opdict=opdict)

if __name__ == '__main__':
    app.run()
