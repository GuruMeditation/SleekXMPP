from sleekxmpp.plugins import xep_0082
from xml.etree import cElementTree as ET
from . import base

class xep_0145(base.base_plugin):
	"""
	XEP-0145 Annotations
	"""
	def plugin_init(self):
		self.description = "Annotations"
		self.xep = "0145"
		self.ns = 'storage:rosternotes'
	
	def post_init(self):
		pass
	

	def makeNote(self, jid, cdate, mdate, text):
		xmlnote = ET.Element('note')
		xmlnote.attrib['jid'] = jid
		xmlnote.text = text
		xmlnote.attrib['mdate'] = mdate
		xmlnote.attrib['cdate'] = cdate
		return xmlnote

	def storeAnnotation(self, jid, text):
		xmlstorage = ET.Element("{%s}storage" % self.ns)
		notes = self.retrieveAnnotations()
		holdcdate = False
		for note in notes:
			if jid in note['jid']:
				holdcdate = note['cdate']
			else:
				xmlnote = self.makeNote(note['jid'], note['cdate'], note['mdate'], note['text'])
				xmlstorage.append(xmlnote)

		if holdcdate is not False:
			cdate = holdcdate
		else:
			cdate = xep_0082.date()

		mdate = xep_0082.date()
		xmlnote = self.makeNote(jid, cdate, mdate, text)
		xmlstorage.append(xmlnote)
		self.xmpp['xep_0049'].storePrivate(xmlstorage)

	def retrieveAnnotations(self):
		node = ET.Element("{%s}storage" % self.ns)
		xmlstorage = self.xmpp['xep_0049'].retrievePrivate(node)
		notes = []
		for xmlnote in xmlstorage.getchildren():
			xmlnote.attrib['text'] = xmlnote.text
			notes.append(xmlnote.attrib)
		return notes
