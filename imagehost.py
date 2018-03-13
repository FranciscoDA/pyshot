
class ImageHost:
	def connect(self):
		raise NotImplementedError()

	def uploadImage(self, imgname, imgbuffer, imgmime, success_cb=None):
		raise NotImplementedError()

class MockImageHost (ImageHost):
	def __init__():
		super().__init__()

	def connect(self):
		pass

	def uploadImage(self, imgname, imgbuffer, imgmime, success_cb=None):
		success_cb([x % imgname for x in ['%s.png', '%s.png']])
