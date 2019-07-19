"""xml2bookshelf.

This program converts ESIR XML to bookshelf for placement.

Usage:
  xml2bookshelf.py -h | --help
  xml2bookshelf.py <XML> <PROJECT_NAME>

-h --help                   Show this message.
"""

# This is the correct license for this particular file. Do not modify or remove this license.
LICENCE = """
BSD 3-Clause License

Copyright (c) 2019, Devon James Merrill
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


import lxml
from lxml import etree
from docopt import docopt
import datetime



class Package(object):
	def __init__(self, name=None):
		self.name = name
		self.pads = {}
		self.layers = {}

class PinType(object):
	def __init__(self):
		self.x_offset = 0.0
		self.y_offset = 0.0


class Pose(object):
	def __init__(self, x='0.0', y='0.0', angle='0.0', flipx=False):
		assert x is not None
		assert y is not None
		self.x = float(x)
		self.y = float(y)
		self.angle = float(angle)
		self.flipx = bool(flipx)

	@staticmethod # all these classes should have a static method like this to initialize
	def from_etree(root): # this type of initializer might have to take dicts from the rest of the design for other classes (like package info)
		assert root.tag == 'POSE'
		x = root.get('x')
		y = root.get('y')
		angle = root.get('angle')
		flipx = root.get('flipx')
		assert x is not None, etree.tostring(root)
		assert y is not None, etree.tostring(root)
		return Pose(x=x, y=y, angle=angle, flipx=flipx)

	def __str__(self):
		return 'Pose(' + str(self.x) + ', ' + str(self.y) + ')'

	def __repr__(self):
		return str(self)

class Component(object):
	def __init__(self, name):
		self.name = name
		self.pins = {}
		self.layers = {}

class Net(object):
	def __init__(self, name):
		self.name = name
		self.pins = []

class Layer(object):
	def __init__(self, name, shapes=None):
		self.name = name
		if shapes is None:
			self.shapes = []
		self.shapes = shapes

	@staticmethod # all these classes should have a static method like this to initialize
	def from_etree(root): # this type of initializer might have to take dicts from the rest of the design for other classes (like package info)
		name = root.get('name')
		bottom = root.get('bottom')
		rects = [Rectangle(r) for r in root.findall('RECTANGLE')]
		assert len(rects) <= 1 # TODO make me work with more rects
		return Layer(name=name, shapes=rects)



class Rectangle(object):
	def __init__(self, root): # maybe refactor to static method
    	#<PCBLAYER name="PASTE" bottom="false"><RECTANGLE width="0.635" height="0.61"><POSE x="0.0" y="0.0" angle="0.0" flipx="false" /></RECTANGLE></PCBLAYER>
		self.root = root
		self.width = self.root.get('width')
		self.height = self.root.get('height')
		pose = Pose.from_etree(root.find('POSE'))
		self.x = pose.x
		self.y = pose.y
		self.angle = pose.angle
		self.flipx = pose.flipx

	def __str__(self):
		return 'Rectangle(w=' + str(self.width) + ', h=' + self.height + ', x=' + str(self.x) + ', y=' + str(self.y) + ')'

	def __repr__(self):
		return str(self)


def run_conversion(xml_file, project_name):
	with open(xml_file, 'r') as f:
		s = f.read()

	parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
	root = etree.fromstring(s, parser=parser)
	print(etree.tostring(root, pretty_print=True).decode())


	print('Finding packages...')
	package_map = {}
	packages = root.findall('PCBPACKAGE')
	for package in packages:
		name = package.get('name')
		assert name is not None
		package_map[name] = Package(name=name)

		pin_types = package.findall('PCBPAD')
		for pin_type in pin_types:
			pass

		pads = package.findall('PAD')
		assert len(pads) > 0
		package_map[name].pads = {}
		for pad in pads:
			iref = pad.find('INDEXREF').get('index')
			vref = pad.find('INDEXREF').find('VARREF').text
			pose = pad.find('POSE')
			pad_name = str(vref) + '[' + str(iref) + ']'
			# print('\t\t' + pad_name)
			package_map[name].pads[pad_name] = Pose(
				x=pose.get('x'),
				y=pose.get('y'),
				angle=pose.get('angle'),
				flipx=pose.get('flipx'),
			)
			# print(package_map[name].pads[pad_name])

		layers = package.findall('PCBLAYER')
		for layer in layers:
			layer_name = layer.get('name')
			bottom = layer.get('bottom')
			package_map[name].layers[layer_name] = Layer.from_etree(layer)


	for name, package in package_map.items():
		print(name, package, package.pads)


	print('Finding components...')
	components = root.findall('PCBCOMPONENT')
	component_map = {}
	for component in components:
		name = component.get('name')
		component_map[name] = Component(name=name)
		package_name = component.find('PACKAGE').get('package')
		package = package_map[package_name]
		print('\t' + name + ' package: ' + package_name)
		component_map[name].layers = package.layers
		print(package.pads)
		for pin_name, pin_pose in package.pads.items():
			component_map[name].pins[pin_name] = pin_pose
			print('\t' + pin_name)

	pcb_module = root.find('PCBMODULE')


	print('Finding instances...')
	component_insts = pcb_module.findall('INST')
	instance_map = {}
	for inst in component_insts:
		name = inst.get('name')
		component = component_map[inst.find('COMPONENT').text]
		instance_map[name] = component


	print('Finding nets...')
	nets = pcb_module.findall('NET')
	net_map = {}
	for net in nets:
		name = net.get('name')
		net_map[name] = Net(name)
		for pin in net.findall('INDEXREF'):
			iref = pin.get('index')
			fref = pin.find('FIELDREF').get('name')
			vref = pin.find('FIELDREF').find('VARREF').text
			pin_name = str(fref) + '[' + str(iref) + ']'
			component = instance_map[vref]
			net_map[name].pins.append((vref, component, pin_name))



	###########################################################################
	#	Data model is complete in memory.
	#	Ready to output to simplified placement model after this point.
	###########################################################################

	nets_header = ''
	nets_header += 'UCLA nets 1.0\n'
	nets_header += '\n'
	nets_header += '# Created    : ' + str(datetime.datetime.now()) + '\n'
	nets_header += '# Created by : ' + str(None) + '\n' # TODO
	nets_header += '\n'
	nets_header += 'NumNets : ' + str(None) + '\n' # TODO
	nets_header += 'NumPins : ' + str(None) + '\n' # TODO
	nets_header += '\n'

	nodes_header = ''
	nodes_header += 'UCLA nodes 1.0\n'
	nodes_header += '\n'
	nodes_header += '# Created    : ' + str(datetime.datetime.now()) + '\n'
	nodes_header += '# Created by : ' + str(None) + '\n' # TODO
	nodes_header += '\n'
	nodes_header += 'NumNodes : ' + str(None) + '\n' # TODO
	nodes_header += 'NumTerminals : ' + '0' + '\n'
	nodes_header += '\n'

	pl_header = ''
	pl_header += 'UCLA pl 1.0\n'
	pl_header += '\n'
	pl_header += '# Created    : ' + str(datetime.datetime.now()) + '\n'
	pl_header += '# Created by : ' + str(None) + '\n' # TODO
	pl_header += '\n'

	nodes_str = ''
	for name, component in instance_map.items():
		# print('\tComponent name: ' + name + ' outline: ' + str(component.layers['COURTYARD'].shapes[0]))
		nodes_str += name + ' ' + component.layers['COURTYARD'].shapes[0].width + ' ' + component.layers['COURTYARD'].shapes[0].height # bookshelf style
		nodes_str += '\n'

	pl_str = ''
	for name, component in instance_map.items():
		pl_str += name + ' 0.0 0.0 : N'
		pl_str += '\n'

	nets_str = ''
	for name, net in net_map.items():
		nets_str += name + ' : ' + str(len(net.pins))
		nets_str += '\n'
		for pin in net.pins:
			inst = pin[0]
			component = pin[1]
			pin_name = pin[2]
			pose = component.pins[pin_name]
			# print('\t' + inst + '.' + pin_name + ' : ' + str(pose.x) + ' ' + str(pose.y))
			nets_str += '\t' + inst + ' B : ' + str(pose.x) + ' ' + str(pose.y) # bookshelf style
			nets_str += '\n'




	with open(project_name + '.nodes', 'w') as file:
		file.write(nodes_header + nodes_str)

	with open(project_name + '.nets', 'w') as file:
		file.write(nets_header + nets_str)

	with open(project_name + '.pl', 'w') as file:
		file.write(pl_header + pl_str)


if __name__ == '__main__':
	arguments = docopt(__doc__, version='xml2bookshelf v0.1')
	run_conversion(
		xml_file=str(arguments['<XML>']), 
		project_name=str(arguments['<PROJECT_NAME>'])
	)