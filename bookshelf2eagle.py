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

				comp2rot[pname] = r
				rot2deg = {'N':0,'S':180,'E':90,'W':270}
				components[pname] = Component(x=newx, y=newy, rotdeg=rot2deg[r], locked=locked)
	return components


def update_placements(
	brd_file,
	pl_file,
	out_file,
):

	brd = Swoop.EagleFile.from_file(brd_file)

	components = read_pl2(pl_file)

	# get the elements (components/blocks/nodes)
	elements = {}
	for n in (Swoop.From(brd).
		get_elements()
	):
		name = n.get_name()
		if name in components:
			c = components[name]
			n.set_x(c.x)
			n.set_y(c.y)
			if c.rot is not None:
				n.set_rot(c.rot)
			n.set_locked = c.locked

	brd.write(out_file, check_sanity=True, dtd_validate=True)



if __name__ == '__main__':
	arguments = docopt(__doc__, version='bookshelf2eagle v0.1')
	update_placements(
		brd_file=str(arguments['--brd']),
		pl_file=str(arguments['--pl']),
		out_file=str(arguments['--out'])
	)