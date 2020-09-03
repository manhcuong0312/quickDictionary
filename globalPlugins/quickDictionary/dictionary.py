#dictionary.py
import addonHandler
addonHandler.initTranslation()

import os
import re
import ssl
import threading
from urllib.request import Request, urlopen
from json import dumps, loads
import config

ssl._create_default_https_context = ssl._create_unverified_context


class Translator(threading.Thread):

    def __init__(self, langFrom, langTo, text, uiLang=None, token=None, mirror=False, isHtml=False, *args, **kwargs):
        super(Translator, self).__init__(*args, **kwargs)
        self._stopEvent = threading.Event()
        self._langFrom = langFrom
        self._langTo = langTo
        self._text = text
        self._uiLang = uiLang
        self._token = token
        self._mirror = mirror
        self._isHtml = isHtml
        self._translation = ''

    langFrom = lambda self: self._langFrom
    langTo = lambda self: self._langTo
    text = lambda self: self._text
    uiLang = lambda self: self._uiLang
    token = lambda self: self._token
    mirror = lambda self: self._mirror
    isHtml = lambda self: self._isHtml
    translation = lambda self: self._translation

    langFrom = property(langFrom)
    langTo = property(langTo)
    text = property(text)
    uiLang = property(uiLang)
    token = property(token)
    mirror = property(mirror)
    isHtml = property(isHtml)
    translation = property(translation)

    def stop(self):
        self._stopEvent.set()

    def run(self):
        headers = {
            'User-Agent': 'Mozilla 5.0'}
        directUrl = 'https://dictionary.yandex.net'
        mirrorUrl = 'https://info.alwaysdata.net'
        servers = [mirrorUrl]
        if not self.mirror:
            servers.insert(0, directUrl)
        lang = '%s-%s' % (self.langFrom, self.langTo)
        urlTemplate = "{server}/api/v1/dicservice.json/lookup?{key}lang={lang}&text={text}{ui}"
        for server in servers:
            url = urlTemplate.format(server=server, lang=lang,
                text=self.text.encode('utf-8'),#***
                key = 'key=%s&' % self.token if self.token else '',
                ui = '&ui=%s' % self.uiLang if self.uiLang else '')
            rq = Request(url, method='GET', headers=headers)
            try:
                resp = urlopen(rq, timeout=8)
            except Exception as e:
                self._translation = 'Error: %s [%s]' % (str(e), server)
                continue
            if resp.status!=200:
                self._translation = 'Error: incorrect response code %d from the server %s' % (resp.status, server)
                continue
            text = loads(resp.read().decode())
            parser = Parser(text)
            self._translation = parser.to_html() if self.isHtml else parser.to_text()
            return


class Parser(object):

    def __init__(self, resp):
        self.resp = resp
        self.html = ''

    def attrs(self, resp):
        attrs = []
        for key in ["pos", "asp", "num", "gen"]:
            if key in resp:
                field = {
                    'num': _('<i>number</i>: '),
                    'gen': _('<i>gender</i>: ')
                    }.get(key, '') + resp[key]
                attrs.append(field)
        if attrs:
            return " (%s)" % ', '.join(attrs)
        return ''

    def to_html(self):
        if not isinstance(self.resp, dict):
            return '<h1>%s</h1>' % _('Parsing error!')
        code = list(self.resp)[0]
        if str(code).isdigit():
            return '<h1>%s: %d</h1>' % (self.resp[code], code)
        html = '<link rel="stylesheet" type="text/css" href="%s">\n' % os.path.join(os.path.dirname(__file__), 'style.css')
        for key in ['def', 'tr', 'mean', 'syn', 'ex']:
            if key in self.resp:
                html += {
                    'mean': _('<p><i>Mean</i>: '),
                    'syn': _('<p><i>Synonyms</i>:\n'),
                    'ex': _('<p><i>Examples</i>:\n')
                    }.get(key, '')
                if key == 'def':
                    if not self.resp['def']:
                        html += '<h1>%s</h1>' % _('No results')
                    for elem in self.resp['def']:
                        html += '<h1>' + elem['text'] + self.attrs(elem) + '</h1>\n'
                        html += Parser(elem).to_html()
                        html += '\n'
                if key == 'tr':
                    html += '<ul>\n'
                    for elem in self.resp['tr']:
                        html += '<li><b>' + elem['text'] + '</b>' + self.attrs(elem) + '\n'
                        html += Parser(elem).to_html()
                        html += '</li>\n';
                    html += '</ul>\n'
                if key == 'mean':
                    means = []
                    for elem in self.resp['mean']:
                        means.append(elem['text'] + self.attrs(elem) )
                    html += ', '.join(means) + '</p>\n'
                    del(means)
                    html += Parser(elem).to_html()
                if key == 'syn':
                    syns = []
                    for elem in self.resp['syn']:
                        syns.append(elem['text'] + self.attrs(elem))
                    html += ', '.join(syns) + '</p>\n'
                    del(syns)
                    html += Parser(elem).to_html()
                if key == 'ex':
                    exs = []
                    for elem in self.resp['ex']:
                        tmp = elem['text'] + self.attrs(elem)
                        if 'tr' in elem:
                            trs = []
                            for extr in elem['tr']:
                                trs.append(extr['text'] + self.attrs(extr))
                            tmp += ' - ' + ', '.join(trs)
                            del(trs)
                        exs.append(tmp)
                    html += ',\n'.join(exs) + '</p>'
                    del(exs)
        self.html = html
        return html

    def to_text(self):
        li = u"\u2022 "
        h1 = "- "
        text = self.html if self.html else self.to_html().replace('<li>', li).replace('<h1>', h1)
        text = re.sub(r'\<[^>]*\>', '', text)
        text = '\r\n'.join((s for s in text.split('\n') if s))
        return text if text else str(resp)
