"""Bookshelf2Eagle2012.

This program converts EAGLE board (.brd) plus a bookshelf placement (.pl) to an EAGLE board with an updated placement.

This program was written by Devon Merrill (devon@ucsd.edu).

Usage:
  bookshelf2eagle.py -h | --help
  bookshelf2eagle.py --brd <BRD> --pl <PL> --out <OUT_NAME>

-h --help                      Show this message.
-i --brd BRD                   The EAGLE .brd file.
-p --pl PL                     The bookshelf placement file with the updated placements.
-o --out OUT_NAME              Name for updated EAGLE file that will be created.
"""

import datetime

import Swoop
from docopt import docopt

from eagle2bookshelf2012 import ElementEntry, de_bounding_box


class Component(object):
	"""Little holder for components info"""
	def __init__(self, x, y, rotdeg, locked):
		super(Component, self).__init__()
		self.x = x
		self.y = y
		self.rotdeg = rotdeg
		self.rot = "R" + str(rotdeg)
		if self.rotdeg == 0:
			self.rot = None
		self.locked = locked


def read_pl2(fname):
	"""
	This is a modification of Chester Holtz code
	Read & parse .pl (placement) file
	:param fname: .pl filename
	"""
	with open(fname,'r') as f:
		lines = f.read().splitlines()

	lines = lines[5:]
	bp = 0
	components = {}
	static_components = []
	for line in lines:
		if line.strip() == '':
			bp = 1
			continue
		else:
			if bp == 0:
				l = line.split()
				pname = l[0].strip()
				newx, newy = (float(l[1]),float(l[2]))
				r = l[4]
				locked = False
				if len(l) > 5:
					if '/FIXED' in l[5]:
						locked = True

				rot2deg = {'N':0,'S':180,'E':270,'W':90}
				components[pname] = Component(x=newx, y=newy, rotdeg=rot2deg[r], locked=locked)

	return components


def update_placements(
	brd_file,
	pl_file,
	out_file,
):

	brd = Swoop.EagleFile.from_file(brd_file)

	# Get the info from the pl file
	pl_info = read_pl2(pl_file)


	# set the rotations for all the components from the pl file
	for n in (Swoop.From(brd).
		get_elements()
	):
		if n.get_name() in pl_info:
			c = pl_info[n.get_name()]
			if c.rot is not None:
				n.set_rot(c.rot)

	# get the elements (components/blocks/nodes) and geometery from brd file
	elements = {}
	for n in (Swoop.From(brd).
		get_elements()
	):
		name = n.get_name()			
		library = n.get_library()
		package = n.get_package()
		e = ElementEntry(name, library=library, package=package)
		e.x_loc = n.get_x()
		e.y_loc = n.get_y()
		e.rotation = n.get_rot()
		e.locked = n.get_locked()
		elements[name] = e

	print 'total: ' + str(len(elements)) + ' elements (components/blocks/nodes)'

	# get the bounding box for the elements (from lib?)
	for n, e in elements.iteritems():
		eagle_package = Swoop.From(brd).get_library(e.library).get_package(e.package)
		pads = eagle_package.get_pads()
		smds = eagle_package.get_smds()

		for pin in pads+smds:
			e.add_pin(pin)

		drawing = eagle_package.get_drawing_elements()

		for de in drawing + pads + smds:
			allowed_types = [
				Swoop.Wire,
				Swoop.Rectangle,
				Swoop.Hole,
				Swoop.Circle,
				Swoop.Polygon,
				Swoop.Smd,
				Swoop.Pad,
			]
			allowed_layers = set(
				(None,1,16,17,18,29,30,31,32,33,34,35,36,151,39,40,41,42,44,45)
			)

			allowed = [isinstance(de, t) for t in allowed_types]
			if not any(allowed):
				continue

			((x_min, x_max), (y_min, y_max)) = de_bounding_box(de)
			
			e.expand_bb(
				x_min,
				x_max,
				y_min,
				y_max,
			)

			if e.name == 'K1':
				print de
				print (e.x_min, e.x_max), (e.y_min, e.y_max)

	components = read_pl2(pl_file)

	for n in (Swoop.From(brd).
		get_elements()
	):

		try:
			str(n.get_value())
		except UnicodeEncodeError as e:
			n.set_value(e.message)

		brd_name = n.get_name()

		if brd_name not in pl_info: # skip if not in pl file
			continue

		e = elements[brd_name]

		# ll_x = e.x_loc # default to origin
		# ll_y = e.y_loc # default to origin

		if (e.rotation is None) or (e.rotation == 'R0'): # N
			n.set_x( pl_info[brd_name].x - e.x_min )
			# ll_x = e.x_loc + (e.x_min)
			n.set_y( pl_info[brd_name].y - e.y_min )
			# ll_y = e.y_loc + (e.y_min)
			# print e.name, 'loc:', (e.x_loc, e.y_loc),'ll:', (ll_x, ll_y), 'x:', (e.x_min, e.x_max), 'y:', (e.y_min, e.y_max)
		elif e.rotation == 'R90':
			n.set_x( pl_info[brd_name].x + e.y_max )
			# ll_x = e.x_loc - (e.y_max)
			n.set_y( pl_info[brd_name].y - e.x_min )
			# ll_y = e.y_loc + (e.x_min)
			# print e.name, 'loc:', (e.x_loc, e.y_loc),'ll:', (ll_x, ll_y), 'x:', (e.x_min, e.x_max), 'y:', (e.y_min, e.y_max)
		elif e.rotation == 'R180':
			n.set_x( pl_info[brd_name].x + e.x_max )
			# ll_x = e.x_loc - (e.x_max)
			n.set_y( pl_info[brd_name].y + e.y_max )
			# ll_y = e.y_loc - (e.y_max)
			# print e.name, 'loc:', (e.x_loc, e.y_loc),'ll:', (ll_x, ll_y), 'x:', (e.x_min, e.x_max), 'y:', (e.y_min, e.y_max)
		elif e.rotation == 'R270':
			n.set_x( pl_info[brd_name].x - e.y_min )
			# ll_x = e.x_loc + (e.y_min)
			n.set_y( pl_info[brd_name].y + e.x_max )
			# ll_y = e.y_loc - (e.x_max)

	brd.write(out_file, check_sanity=False, dtd_validate=False) # should really pass sanity check and dtd



if __name__ == '__main__':
	arguments = docopt(__doc__, version='bookshelf2eagle v0.1')
	update_placements(
		brd_file=str(arguments['--brd']),
		pl_file=str(arguments['--pl']),
		out_file=str(arguments['--out'])
	)