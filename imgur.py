
from imagehost import ImageHost
from requests import Session
import threading

apikey = '2cb56e4f1b7f361'
class ImgurConnection(ImageHost):
	def __init__(self, handler):
		self.handler = handler
		self.session = Session()

	def connect(self):
		pass

	def uploadImage(self, imgname, imgbuffer, imgmime):
		def doRequest():
			try:
				r = self.session.post('https://api.imgur.com/3/image', timeout=20,
					headers={'Authorization': 'Client-ID %s' % apikey},
					data={'title': 'Pyshot screenshot', 'name': imgname},
					files={'image': (imgname, imgbuffer, imgmime)}
				)
				if r.status_code != 200:
					raise Exception(r.json())
				json = r.json()
				link = json['data']['link']
				deleteHash = json['data']['deletehash']
				def deleteJob():
					def doDeleteRequest():
						try:
							r = self.session.delete('https://api.imgur.com/3/image/%s' % deleteHash,
								timeout=20,
								headers={'Authorization': 'Client-ID %s' % apikey},
							)
							if r.status_code != 200:
								raise Exception(r.json())
								self.handler.onDeleteFailure()
							self.handler.onDeleteSuccess()
						except Exception as e:
							print(e)
					self.handler.onDeleteStart()
					thread = threading.Thread(target=doDeleteRequest)
					thread.daemon = True
					thread.start()
				self.handler.onUploadSuccess(host_url=link, delete_job=deleteJob)
			except Exception as e:
				print ('Upload error response:')
				print(e)
				self.handler.onUploadFailure()
		thread = threading.Thread(target=doRequest)
		thread.daemon = True
		thread.start()
