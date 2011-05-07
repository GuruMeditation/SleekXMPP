from xml.etree import cElementTree as ET
from . import base
import time

class xep_0202(base.base_plugin):
	"""
	XEP-0202 Entity Time
	"""
	def plugin_init(self):
		self.description = "Entity Time"
		self.xep = "0202"
		self.ns = 'urn:xmpp:time'
		self.xmpp.add_handler("<iq type='get' xmlns='jabber:client'><time xmlns='%s' /></iq>" % self.ns, self.report_time)
	
	def post_init(self):
		self.xmpp['xep_0030'].add_feature(self.ns)
	
	def gendate(self):
		tabdate = time.gmtime()
		today = str(tabdate[0]).zfill(4) + '-' + str(tabdate[1]).zfill(2)
		today += '-' + str(tabdate[2]).zfill(2)
		today += 'T' + str(tabdate[3]).zfill(2) + ':' + str(tabdate[4]).zfill(2) 
		today += ':'+str(tabdate[5]).zfill(2)+'Z'
		return today

	def gentzo(self):
		if time.localtime().tm_isdst>0:
			timezone = -time.altzone
		else:
			timezone = -time.timezone
		hours =  int(timezone/3600)
		minutes = timezone%3600
		if timezone<0:
			sign = '-'
		else:
			sign = '+'
		tzo = sign + str(hours).zfill(2) + ':' + str(minutes).zfill(2)
		return tzo

	def report_time(self, xml):
		iq = self.xmpp.makeIqResult(xml.get('id', 'unknown'))
		iq.attrib['to'] = xml.get('from', self.xmpp.server)
		qtime = ET.Element("{%s}time" % self.ns)
		tzo = ET.Element('tzo')
		tzo.text = self.gentzo()
		utc = ET.Element('utc')
		utc.text = self.gendate()
		qtime.append(tzo)
		qtime.append(utc)
		iq.append(qtime)
		self.xmpp.send(iq)
	
	def getTime(self, jid):
		iq = self.xmpp.makeIqGet()
		qtime = ET.Element("{%s}time" % self.ns)
		iq.append(qtime)
		iq.attrib['to'] = jid
		iq.attrib['from'] = self.xmpp.fulljid
		id = iq.get('id')
		result = self.xmpp.send(iq, "<iq id='%s'/>" % id)
		if result and result is not None and result.get('type', 'error') != 'error':
			qry = result.find('{urn:xmpp:time}time')
			entitytime = {}
			for child in qry.getchildren():
				entitytime[child.tag.split('}')[-1]] = child.text
			return entitytime
		else:
			return False

