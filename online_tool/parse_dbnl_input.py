#!/usr/bin/env python3

"""Web-tool DBNL2DraCor parse_dbnl_input.py

Willem Jan Faber.

Copyright 2024, KB/National Library of the Netherlands.
"""

def escape(str_xml: str):
    str_xml = str_xml.replace("&", "&amp;")
    str_xml = str_xml.replace("<", "&lt;")
    str_xml = str_xml.replace(">", "&gt;")
    str_xml = str_xml.replace('"', "&quot;")
    str_xml = str_xml.replace("'", "&apos;")
    return str_xml


def unescape(str_xml: str):
    str_xml = str_xml.replace("&amp;", "&")
    str_xml = str_xml.replace("&lt;", "<")
    str_xml = str_xml.replace("&gt;", ">")
    str_xml = str_xml.replace("&quot;", '"')
    str_xml = str_xml.replace("&apos;", "'")
    return str_xml


def speaker_filter(speakerlist: set, newspeaker: str) -> set | tuple:
    newspeaker = escape(newspeaker)
    if newspeaker in speakerlist:
        for speaker in speakerlist:
            if newspeaker == speaker:
                return speakerlist
    speakerlist.add(newspeaker)
    return speakerlist


def parse_fulltext(data):
    rec = False
    srec = False

    speakerlist = set()

    chapters = []
    acts = []
    plays = []

    read_order = []

    alias = {}
    ctype = ""
    nexupspeaker = False
    srec1 = False

    for item in data.iter():
        if item.attrib.get("rend", "") == "speaker" and item.text:
            target = item.text.strip()
            if target.endswith("."):
                target = target[:-1]
            if not escape(target) in speakerlist:
                speakerinfo = speaker_filter(speakerlist, target)
                if type(speakerinfo) == tuple:
                    alias[speakerinfo[0]] = speakerinfo[1]
                else:
                    speakerlist = speakerinfo
        if item.attrib.get("rend", "") == "speaker":
            srec = True

        if item.tag == "speaker":
            srec1 = True

        if srec1 and item.tag == "hi":
            srec1 = False
            target = item.text.strip()
            if target.endswith("."):
                target = target[:-1]
            if not escape(target) in speakerlist:
                speakerinfo = speaker_filter(speakerlist, target)
                if type(speakerinfo) == tuple:
                    alias[speakerinfo[0]] = speakerinfo[1]
                else:
                    speakerlist = speakerinfo

        if srec and item.text:
            srec = False
            if not escape(item.text.strip()) in speakerlist:
                target = item.text.strip()
                if target.endswith("."):
                    target = target[:-1]
                speakerinfo = speaker_filter(speakerlist, target)
                if type(speakerinfo) == tuple:
                    alias[speakerinfo[0]] = speakerinfo[1]
                else:
                    speakerlist = speakerinfo

        if item.tag == "div":
            if item.attrib.get("type") == "act":
                rec = True
                if acts:
                    read_order.append({"act": acts})
                acts = [""]
                ctype = "act"
            if item.attrib.get("type") == "chapter":
                rec = True
                if chapters:
                    read_order.append({"chapter": chapters})
                chapters = [""]
                ctype = "chapter"
            if item.attrib.get("type") == "play":
                rec = True
                if plays:
                    read_order.append({"play": plays})
                ctype = "play"
                plays = [""]

        if rec:
            if (
                item.text
                and item.attrib.get("rend", "") == "speaker"
                and item.text.strip()
            ):
                speak_xml = "\n<speaker>" + escape(item.text) + "</speaker>\n"
                if ctype == "chapter":
                    chapters[-1] += speak_xml
                if ctype == "act":
                    acts[-1] += speak_xml
                if ctype == "play":
                    plays[-1] += speak_xml
            elif item.attrib.get("rend", "") == "speaker":
                nexupspeaker = True
            elif nexupspeaker and item.text:
                speak_xml = "\n<speaker>" + escape(item.text) + "</speaker>\n"
                nexupspeaker = False

            else:
                if item.text:
                    if ctype == "chapter":
                        chapters[-1] += escape(item.text)
                    if ctype == "act":
                        acts[-1] += escape(item.text)
                    if ctype == "play":
                        plays[-1] += escape(item.text)

    return read_order, speakerlist, alias
