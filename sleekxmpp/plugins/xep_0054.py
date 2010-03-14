from xml.etree import cElementTree as ET
from . import base

class xep_0054(base.base_plugin):
	"""
	XEP-0054 vcard-temp
	"""
	def plugin_init(self):
		self.description = "vcard-temp"
		self.xep = "0054"
		self.ns = 'vcard-temp'
	
	def post_init(self):
		pass

	def getvcard(self, jid=None):
		iq = self.xmpp.makeIqGet()
		if jid is not None:
			iq.attrib['to'] = jid
		vcard = ET.Element("{%s}vCard" % self.ns)
		iq.append(vcard)
		id = iq.get('id')
		result = send.xmpp.send(iq, "<iq id='%s'/>" % id)
		if result and result is not None and result.get('type', 'error') != 'error':
			xmlvcard = result.find("{%s}vCard" % self.ns)
			return xmlvcard
		return False

	def setvcard(self, vcard):
		iq = self.xmpp.makeIqSet()
		xmlvcard = ET.Element("{%s}vCard" % self.ns)
		for el in vcard.getchildren():
			xmlvcard.append(el)
		iq.append(xmlvcard)
		id = iq.get('id')
		result = self.xmpp.send(iq, "<iq id='%s'/>" % id)
		if result and result is not None and result.get('type', 'error') != 'error':
			return True
		return False



	def makevcard(self, **vcard):
		xmlvcard = ET.Element("{%s}vCard" % self.ns)
		for el in vcard:
			xmlel = ET.Element(el)
			xmlel.text = vcard[el]
			xmlvcard.append(xmlel)
		return xmlvcard
