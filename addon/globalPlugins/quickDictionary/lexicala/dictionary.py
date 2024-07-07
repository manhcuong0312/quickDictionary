# dictionary.py
# Service summary, configuration scheme and objects for executing translation requests
# and processing the received responses
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2023 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

from typing import Any, Callable, List, Dict, Union
import addonHandler
import config
from logHandler import log
from .. import addonName
from ..service import Translator, Parser, secrets
from ..shared import htmlTemplate
from .languages import langs
from .api import Lapi, serviceName

try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to init translations. This may be because the addon is running from NVDA scratchpad.")
_: Callable[[str], str]


# Translators: The name of the online dictionary service
serviceSummary = _("Lexicala Dictionaries")

confspec: Dict[str, str] = {
	"source": "string(default=%s)" % langs.defaultSource,
	"from": "string(default=%s)" % langs.defaultFrom.code,
	"into": "string(default=%s)" % langs.defaultInto.code,
	"autoswap": "boolean(default=false)",
	"copytoclip": "boolean(default=false)",
	"username": 'string(default=%s)' % secrets[serviceName]._username,
	"password": "string(default=%s)" % secrets[serviceName]._password,
	"morph": "boolean(default=false)",  # Strip words to their stem
	"analyzed": "boolean(default=false)",  # Searching both headwords and inflections
	"all": "boolean(default=false)",  # Show all available translations
	"switchsynth": "boolean(default=false)"
}


class ServiceTranslator(Translator):
	"""Provides interaction with the online dictionary service."""

	def __init__(self, langFrom: str, langTo: str, text: str, *args, **kwargs) -> None:
		"""Initialization of the source and target language, as well as word or phrase to search in the dictionary.
		@param langFrom: source language
		@type langFrom: str
		@param langTo: target language
		@type langTo: str
		@param text: a word or phrase to look up in a dictionary
		@type text: str
		"""
		super(ServiceTranslator, self).__init__(langFrom, langTo, text, *args, **kwargs)

	@property
	def source(self) -> str:
		"""Short name of the source language.
		@return: source language code
		@rtype: str
		"""
		return config.conf[addonName][serviceName]['source']

	@property
	def morph(self) -> bool:
		"""Search in both headwords and inflections.
		@return: parameter of searching in the remote dictionary
		@rtype: bool
		"""
		return config.conf[addonName][serviceName]['morph']

	@property
	def analyzed(self) -> bool:
		"""Strip words to their stem.
		@return: parameter of searching in the remote dictionary
		@rtype: bool
		"""
		return config.conf[addonName][serviceName]['analyzed']

	def run(self) -> None:
		"""Query the remote dictionary and save the processed response.
		Should run in a separate thread to avoid blocking.
		"""
		self._resp = Lapi(
			text=self.text,
			lang=self.langFrom,
			source=self.source,
			morph=self.morph,
			analyzed=self.analyzed
		).search()
		if self._resp.get('error'):
			self._error = True
		parser = ServiceParser(response=self._resp, target=self.langTo)
		html: str = parser.to_html()
		self._html = htmlTemplate.format(body=html) if html else html
		self._plaintext = parser.to_text()


