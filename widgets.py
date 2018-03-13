
import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import threading
from time import sleep

class Rectangle:
	def __init__(self, x1, y1, x2, y2):
		self.set(x1,y1,x2,y2)
	def set(self, x1, y1, x2, y2):
		self.x1, self.y1 = min(x1, x2), min(y1, y2)
		self.x2, self.y2 = max(x1, x2), max(y1, y2)
	def width(self): return self.x2 - self.x1
	def height(self): return self.y2 - self.y1
	def area(self): return self.width() * self.height()


def debugEvent(*etc):
	print (etc)

def setVisual (w, ev=None):
	w.set_visual(w.get_screen().get_rgba_visual())

class Image(Gtk.Image):
	def __init__(self,pb):
		super().__init__()
		self.set_from_pixbuf(pb)
		self.connect_after('draw', self.drawOverlay)
		self.connect('screen-changed', setVisual)
		self.set_app_paintable(True)
		self.rect = Rectangle(0, 0, 0, 0)
		self.th = None

	def redraw(self):
		sleep(1/60)
		GLib.idle_add(self.queue_draw)

	def drawOverlay(self, w, cairo_ctx):
		screenrect = Rectangle(*cairo_ctx.clip_extents())
		cairo_ctx.set_source_rgba(0, 0, 0, 0.8)
		cairo_ctx.set_operator(cairo.OPERATOR_OVER)
		cairo_ctx.rectangle(screenrect.x1, screenrect.y1, screenrect.width(), screenrect.height())
		cairo_ctx.fill()

		cairo_ctx.set_operator(cairo.OPERATOR_CLEAR)
		cairo_ctx.rectangle(self.rect.x1, self.rect.y1, self.rect.width(), self.rect.height())
		cairo_ctx.fill()
	def getSelection(self):
		return self.get_pixbuf().new_subpixbuf(
			self.rect.x1, self.rect.y1, self.rect.width(), self.rect.height()
		)

	def setRectangle(self, x1, y1, x2, y2):
		self.rect.set(x1, y1, x2, y2)
		if not self.th or not self.th.is_alive():
			self.th = threading.Thread(target=self.redraw)
			self.th.daemon = True
			self.th.start()

class Action(Gtk.MenuItem):
	def __init__(self, action_name, icon_name=None, icon_size=24):
		super().__init__()
		b = Gtk.Box()
		if icon_name:
			img = Gtk.Image(
				icon_name=icon_name,
				icon_size=icon_size,
				pixel_size=icon_size
			)
			b.pack_start(img, False, False, 0)
		b.pack_start(Gtk.Label(action_name), False, False, 0 if icon_name else icon_size)
		self.add(b)

class Menu(Gtk.Menu):
	def __init__(self):
		super().__init__()
		self.set_reserve_toggle_size(False)

class Window(Gtk.Window):
	def __init__(self):
		super().__init__(title='', decorated=False, resizable=False)

		self.__dragstartx, self.__dragstarty = None, None
		self.fullscreen()

		self.connect('screen-changed', setVisual)
		self.connect('button-press-event', self.buttonPressed)
		self.connect('button-release-event', self.buttonReleased)
		self.connect('motion-notify-event', self.mouseMoved)

	def set_image(self, im):
		self.image = im
		self.add(im)

	def set_menu(self, menu):
		self.menu = menu

	def show_all(self):
		setVisual(self)
		super().show_all()
		win = self.get_window()
		win.set_events(
			win.get_events() |
			Gdk.EventMask.POINTER_MOTION_MASK |
			Gdk.EventMask.BUTTON_PRESS_MASK |
			Gdk.EventMask.BUTTON_RELEASE_MASK
		)
		win.set_cursor(Gdk.Cursor.new_from_name(self.get_display(), 'crosshair'))

	def buttonPressed(self, _, ev):
		if ev.button == 1:
			self.image.setRectangle(ev.x, ev.y, ev.x, ev.y)
			self.__dragstartx, self.__dragstarty = ev.x, ev.y
			return True # stop repeated events
	def buttonReleased(self, _, ev):
		if ev.button == 1:
			self.image.setRectangle(self.__dragstartx, self.__dragstarty, ev.x, ev.y)
			self.__dragstartx, self.__dragstarty = None, None
			self.menu.show_all()
			self.menu.popup(None, None, None, None, 0, Gdk.CURRENT_TIME)
			return True # stop repeated events

	def mouseMoved(self, _, ev):
		if self.hasSelectionRectangle():
			self.image.setRectangle(self.__dragstartx, self.__dragstarty, ev.x, ev.y)
	def hasSelectionRectangle(self):
		return self.__dragstartx and self.__dragstarty

class PopupWindow(Gtk.Window):
	def __init__(self):
		super().__init__(Gtk.WindowType.TOPLEVEL)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.showIdleWait('Uploading...')

	def showIdleWait(self, msg):
		self.foreach(lambda w, *_: self.remove(w), None)
		box = Gtk.VBox()
		sp = Gtk.Spinner()
		sp.start()
		box.pack_start(sp, False, False, 0)
		l = Gtk.Label(msg)
		box.pack_start(l, False, False, 0)
		self.add(box)
		self.show_all()

	def showUrls(self, host_url=None, direct_url=None, delete_job=None):
		self.foreach(lambda w, *_: self.remove(w), None)
		box = Gtk.VBox()
		for (url,label) in zip((host_url, direct_url), ('Host URL:', 'Direct URL:')):
			if not url:
				continue
			box.pack_start(Gtk.Label(label), False, False, 0)
			entry = Gtk.Entry(text=url, editable=False)
			entry.connect('button-release-event', lambda w, ev: w.select_region(0, -1))
			box.pack_start(entry, False, False, 0)
		if delete_job is not None:
			deletebtn = Gtk.Button(label='Delete')
			deletebtn.connect('clicked', lambda *etc: delete_job())
			box.pack_start(deletebtn, False, False, 0)
		self.add(box)
		self.show_all()

	def showOk(self, msg):
		self.foreach(lambda w, *_: self.remove(w), None)
		box = Gtk.VBox()
		box.pack_start(Gtk.Image(icon_name='mail-signed-verified', pixel_size=32, icon_size=32), False, False, 0)
		box.pack_start(Gtk.Label(msg), False, False, 0)
		self.add(box)
		self.show_all()

	def showError(self, error):
		self.foreach(lambda w, *_: self.remove(w), None)
		box = Gtk.VBox()
		box.pack_start(Gtk.Image(icon_name='network-error',pixel_size=32,icon_size=32), False, False, 0)
		box.pack_start(Gtk.Label(error), False, False, 0)
		self.add(box)
		self.show_all()

	def show_all(self):
		super().show_all()
		win = self.get_window()
		win.set_events(
			win.get_events() |
			Gdk.EventMask.BUTTON_PRESS_MASK |
			Gdk.EventMask.BUTTON_RELEASE_MASK
		)

class FileChooserSavePNGDialog(Gtk.FileChooserDialog):
	def __init__(self, title, parent):
		super().__init__(
			title, parent,
			action=Gtk.FileChooserAction.SAVE,
			buttons = (
				'Cancel', Gtk.ResponseType.CANCEL,
				'Save', Gtk.ResponseType.ACCEPT
			)
		)
		filt = Gtk.FileFilter()
		filt.add_mime_type('image/png')
		filt.add_pattern('*.png')
		self.set_do_overwrite_confirmation(True)
		self.set_filter(filt)
