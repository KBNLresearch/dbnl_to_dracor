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

DEFAULT_URL = 'https://www.dbnl.org/nieuws/xml.php?id=vond001gysb01'

DEFAULT_PARAMS = {'remove_pb' : False,
                  'remove_hi' : False,
                  'remove_note': False,
                  'remove_rend' : False,
                  'remove_xptr' : False,
                  'stats': 0, 
                  'url' : DEFAULT_URL}

def extract_playlist(url=DEFAULT_URL):
    req = requests.get(url)
    parse = etree.XMLParser(remove_blank_text=True)
    data = req.content
    xml = etree.fromstring(data,parser=parse)

    for item in xml.iter():
        print(item.attrib, item.tag, item.text)


def parse_xml(url=DEFAULT_URL, params=DEFAULT_PARAMS):
    req = requests.get(url)
    parser = etree.XMLParser(remove_blank_text=True)
    data = req.content
    xml = etree.fromstring(data, parser=parser)
    formatted_xml = etree.tostring(xml,
                                   pretty_print = True,
                                   encoding = 'utf-8').decode()
    start_len = len(formatted_xml)
    if params.get('remove_pb'):
        '''
        <pb> elementen inclusief attributen ('<pb.*?>')'''
        to_remove = set()
        for i in xml.iter():
            if str(i.tag).startswith('pb'):
                to_remove.add(str(i.tag))

        for elm in to_remove:
            etree.strip_tags(xml, elm)

    if params.get('remove_hi'):
        '''
        <hi> elementen inclusief attributen,
        exclusief inhoud ('<hi.*?>' + '<hi.*?\n.*?>' + '</hi>')'''

        to_remove = set()
        for i in xml.iter():
            if str(i.tag).startswith('hi'):
                to_remove.add(str(i.tag))

        for elm in to_remove:
            etree.strip_tags(xml, elm)

    if params.get('remove_rend'):
        '''
        "rend" attributen inclusief waardes (' rend=".*?"')'''
        for elem in xml.iter():
            if 'rend' in elem.attrib:
                del elem.attrib['rend']

    if params.get('remove_xptr'):
        ''' 
        <xptr> elementen inclusief attributen ('<xptr.*?>')'''
        to_remove = set()
        for i in xml.iter():
            if str(i.tag).startswith('xptr'):
                to_remove.add(str(i.tag))

        for elm in to_remove:
            etree.strip_tags(xml, elm)


    if params.get('remove_note'):
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


@app.route("/", methods=['GET', 'POST'])
def index():
    operation_params = DEFAULT_PARAMS.copy()
    if request.method == 'GET':
        return render_template('index.html', opdict=operation_params)

    if request.method == 'POST':
        todo = request.form.get('url')
        operation = request.form.getlist('op')

        for op in operation:
            operation_params[op] = True

        url = urlparse(todo)

        if url.hostname is None:
            return render_template('index.html', opdict=operation_params)

        if not '=' in url.query:
            return render_template('index.html', opdict=operation_params)

        try:
            xml_id = escape(url.query.split('=')[-1])
        except:
            return render_template('index.html', opdict=operation_params)

        to_parse = f'https://www.dbnl.org/nieuws/xml.php?id={xml_id}'

        xml_data, stats = parse_xml(to_parse, operation_params)

        operation_params['stats'] = stats
        operation_params['url'] = to_parse

        return render_template('index.html',
                               xml_data=xml_data,
                               opdict=operation_params)

@app.route("/batch", methods=['GET'])
@app.route("/batch/", methods=['GET'])
def batch_operation() -> Response:
    ''' 
        For batch handling use this, default operation == remove.

        /batch/?todo=groo001adam01 == /batch/?operation=remove&todo=groo001adam01
        /batch/?operation=playerslist&todo=groo001adam01

        We will handle one xml at the time, so the response is one xml.
    '''

    operation_params = DEFAULT_PARAMS.copy()

    for key in operation_params:
        if isinstance(operation_params[key], bool):
            operation_params[key] = not operation_params[key]

    todo = request.args.get('todo')
    if not todo:
        return "Missing 'todo' argument. Use /batch/?todo=heyn003vrie01", 400

    operation = request.args.get('operation') or 'remove'
    if operation == 'remove': 
        to_parse = f'https://www.dbnl.org/nieuws/xml.php?id={todo}'
        xml_data, stats = parse_xml(to_parse, operation_params)
        return Response(xml_data, mimetype='text/xml')

    return "Unknown operation error.", 500


if __name__ == '__main__':
    app.run()