class ServiceParser(Parser):
	"""Parse the deserialized response from the server and returns it in HTML and text formats."""

	def __init__(self, response: Dict, target: str) -> None:
		"""Input data for further analysis and conversion to other formats.
		@param response: deserialized response from the online dictionary
		@type response: Dict
		@param target: target language to search in the list of translations
		@type target: str
		"""
		super(ServiceParser, self).__init__(response)
		self._langFrom: str = ''
		self._langInto: str = target

	def results(self) -> str:
		"""Analysis of the list of results.
		@return: all available results in HTML format
		@rtype: str
		"""
		if not self.resp.get('results') or len(self.resp['results']) == 0:
			return self.error(self.resp)
		results: List[str] = []
		for result in self.resp['results']:
			self._langFrom = self.language(result)
			transResp: Dict = Lapi().entries(self.id(result))
			results.append(self.headwords(transResp))
			results.append(self.senses(transResp))
		return self.filledOnly(results)

	def headwords(self, resp: Dict) -> str:
		"""Analysis of the "headword" object.
		Doc: "headword": object or list of objects
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		rsp: Union[List[Dict], Dict] = resp.get('headword', {})
		if isinstance(rsp, list):
			hws: List[str] = [self.headword(r) for r in rsp]
			return self.filledOnly(hws)
		return self.headword(rsp)

	def headword(self, resp: Dict) -> str:
		"""Analysis of the "headword" list item.
		Doc: "headword": object (within the headwords array)
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		if not resp or len(resp) == 0:
			return ''
		hw: str = "<h1>%s</h1>" % (self.text(resp) + self.inParentheses(
			self.pos(resp),
			self.gender(resp),
			self.number(resp)))
		hwl: List[str] = [hw]
		hwl.extend(self.filter(resp))
		return self.filledOnly(hwl)

	def senseIDs(self, resp: Dict) -> List[str]:
		"""Return a list of identifiers associated with the key "senses".
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: all found in current response branch dictionary article identifiers
		@rtype: List[str]
		"""
		rsp: Union[List[Dict], Dict] = resp.get('senses', {})
		ids: List[str] = []
		if isinstance(rsp, list):
			ids = [r['id'] for r in rsp if r.get('id')]
		return ids

	def senses(self, resp: Dict) -> str:
		"""Analysis of the "senses" object.
		Doc: "senses": array of objects
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		rsp: Union[List[Dict], Dict] = resp.get('senses', {})
		sns: str = ''
		if isinstance(rsp, list):
			sns = self.filledOnly(
				[self.withPrefix("<li>{value}</li>", '', self.sense(r)) for r in rsp])
		else:
			sns = self.withPrefix("<li>{value}</li>", '', self.sense(rsp))
		return self.withPrefix('<ul type="disc">\n{value}\n</ul>', '', sns)

	def sense(self, resp: Dict) -> str:
		"""Analysis of the "sense" object.
		Doc: "sense": object (within the senses array)
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		if not resp or not isinstance(resp, dict):
			return ''
		sns: List[str] = []
		# self.id(resp)  # currently not used
		sns.append(self.definition(resp) + self.translations(resp))
		sns.extend(self.filter(resp))
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<i>{name}</i>: {value}", _("mean"), self.filledOnly(sns))

	def compositional_phrases(self, resp: Dict) -> str:
		"""Analysis of the "compositional_phrases" object.
		Doc: "compositional_phrases": array of objects
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		rsp: Union[List[Dict], Dict] = resp.get('compositional_phrases', {})
		cp: str = ''
		if isinstance(rsp, list):
			cp = self.filledOnly(
				[self.withPrefix("<span>{value}</span>", '', self.compositional_phrase(r)) for r in rsp]
			)
		else:
			cp = self.withPrefix("<span>{value}</span>", '', self.compositional_phrase(rsp))
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("compositional phrases"), cp)

	def compositional_phrase(self, resp: Dict) -> str:
		"""Analysis of the "compositional_phrase" object.
		Doc: "compositional_phrase": object (within the compositional_phrases array)
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		if not resp or not isinstance(resp, dict):
			return ''
		cp: str = self.text(resp) + self.inParentheses(self.pos(resp))
		cp += self.withPrefix(" - {value}", '', self.definition(resp))
		cpl: List[str] = [cp]
		cpl.extend(self.filter(resp))
		return self.filledOnly(cpl)

	def examples(self, resp: Dict) -> str:
		"""Analysis of the "examples" array.
		Doc: "examples": array of objects
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		rsp: Union[List[Dict], Dict] = resp.get('examples', {})
		exs: str = ''
		if isinstance(rsp, list):
			exs = self.filledOnly(
				[self.withPrefix("<span>{value}</span>", '', self.example(r)) for r in rsp])
		else:
			exs = self.withPrefix("<span>{value}</span>", '', self.example(rsp))
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("examples"), exs)

	def example(self, resp: Dict) -> str:
		"""Analysis of the "example" object.
		Doc: "example": object (within the examples array)
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		if not resp or not isinstance(resp, dict):
			return ''
		example: List[str] = [
			self.text(resp),
			self.alternative_scripts(resp)
		]
		return self.filledOnly(example)

	def inflections(self, resp: Dict) -> str:
		"""Analysis of the "inflections" object.
		Doc: "inflections": array of objects
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		rsp: Union[List[Dict], Dict] = resp.get('inflections', {})
		ifs: str = ''
		if isinstance(rsp, list):
			ifs = self.filledOnly(
				[self.withPrefix("<span>{value}</span>", '', self.inflection(r)) for r in rsp]
			)
		else:
			ifs = self.withPrefix("<span>{value}</span>", '', self.inflection(rsp))
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("inflections"), ifs)

	def inflection(self, resp: Dict) -> str:
		"""Analysis of the "inflection" object.
		Doc: "inflection": object (within the inflections array)
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		if not resp or not isinstance(resp, dict):
			return ''
		inf: List[str] = [
			resp.get('text', '') + self.inParentheses(
				self.pos(resp),
				self.gender(resp),
				self.number(resp))]
		inf.extend(self.filter(resp))
		return self.filledOnly(inf)

	def pronunciation(self, resp: Dict) -> str:
		"""Analysis of the "pronunciation" object.
		Doc: "pronunciation": object
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		if not resp or not isinstance(resp, dict):
			return ''
		rsp: Dict = resp.get('pronunciation', {})
		pron: List[str] = [
			rsp.get('value', ''),
			self.geographical_usage(rsp)
		]
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i> {value}</p>", _("pronunciation"), self.filledOnly(pron, sep=', '))

	def translations(self, resp: Dict) -> str:
		"""Analysis of the "translations" object.
		Doc: "translations": object or array of objects
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		rsp: Dict = resp.get('translations', {})
		if not rsp:
			return ''
		if config.conf[addonName][serviceName]['all']:
			trs: List[str] = []
			trsl: str = ''
			for lng, cnt in rsp.items():
				lng = langs[lng].name
				if isinstance(cnt, list):
					tr: str = self.filledOnly(
						[self.withPrefix("{value}", '', self.translation(r)) for r in cnt],
						sep=', ')
				else:
					tr = self.withPrefix("{value}", '', self.translation(cnt))
				trs.append(self.withPrefix("{name} - <b>{value}</b>", lng, tr))
			trsl = ';<br>\n'.join(sorted(trs, key=lambda k: k.lower()))
			return self.withPrefix("\n<p>{value}.</p>", '', trsl)
		if not rsp.get(self._langInto) or len(rsp.get(self._langInto, {})) == 0:
			return ''
		rs: Dict = rsp.get(self._langInto, {})
		trsl = ''
		if isinstance(rsp, list):
			trsl = self.filledOnly(
				[self.withPrefix("{value}", '', self.translation(r)) for r in rs],
				sep=', ')
		else:
			trsl = self.withPrefix("{value}", '', self.translation(rs))
		return self.withPrefix(" - {value}", '', trsl)

	def translation(self, resp: Dict) -> str:
		"""Analysis of the "translations" list item object.
		Doc: "translation": object (within the translations array)
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		trs: List[str] = []
		trs.append(resp.get('text', '') + self.inParentheses(
			self.pos(resp),
			self.gender(resp),
			self.number(resp))
		)
		trs.extend(self.filter(resp))
		return self.filledOnly(trs)

	def inParentheses(self, *args: str) -> str:
		"""List of values displayed in parentheses next to the word.
		@param args: strings to display
		@type args: sequence of str
		@return: if the input parameters are not empty - they are returned in parentheses
		@rtype: str
		"""
		fields: List[str] = []
		for arg in args:
			if arg and arg.strip() != '':
				fields.append(str(arg))
		return self.withPrefix(" <i>({value})</i>", '', self.filledOnly(fields, sep=', '))

	def strList(self, resp: Union[Any, List[str]]) -> str:
		"""Convert an input str or list of strs to a single line.
		An argument can be either a string or a list of simple types.
		@param resp: incoming string or list of strings
		@type resp: Union[Any, List[str]]
		@return: line in which all input data are combined
		@rtype: str
		"""
		if isinstance(resp, list):
			return self.filledOnly(resp)
		elif resp and resp != '':
			return str(resp)
		return ''

	def filledOnly(self, lines: List[str], sep: str = '\n') -> str:
		"""Combine only non-empty strings from the entered list,
		by default a newline character '\n' is inserted between all lines.
		@param lines: a list of strings that may be empty
		@type lines: List[str]
		@param sep: separator, which will be inserted when merging strings
		@type sep: str
		@return: a line consisting only of non-empty strings in the list
		@rtype: str
		"""
		return sep.join(filter(lambda line: line and line != '', lines))

	def withPrefix(self, template: str, name: str, value: str) -> str:
		"""Display the field value after the specified prefix.
		Return an empty string if the last argument contains an empty value.
		The template must contain a {value} field and an optional {name} field.
		@param template: template string
		@type template: str
		@param name: title to be inserted in place of {name}
		@type: str
		@param value: string to be inserted in place of {value}
		@type value: str
		@return: combined in a str fields name and value according to the specified template
		@rtype: str
		"""
		if value and value != '':
			if '{name}' not in template:
				template += '{name}'
				name = ''
			return template.format(name=name.capitalize(), value=value)
		return ''

	def text(self, resp: Dict) -> str:
		"""Get the value of the "text" field.
		Doc: "text": string or list of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.strList(resp.get('text', ''))

	def id(self, resp: Dict) -> str:
		"""Get the value of the "id" field.
		Doc: "id": string
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return resp.get('id', '')

	def language(self, resp: Dict) -> str:
		"""Get the value of the "language" field.
		Doc: "language": string
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return resp.get('language', '')

	def pos(self, resp: Dict) -> str:
		"""Analysis of the "Part Of Speech" object.
		Doc: "pos": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.strList(resp.get('pos'))

	def gender(self, resp: Dict) -> str:
		"""Analysis of the "gender" object.
		Doc: "gender": string
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.strList(resp.get('gender'))

	def number(self, resp: Dict) -> str:
		"""Get the value of the "number" field.
		Doc: "number": string
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.strList(resp.get('number'))

	def definition(self, resp: Dict) -> str:
		"""Get the value of the "definition" field.
		Doc: "definition": string
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return resp.get('definition', '')

	def subcategorization(self, resp: Dict) -> str:
		"""Get the value of the "subcategorization" field.
		Doc: "subcategorization": string or Array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.withPrefix(
			"<p><i>{name}</i>: {value}</p>",
			# Translators: Field name in a dictionary entry
			_("subcategorization"),
			self.strList(resp.get('subcategorization')))

	def case(self, resp: Dict) -> str:
		"""Get the value of the "case" field.
		Doc: "case": string or Array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("case"), self.strList(resp.get('case')))

	def register(self, resp: Dict) -> str:
		"""Get the value of the "register" field.
		Doc: "register": string or Array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("register"), self.strList(resp.get('register')))

	def geographical_usage(self, resp: Dict) -> str:
		"""Get the value of the "geographical_usage" field.
		Doc: "geographical_usage": string or Array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.withPrefix(
			"<p><i>{name}</i>: {value}</p>",
			# Translators: Field name in a dictionary entry
			_("geographical usage"),
			self.strList(resp.get('geographical_usage')))

	def mood(self, resp: Dict) -> str:
		"""Get the value of the "mood" field.
		Doc: "mood": string or Array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("mood"), self.strList(resp.get('mood')))

	def tense(self, resp: Dict) -> str:
		"""Get the value of the "tense" field.
		Doc: "tense": string or Array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("tense"), self.strList(resp.get('tense')))

	def homograph_number(self, resp: Dict) -> str:
		"""Get the value of the "homograph_number" field.
		Doc: "homograph_number": number
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.withPrefix(
			"<p><i>{name}</i>: {value}</p>",
			# Translators: Field name in a dictionary entry
			_("homograph number"),
			self.strList(resp.get('homograph_number')))

	def alternative_scripts(self, resp: Dict) -> str:
		"""Get the value of the "alternative_scripts" object.
		Doc: "alternative_scripts": object
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		if isinstance(resp.get('alternative_scripts'), dict):
			return '\n'.join(
				(self.withPrefix(
					"{name}: {value}",
					key,
					val
				) for key, val in resp.get('alternative_scripts', {}) if key != '' and val != '')
			)
		return ''

	def semantic_category(self, resp: Dict) -> str:
		"""Analysis of the "semantic_category" object.
		Doc: "semantic_category": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.withPrefix(
			"<p><i>{name}</i>: {value}</p>",
			# Translators: Field name in a dictionary entry
			_("semantic category"),
			self.strList(resp.get('semantic_category')))

	def semantic_subcategory(self, resp: Dict) -> str:
		"""Analysis of the "semantic_subcategory" object.
		Doc: "semantic_subcategory": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.withPrefix(
			"<p><i>{name}</i>: {value}</p>",
			# Translators: Field name in a dictionary entry
			_("semantic subcategory"),
			self.strList(resp.get('semantic_subcategory')))

	def range_of_application(self, resp: Dict) -> str:
		"""Analysis of the "range_of_application" object.
		Doc: "range_of_application": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.withPrefix(
			"<p><i>{name}</i>: {value}</p>",
			# Translators: Field name in a dictionary entry
			_("range of application"),
			self.strList(resp.get('range_of_application')))

	def sentiment(self, resp: Dict) -> str:
		"""Analysis of the "sentiment" object.
		Doc: "sentiment": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("sentiment"), self.strList(resp.get('sentiment')))

	def see(self, resp: Dict) -> str:
		"""Analysis of the "see" object.
		Doc: "see": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("see"), self.strList(resp.get('see')))

	def see_also(self, resp: Dict) -> str:
		"""Analysis of the "see_also" object.
		Doc: "see_also": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("see also"), self.strList(resp.get('see_also')))

	def synonyms(self, resp: Dict) -> str:
		"""Analysis of the "synonyms" object.
		Doc: "synonyms": array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("synonyms"), self.strList(resp.get('synonyms')))

	def antonyms(self, resp: Dict) -> str:
		"""Analysis of the "antonyms" object.
		Doc: "antonyms": array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("antonyms"), self.strList(resp.get('antonyms')))

	def collocate(self, resp: Dict) -> str:
		"""Analysis of the "collocate" object.
		Doc: "collocate": array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("collocate"), self.strList(resp.get('collocate')))

	def aspect(self, resp: Dict) -> str:
		"""Get the value of the "aspect" field.
		Doc: "aspect": string
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("aspect"), self.strList(resp.get('aspect')))

	def source(self, resp: Dict) -> str:
		"""Get the value of the "source" field.
		Doc: "source": string
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.withPrefix(
			"<p><i>{name}</i>: <b>{value}</b></p>",
			# Translators: Field name in a dictionary entry
			_("&Dictionary:").replace('&', '').replace(':', ''),
			resp.get('source', ''))

	def error(self, resp: Dict) -> str:
		"""Convert errors received when connecting to the dictionary service into a text string.
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.withPrefix("<h1>{name}: {value}</h1>", "error", resp.get('error', ''))

	def filter(self, resp: Dict) -> List[str]:
		"""Passe the branch of the deserialized response  through a set of analyzers.
		@param resp: branch of the deserialized response from the server
		@type resp: Dict
		@return: found data in HTML format
		@rtype: List[str]
		"""
		return [
			# self.pronunciation(resp),  # currently not used
			self.subcategorization(resp),
			self.case(resp),
			self.mood(resp),
			self.register(resp),
			self.geographical_usage(resp),
			self.tense(resp),
			self.homograph_number(resp),
			self.inflections(resp),
			# self.alternative_scripts(resp),  # currently not used
			self.collocate(resp),
			self.semantic_category(resp),
			self.semantic_subcategory(resp),
			self.range_of_application(resp),
			self.sentiment(resp),
			self.synonyms(resp),
			self.antonyms(resp),
			self.aspect(resp),
			self.senses(resp),
			self.compositional_phrases(resp),
			self.examples(resp),
			self.see(resp),
			self.see_also(resp),
		]

	def to_html(self) -> str:
		"""Return the HTML representation of the deserialized response sent to the class from the server.
		@return: found data in HTML format
		@rtype: str
		"""
		if not self.html:
			self.html = self.results().replace('\u02c8', '')
		return self.html
