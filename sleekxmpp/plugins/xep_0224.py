from xml.etree import cElementTree as ET
from . import base

class xep_0224(base.base_plugin):
	"""
	XEP-0224 Attention
	"""
	def plugin_init(self):
		self.description = "Attention"
		self.xep = "0224"
		self.ns = 'urn:xmpp:attention:0'
		self.xmpp.add_handler("<message xmlns='jabber:client'><attention xmlns='%s' /></message>" % self.ns, self.handler_attention)
	
	def post_init(self):
		self.xmpp['xep_0030'].add_feature(self.ns)

	def handler_attention(self, xml):
		print('/!\ Dring dring !!! /!\\')

	def makeAttention(self):
		xmlattention = ET.Element("{%s}attention" % self.ns)
		return xmlattention

	def sendAttention(self, to, body=None, msubject=None, mtype=None):
		xmlattention = self.makeAttention()
		xmlmessage = self.xmpp.makeMessage(to, body, msubject, mtype)
		xmlmessage.append(xmlattention)
		self.xmpp.send(xmlmessage)
