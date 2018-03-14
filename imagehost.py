
from time import sleep
import threading

class ImageHost:
	def connect(self):
		raise NotImplementedError()

	def uploadImage(self, imgname, imgbuffer, imgmime, success_cb=None):
		raise NotImplementedError()

class MockImageHost (ImageHost):
	def __init__(self, handler):
		self.handler = handler

	def connect(self):
		pass

	def uploadImage(self, imgname, imgbuffer, imgmime):
		def doRequest():
			sleep(3)
			def deleteJob():
				def doDeleteRequest():
					sleep(3)
					self.handler.onDeleteSuccess()
				self.handler.onDeleteStart()
				thread = threading.Thread(target=doDeleteRequest)
				thread.daemon = True
				thread.start()
			self.handler.onUploadSuccess(host_url='hello world', delete_job=deleteJob)
		thread = threading.Thread(target=doRequest)
		thread.daemon = True
		thread.start()
