import procgame.dmd
import pinproc
import pyglet
import pyglet.image
import pyglet.window
from pyglet import gl

print "Pyglet!"

DMD_SIZE = (128, 32)
DMD_SCALE = 8

# Bitmap data for luminance-alpha mask image.
# See image_to_string below for code to generate this:
MASK_DATA = """\x00\xf2\x00\xd8\x00\xa5\x00\x8b\x00\x8c\x00\xa6\x00\xd8\x00\xf2\x00\xd9\x00\x8c\x00\x73\x00\x58\x00\x59\x00\x73\x00\x8c\x00\xd9\x00\xa5\x00\x73\x00\x25\x00\x0c\x00\x0c\x00\x25\x00\x73\x00\xa5\x00\x8c\x00\x58\x00\x0c\xff\x00\xff\x00\x00\x0c\x00\x59\x00\x8c\x00\x8c\x00\x59\x00\x0c\xff\x00\xff\x00\x00\x0c\x00\x58\x00\x8c\x00\xa5\x00\x73\x00\x25\x00\x0c\x00\x0c\x00\x26\x00\x72\x00\xa6\x00\xd9\x00\x8c\x00\x72\x00\x59\x00\x59\x00\x72\x00\x8c\x00\xd9\x00\xf3\x00\xd9\x00\xa5\x00\x8c\x00\x8c\x00\xa6\x00\xd9\x00\xf3"""


class Desktop(object):
	"""The :class:`Desktop` class helps manage interaction with the desktop, providing both a windowed
	representation of the DMD, as well as translating keyboard input into pyprocgame events."""
	
	exit_event_type = 99
	"""Event type sent when Ctrl-C is received."""
	
	key_map = {}
	
	window = None
	mask = pyglet.image.ImageData(8, 8, 'LA', MASK_DATA, pitch=16)
	mask_texture = pyglet.image.TileableTexture.create_for_image(mask)
	
	def __init__(self):
		self.ctrl = 0
		self.i = 0
		self.key_events = []
		self.setup_window()
		self.add_key_map(pyglet.window.key.LSHIFT, 3)
		self.add_key_map(pyglet.window.key.RSHIFT, 1)
	
	def add_key_map(self, key, switch_number):
		"""Maps the given *key* to *switch_number*, where *key* is one of the key constants in :mod:`pygame.locals`."""
		self.key_map[key] = switch_number

	def clear_key_map(self):
		"""Empties the key map."""
		self.key_map = {}

	def get_keyboard_events(self):
		"""Asks :mod:`pygame` for recent keyboard events and translates them into an array
		of events similar to what would be returned by :meth:`pinproc.PinPROC.get_events`."""
		if self.window.has_exit:
			self.append_exit_event()
		e = self.key_events
		self.key_events = []
		return e
	
	def append_exit_event(self):
		self.key_events.append({'type':self.exit_event_type, 'value':'quit'})

	def setup_window(self):
		self.window = pyglet.window.Window(width=DMD_SIZE[0]*DMD_SCALE, height=DMD_SIZE[1]*DMD_SCALE)
		
		@self.window.event
		def on_close():
			self.append_exit_event()
		
		@self.window.event
		def on_key_press(symbol, modifiers):
			if (symbol == pyglet.window.key.C and modifiers & pyglet.window.key.MOD_CTRL) or (symbol == pyglet.window.key.ESCAPE):
				self.append_exit_event()
			elif symbol in self.key_map:
				self.key_events.append({'type':pinproc.EventTypeSwitchClosedDebounced, 'value':self.key_map[symbol]})
		
		@self.window.event
		def on_key_release(symbol, modifiers):
			if symbol in self.key_map:
				self.key_events.append({'type':pinproc.EventTypeSwitchOpenDebounced, 'value':self.key_map[symbol]})

	def draw(self, frame):
		"""Draw the given :class:`~procgame.dmd.Frame` in the window."""
		self.window.dispatch_events()
		self.window.clear()
		gl.glEnable(gl.GL_BLEND)
		gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
		gl.glLoadIdentity()

		gl.glColor3f(1.0, 0.5, 0.25)

		gl.glScalef(1, -1, 1)
		gl.glTranslatef(0, -DMD_SIZE[1]*DMD_SCALE, 0)

		data = frame.get_data_mult()
		image = pyglet.image.ImageData(DMD_SIZE[0], DMD_SIZE[1], 'L', data, pitch=DMD_SIZE[0])

		gl.glTexParameteri(image.get_texture().target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
		image.blit(0, 0, width=DMD_SIZE[0]*DMD_SCALE, height=DMD_SIZE[1]*DMD_SCALE)

		del image

		gl.glColor4f(1.0, 1.0, 1.0, 1.0)
		self.mask_texture.blit_tiled(x=0, y=0, z=0, width=DMD_SIZE[0]*DMD_SCALE, height=DMD_SIZE[1]*DMD_SCALE)
		self.window.flip()
	
	def __str__(self):
		return '<Desktop pyglet>'


def image_to_string(filename):
	"""Generate a string representation of the image at the given path, for embedding in code."""
	image = pyglet.image.load(filename)
	data = image.get_data('LA', 16)
	s = ''
	for x in data:
		s += "\\x%02x" % (ord(x))
	return s
