#! /usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, GLib

from widgets import ScreenshotOverlay, Window, Menu, Action, PopupWindow, FileChooserSavePNGDialog
from os.path import expanduser
from pathlib import Path
from imgur import ImgurConnection
from imagehost import ImageHost, MockImageHost
from time import time

class PopupWindowHandler:
	def __init__(self, popupw):
		self.popupw = popupw

	def onUploadSuccess(self, host_url=None, direct_url=None, delete_job=None):
		GLib.idle_add(self.popupw.showUrls, host_url, direct_url, delete_job)
	def onUploadFailure(self):
		GLib.idle_add(self.popupw.showError, 'Error while uploading image')

	def onLoginSuccess(self):
		pass
	def onLoginFailure(self):
		self.onUploadFailure()

	def onDeleteStart(self):
		GLib.idle_add(self.popupw.showIdleWait, 'Deleting...')
	def onDeleteSuccess(self):
		GLib.idle_add(self.popupw.showOk, 'Delete Success!')
	def onDeleteFailure(self):
		GLib.idle_add(self.popupw.showError, 'Error while deleting image')


if __name__ == "__main__":
	w = Window()
	overlay = ScreenshotOverlay(Gdk.pixbuf_get_from_window(
		Gdk.get_default_root_window(), 0, 0,
		Gdk.Screen.get_default().get_width(),
		Gdk.Screen.get_default().get_height()
	))
	menu = Menu()
	windowclose = w.connect('delete-event', Gtk.main_quit)
	menuclose = menu.connect('selection-done', lambda *_: w.close())

	def preventQuit():
		w.disconnect(windowclose)
		menu.disconnect(menuclose)

	def saveAs(*_):
		preventQuit()
		def save(fcd, response):
			if response == Gtk.ResponseType.ACCEPT:
				fn = fcd.get_filename()
				if not fn.endswith('png'):
					fn = '%s.png' % fn
				if fn:
					pb = overlay.getSelection()
					pb.savev(fn, 'png', [], [])
			w.close()
			Gtk.main_quit()
		fcd = FileChooserSavePNGDialog('Save as...',w)
		fcd.connect('response', save)
		fcd.show_all()

	def sendToHost(HostCtor):
		preventQuit()
		pw = PopupWindow()
		pw.set_title('Pyshot')

		w.destroy()
		pw.connect('delete-event', Gtk.main_quit)
		pb = overlay.getSelection()
		b, imgdata = pb.save_to_bufferv('png', [], [])
		pw.show_all()

		handler = PopupWindowHandler(pw)
		host = HostCtor(handler)
		host.connect()
		host.uploadImage('screenshot.png', imgdata, 'image/png')

	def sendToImgur(*_):
		sendToHost(ImgurConnection)
	def sendToMockImageHost(*_):
		sendToHost(MockImageHost)

	def saveToPictures(*_):
		preventQuit()
		w.destroy()
		Gtk.main_quit()
		pb = overlay.getSelection()
		pb.savev(expanduser('~/Pictures/screenshot_%d.png' % time()), 'png', [], [])

	for action, callback in (
			(Action('Save as...', 'folder'), saveAs),
			(Action('Quicksave in Pictures', 'folder-pictures'), saveToPictures),
			(Action('Upload to Imgur'), sendToImgur),
			#(Action('Upload to MockImageHost'), sendToMockImageHost)
		):
		action.connect('activate', callback)
		menu.add(action)


	w.setOverlay(overlay)
	w.context_menu = menu
	w.show_all()
	Gtk.main()
