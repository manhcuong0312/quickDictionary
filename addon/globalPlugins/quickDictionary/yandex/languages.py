#languages.py
# Description of the class for working with the languages of a specific service
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2021 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

from typing import List, Generator
import os
from .. import _addonName
from ..service import Language, Languages, secrets
from .api import serviceName, Yapi


class ServiceLanguages(Languages):
	"""Represents a list of languages available in the dictionary service."""

	def __init__(self, file: str = "%s.json" % os.path.splitext(os.path.abspath(__file__))[0]) -> None:
		"""Initialization of an object representing a collection of available language pairs.
		Inherited methods from the parent class: load, save, __getitem__ and locale property
		Must be implemented: fromList, intoList, update, isAvailable and properties defaultFrom, defaultInto, all
		@param file: external file containing a list of available source and target languages
		@type file: str
		"""
		super(ServiceLanguages, self).__init__(file)
		self.updated = False
		self._all: List[Language] = []

	def update(self) -> bool:
		"""Get a list of available language pairs from a remote server and save them in an external file.
		This method should save the result of the operation in the logical field <self.updated>.
		@return: the success status of the operation
		@rtype: bool
		"""
		self.updated = False
		langs = Yapi().languages()
		if len(langs)>10:
			self.updated = self.save(langs)
		return self.updated

	def fromList(self) -> Generator[Language, None, None]:
		"""Sequence of available source languages.
		@return: sequence of available source languages
		@rtype: Generator[Language, None, None]
		"""
		for lang in list({c.split('-')[0]: c for c in self._langs}):
			yield Language(lang)

	def intoList(self, lang: str) -> Generator[Language, None, None]:
		"""Sequence of available target languages for a given source language.
		@param lang: source language code
		@type lang: str
		@return: sequence of available target languages
		@rtype: Generator[Language, None, None]
		"""
		if not lang: return
		for lng in self._langs:
			l = lng.split('-')
			if l[0]==lang:
				yield Language(l[1])

	def isAvailable(self, source: str, target: str) -> bool:
		"""Indicates whether the selected language pair is in the list of available languages.
		@param source: source language code
		@type source: str
		@param target: target language code
		@type target: str
		@return: whether a language pair is present in the list of available
		@rtype: bool
		"""
		return "%s-%s" % (source, target) in self._langs

	@property
	def defaultFrom(self) -> Language:
		"""Default source language.
		@return: English if available, else - the first language in list of source languages
		@rtype: Language
		"""
		return Language('en' if next(filter(lambda l: l.code=='en', self.fromList()), None) else self._langs[0].split('-')[0])

	@property
	def defaultInto(self) -> Language:
		"""Default target language.
		@return: locale language, if it is available as the target for the default source, otherwise the first one in the list
		@rtype: Language
		"""
		return self.locale if next(filter(lambda l: l.code==self.locale.code, self.intoList(self.defaultFrom.code)), None) else [l for l in self.intoList(self.defaultFrom.code)][0]

	@property
	def all(self) -> List[Language]:
		"""Full list of all supported source and target languages.
		@return: list of all supported languages
		@rtype: List[Language]
		"""
		if not self._all:
			self._all = [lang for lang in self.fromList()]
			for source in self.fromList():
				for target in self.intoList(source.code):
					if target.code not in [lng.code for lng in self._all]:
						self._all.append(target)
		return self._all


# An instance of the Languages object for use in the add-on
langs = ServiceLanguages()
