#shared.py
# Some functions for different purposes at the add-on level
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

import addonHandler
from logHandler import log
try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to initialise translations. This may be because the addon is running from NVDA scratchpad.")

import os
import re
import api
import ui
import braille
from speech import speak
from speech.commands import LangChangeCommand, CallbackCommand
from textInfos import POSITION_SELECTION
from time import sleep
from tones import beep
from functools import lru_cache, wraps
from threading import Thread
import config
from . import _addonName
from .locator import services
from .synthesizers import profiles


@lru_cache(maxsize=64)
def translateWithCaching(langFrom: str, langInto: str, text: str, service_id:int, credentials:int, others:int):
	"""Call the request procedure to the remote server on a separate thread.
	Wait for the request to complete and return a prepared response.
	All function values are cached to reduce the number of requests to the server.
	@param langFrom: source language
	@type langFrom: str
	@param langInto: target language
	@type langInto: str
	@param text: word or phrase to translate
	@type text: str
	* the following parameters are not used in the function, but are required for to properly caching
	@param service_id: the ID of the service used for translation
	@type service_id: int
	@param credentials: hash of credentials used to access the online service
	@type credentials: int, hash(username + password)
		@param others: hash of other parameters to be considered when caching
		@type others: int
	@return: object containing the prepared response from the remote dictionary
	@rtype: <service>.dictionary.Translator
	"""
	translator = services[config.conf[_addonName]['active']].translator(langFrom, langInto, text)
	translator.start()
	i=0
	while translator.is_alive():
		sleep(0.1)
		if i == 10:
			beep(500, 100)
			i = 0
		i+=1
	translator.join()
	return translator

def waitingFor(target, args:list=[]):
	"""Waiting for the function to complete, beeps are output while waiting.
	@param target: function that will be started and user will hear sounds during its execution
	@type target: function
	@param args: list of arguments to be passed to the function
	@type args: list
	"""
	load = Thread(target=target, args=args)
	load.start()
	i=0
	while load.is_alive():
		sleep(0.1)
		if i == 10:
			beep(500, 100)
			i = 0
		i+=1
	load.join()

def copyToClipboard(text: str) -> None:
	"""Copy the received text to the clipboard and announce the completion status of the operation.
	@param text: text to be copied to the clipboard
	@type text: str
	"""
	if api.copyToClip(text):
		# Translators: Message if the text was successfully copied to the clipboard
		ui.message(_("Copied to clipboard."))
	else:
		# Translators: Message if the text could not be copied to the clipboard
		ui.message(_("Copy failed."))

def getSelectedText() -> str:
	"""Retrieve the selected text.
	If the selected text is missing - extract the text from the clipboard.
	If the clipboard is empty or contains no text data - announce a warning.
	@return: selected text, text from the clipboard, or an empty string
	@rtype: str
	"""
	obj = api.getFocusObject()
	treeInterceptor = obj.treeInterceptor
	if hasattr(treeInterceptor, 'TextInfo') and not treeInterceptor.passThrough:
		obj = treeInterceptor
	try:
		info = obj.makeTextInfo(POSITION_SELECTION)
	except (RuntimeError, NotImplementedError):
		info = None
	if not info or info.isCollapsed or not clearText(info.text):
		try:
			text = api.getClipData()
		except Exception:
			text = ''
		if not text or not isinstance(text, str) or not clearText(text):
			# Translators: user has pressed the shortcut key for translating selected text, but no text was actually selected and clipboard is clear
			ui.message(_("There is no selected text, the clipboard is also empty, or its content is not text!"))
			return ''
		return clearText(text)
	return clearText(info.text)

def clearText(text: str) -> str:
	"""Retrieve only text information from a string, containing only letters and whitespace.
	@param text: incoming text string to be cleared of unnecessary characters
	@type text: str
	@return: text string stripped of unnecessary characters
	@rtype: str
	"""
	text = ''.join([s for s in text.strip() if s.isalpha() or s.isspace()])
	return ' '.join(re.split('\s+', text))

# Below toggle code came from Tyler Spivey's code, with enhancements by Joseph Lee (from Instant Translate add-on)
def finally_(func, final):
	"""Calls final after func, even if it fails."""
	def wrap(f):
		@wraps(f)
		def new(*args, **kwargs):
			try:
				func(*args, **kwargs)
			finally:
				final()
		return new
	return wrap(final)

# Template for displaying HTML content.
htmlTemplate = ''.join(["&nbsp;",
	"<!DOCTYPE html>",
	"<html>",
	"<head>",
	'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">',
	"<title></title>"
	'<link rel="stylesheet" type="text/css" href="%s">' % os.path.join(os.path.dirname(__file__), 'style.css'),
	"</head>",
	"<body>{body}</body>",
	"</html>"
])

def messageWithLangDetection(msg: dict):
	"""Pronounce text in a given language if enabled the setting for auto-switching languages of the synthesizer.
	After the speech, switche to the previous synthesizer, if the corresponding option is enabled.
	@param msg: language code and text to be spoken in the specified language
	@type msg: dict -> {'lang': str, 'text': str}
	"""
	speechSequence=[]
	if config.conf['speech']['autoLanguageSwitching']:
		speechSequence.append(LangChangeCommand(msg['lang']))
	speechSequence.append(msg['text'])
	if config.conf[_addonName][services[config.conf[_addonName]['active']].name]['switchsynth']:
		previous = profiles.getCurrent()
		speechSequence.append(CallbackCommand(callback=profiles.restorePrevious))
		speechSequence.append(CallbackCommand(callback=lambda prev=previous: profiles.rememberCurrent(prev)))
	speak(speechSequence)
	braille.handler.message(msg['text'])
