#!/usr/bin/env python3

"""Web-tool DBNL2DraCor app.py

Willem Jan Faber

Copyright 2024, KB/National Library of the Netherlands
"""


from urllib.parse import urlparse

import requests
from flask import Flask, Response, render_template, request
from lxml import etree
from markupsafe import escape

app = Flask(__name__)

DEFAULT_URL = "https://www.dbnl.org/nieuws/xml.php?id=vos_002kluc01"

# Change this if you deploy elsewhere.
TOOL_URL = "http://127.0.0.1:5000"
# TOOL_URL = "https://www.kbresearch.nl/"

DEFAULT_PARAMS = {
    "remove_pb": False,
    "remove_hi": False,
    "remove_note": False,
    "remove_rend": False,
    "remove_xptr": False,
    "stats": 0,
    "mode": "remove",
    "url": DEFAULT_URL,
    "tool_url": TOOL_URL,
}


def fetch_xmldata(url) -> etree:
    try:
        req = requests.get(url)
        parser = etree.XMLParser(remove_blank_text=True)
        data = req.content
        xml = etree.fromstring(data, parser=parser)
    except Exception as err:
        raise err
    return xml



def parse_xml(xml, params):
    formatted_xml = etree.tostring(xml,
                                   pretty_print=True,
                                   encoding="utf-8").decode()
    start_len = len(formatted_xml)
    if params.get("remove_pb"):
        to_remove = set()
        for i in xml.iter():
            if str(i.tag).startswith("pb"):
                to_remove.add(str(i.tag))

        for elm in to_remove:
            etree.strip_tags(xml, elm)

    if params.get("remove_hi"):
        to_remove = set()
        for i in xml.iter():
            if str(i.tag).startswith("hi"):
                to_remove.add(str(i.tag))

        for elm in to_remove:
            etree.strip_tags(xml, elm)

    if params.get("remove_rend"):
        for elem in xml.iter():
            if "rend" in elem.attrib:
                del elem.attrib["rend"]

    if params.get("remove_xptr"):
        to_remove = set()
        for i in xml.iter():
            if str(i.tag).startswith("xptr"):
                to_remove.add(str(i.tag))

        for elm in to_remove:
            etree.strip_tags(xml, elm)

    if params.get("remove_note"):
        to_remove = set()

        for i in xml.iter():
            if str(i.tag).startswith("note"):
                to_remove.add(str(i.tag))

        for elm in to_remove:
            etree.strip_tags(xml, elm)

        for elem in xml.iter():
            if "note" in elem.attrib:
                del elem.attrib["note"]

    formatted_xml = etree.tostring(xml,
                                   pretty_print=True,
                                   encoding="utf-8").decode()

    end_len = len(formatted_xml)

    return formatted_xml, start_len - end_len


def extract_speakerlist(xml):
    operation_params = DEFAULT_PARAMS.copy()

    for key in operation_params:
        if isinstance(operation_params[key], bool):
            operation_params[key] = not operation_params[key]

    xml, stats = parse_xml(xml, operation_params)
    xml = etree.fromstring(xml)

    speakers = set()

    for item in xml.iter():
        if item.tag == 'speaker':
            if item.text and not item.text is None:
                speakers.add(item.text.strip())

    xml = '<xml>\n'
    for speaker in speakers:
        xml += f'\t<speaker>{speaker}</speaker>\n'
    xml += '</xml>\n'
    return xml


@app.route("/extract", methods=["POST"])
@app.route("/extract/", methods=["POST"])
@app.route("/", methods=["GET", "POST"])
def index():
    operation_params = DEFAULT_PARAMS.copy()
    if request.method == "GET":
        return render_template("index.html", opdict=operation_params)
    todo = request.form.get("url")
    operation = request.form.getlist("op")

    for op in operation:
        operation_params[op] = True

    url = urlparse(todo)

    if url.hostname is None:
        return render_template("index.html", opdict=operation_params)

    if "=" not in url.query:
        return render_template("index.html", opdict=operation_params)

    try:
        xml_id = escape(url.query.split("=")[-1])
    except Exception as err:
        operation_params['err'] = err
        return render_template("index.html", opdict=operation_params)

    dbnl_url = f"https://www.dbnl.org/nieuws/xml.php?id={xml_id}"
    operation_params["url"] = dbnl_url

    if "extract" not in request.path:
        try:
            xml_data, stats = parse_xml(fetch_xmldata(dbnl_url), operation_params)
            operation_params["stats"] = stats
            operation_params["mode"] = "remove"
        except Exception as err:
            operation_params['err'] = err
            return render_template("index.html",
                                   xml_data=xml_data,
                                   opdict=operation_params)


    else:
        try:
            xml_data = extract_speakerlist(fetch_xmldata(dbnl_url))
            operation_params["mode"] = "extract"
        except Exception as err:
            operation_params['err'] = err
            return render_template("index.html",
                                   xml_data=xml_data,
                                   opdict=operation_params)


    return render_template("index.html",
                           xml_data=xml_data,
                           opdict=operation_params)



@app.route("/batch", methods=["GET"])
@app.route("/batch/", methods=["GET"])
def batch_operation() -> Response:
    """
    For batch handling use this, default operation == remove.

    /batch/?id=groo001adam01 == /batch/?mode=remove&id=groo001adam01
    /batch/?mode=playerslist&id=groo001adam01

    We will handle one xml at the time, so the response is one xml.
    """

    operation_params = DEFAULT_PARAMS.copy()

    for key in operation_params:
        if isinstance(operation_params[key], bool):
            operation_params[key] = not operation_params[key]

    print(request.args)
    todo = request.args.get("id")
    if not todo:
        return "Missing 'todo' argument. Use /batch/?todo=heyn003vrie01", 400

    operation = request.args.get("mode") or "remove"
    to_parse = f"https://www.dbnl.org/nieuws/xml.php?id={todo}"

    if operation == "remove":
        try:
            xml_data, stats = parse_xml(fetch_xmldata(to_parse),
                                        operation_params)
            return Response(xml_data, mimetype="text/xml")
        except Exception:
            return "Fatal exception, parse_xml failed.", 500

    else:
        try:
            xml_data = extract_speakerlist(fetch_xmldata(to_parse))
            return Response(xml_data, mimetype="text/xml")
        except Exception:
            return "Fatal exception, extract_speakerlist failed.", 500

    return "You should not be here.", 500


if __name__ == "__main__":
    app.run(debug=False)
