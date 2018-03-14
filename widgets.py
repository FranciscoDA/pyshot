
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

class ScreenshotOverlay(Gtk.Image):
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

		self.context_menu = None
		self.connect('screen-changed', setVisual)
		self.connect('button-press-event', self.buttonPressed)
		self.connect('button-release-event', self.buttonReleased)
		self.connect('motion-notify-event', self.mouseMoved)

	def setOverlay(self, overlay):
		self.image = overlay
		self.add(overlay)

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
			self.context_menu.show_all()
			self.context_menu.popup(None, None, None, None, 0, Gdk.CURRENT_TIME)
			return True # stop repeated events

	def mouseMoved(self, _, ev):
		if self.hasSelectionRectangle():
			self.image.setRectangle(self.__dragstartx, self.__dragstarty, ev.x, ev.y)
	def hasSelectionRectangle(self):
		return self.__dragstartx and self.__dragstarty

class PopupWindow(Gtk.Window):
	def __init__(self):
		super().__init__(Gtk.WindowType.TOPLEVEL)
		self.set_size_request(180, 90)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.set_resizable(False)
		self.vbox = Gtk.VBox(False, 0)
		self.add(self.vbox)
		self.showIdleWait('Uploading...')

	def clearVBox(self):
		self.vbox.foreach(lambda w, *_: self.vbox.remove(w), None)

	def showIdleWait(self, msg):
		self.clearVBox()
		sp = Gtk.Spinner()
		sp.start()
		self.vbox.pack_start(sp, True, True, 0)
		self.vbox.pack_start(Gtk.Label(msg), True, False, 0)
		self.show_all()

	def showUrls(self, host_url=None, direct_url=None, delete_job=None):
		self.clearVBox()
		for (url,label) in zip((host_url, direct_url), ('Host URL:', 'Direct URL:')):
			if not url:
				continue
			self.vbox.pack_start(Gtk.Label(label), False, False, 0)
			entry = Gtk.Entry(text=url, editable=False)
			entry.connect('button-release-event', lambda w, ev: w.select_region(0, -1))
			self.vbox.pack_start(entry, True, False, 0)
		if delete_job is not None:
			deletebtn = Gtk.Button(label='Delete')
			deletebtn.connect('clicked', lambda *etc: delete_job())
			self.vbox.pack_start(deletebtn, False, False, 0)
		self.show_all()

	def setMessageWithIcon(self, message, icon_name=None):
		self.clearVBox()
		if icon_name is not None:
			img = Gtk.Image(icon_name='mail-signed-verified', pixel_size=32, icon_size=32)
			self.vbox.pack_start(img, True, False, 0)
		self.vbox.pack_start(Gtk.Label(message), True, False, 0)
	def showOk(self, message):
		self.setMessageWithIcon(message, 'mail-signed-verified')
		self.show_all()
	def showError(self, error):
		self.setMessageWithIcon(error, 'network-error')
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
