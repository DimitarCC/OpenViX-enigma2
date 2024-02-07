from enigma import eServiceReference
from ServiceReference import ServiceReference
from urllib.request import urlopen
from time import time
from twisted.internet import threads
import twisted.python.runtime
import socket

idIPTV = 0x13E9

def getRealServiceRefForIPTV(ref, useStrRef = False):
	if useStrRef:
		if ref and ref.startswith("5097:"):
			if ref.find(".m3u8") > -1:
				service_ref_cleaned = "4097:" + ":".join(ref.split(":")[1:])
			else:
				service_ref_cleaned = "1:" + ":".join(ref.split(":")[1:])
		else:
			service_ref_cleaned = ref
		if service_ref_cleaned.find("17999/") > -1:
			service_ref_cleaned = service_ref_cleaned.split("17999/")[1].split(":")[0].replace("%3a", ":")
		return service_ref_cleaned
	elif ref and ref.type == idIPTV:
		if ref.toString().find(".m3u8") > -1:
			service_ref_cleaned = "4097:" + ":".join(ref.toString().split(":")[1:])
		else:
			service_ref_cleaned = "1:" + ":".join(ref.toString().split(":")[1:])
		if service_ref_cleaned.find("17999/") > -1:
			service_ref_cleaned = service_ref_cleaned.split("17999/")[1].split(":")[0].replace("%3a", ":")
		ref = eServiceReference(service_ref_cleaned)
	return ref

class IPTVProcessor():
	def __init__(self):
		self.last_exec = None
		self.playlist = None
		self.isPlayBackup = False
		self.iptv_service_provider = ""
		self.url = ""
		self.offset = 0
		self.refresh_interval = 1
		self.scheme = ""
		self.search_criteria = ",{SID}"
		

	def processService(self, nref, iptvinfodata, callback=None):
		splittedRef = nref.toString().split(":")
		sRef = nref and ServiceReference(getRealServiceRefForIPTV(nref))
		origRef = ":".join(splittedRef[:10])
		iptvInfoDataSplit = iptvinfodata[0].split("|<|")
		channelForSearch = iptvInfoDataSplit[0].split(":")[0]
		#catchUpDays = 0
		#if len(iptvInfoDataSplit) > 1:
		#	catchUpDays = int(iptvInfoDataSplit[1])
		#print "[IPTV] channelForSearch = " + channelForSearch
		#print "[IPTV] orig_name = " + orig_name
		orig_name = sRef and sRef.getServiceName()
		backup_ref = nref.toString()
		try:
			backup_ref = iptvinfodata[1].split(":")[0].replace("%3a", ":")
		except:
			pass
		if callback:
			threads.deferToThread(self.processDownloadPlaylist, nref, channelForSearch, origRef, backup_ref, orig_name).addCallback(callback)
		else:
			return self.processDownloadPlaylist(nref, channelForSearch, origRef, backup_ref, orig_name) , nref, False
		return nref, nref, True
		
	def processDownloadPlaylist(self, nref, channelForSearch, origRef, backup_ref, orig_name):
		try:
			socket.setdefaulttimeout(2)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
			channelSID = self.search_criteria.replace("{SID}", channelForSearch)
			prov = self
			cache_time = 0
			if prov.refresh_interval > -1:
				cache_time = int(prov.refresh_interval * 60 * 60)
			nref_new = nref.toString()
			cur_time = time()
			time_delta = prov.last_exec and cur_time - prov.last_exec or None
			if prov.refresh_interval > -1 and time_delta and  time_delta < cache_time:
				playlist = prov.playlist
			else:
				response = urlopen(prov.url)
				playlist = response.read().decode('utf-8')
				prov.playlist = playlist
				if cache_time > 0:
					prov.last_exec = cur_time

			playlist_splitted = playlist.split("\n")
			idx = 0
			for line in playlist_splitted:
				if line.find(channelSID) > -1:
					iptv_url = playlist_splitted[idx + prov.offset].replace(":", "%3a")
					nref_new = origRef + ":" + iptv_url + ":" + orig_name + "•" + prov.iptv_service_provider
					break
				idx += 1
			self.nnref = eServiceReference(nref_new)
			self.isPlayBackup = False
			return self.nnref
		except Exception as ex:
			print("EXCEPTION: " + str(ex))
			self.isPlayBackup = True
			self.nnref = eServiceReference(backup_ref + ":")
			return self.nnref