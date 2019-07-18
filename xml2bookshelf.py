from lxml import etree


class Package(object):
	def __init__(self, name=None):
		self.name = name
		self.pads = {}

class PinType(object):
	def __init__(self):
		self.x_offset = 0.0
		self.y_offset = 0.0

class Pose(object):
	def __init__(self, x='0.0', y='0.0', angle='0.0', flipx=False):
		self.x = float(x)
		self.y = float(y)
		self.angle = float(angle)
		self.flipx = bool(flipx)

	def __str__(self):
		return 'Pose(' + str(self.x) + ', ' + str(self.y) + ')'

	def __repr__(self):
		return str(self)

class Component(object):
	def __init__(self, name):
		self.name = name
		self.pins = {}

class Net(object):
	def __init__(self, name):
		self.name = name
		self.pins = []


with open('a-resistor.xml', 'r') as f:
	s = f.read()

parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
root = etree.fromstring(s, parser=parser)
print(etree.tostring(root, pretty_print=True).decode())



print('Finding packages...')
package_map = {}
packages = root.findall('PCBPACKAGE')
for package in packages:
	name = package.get('name')
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

# exit(-1)

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

print()
print('Nets:')
for name, net in net_map.items():
	print(name + ' : ' + str(len(net.pins)))
	for pin in net.pins:
		inst = pin[0]
		component = pin[1]
		pin_name = pin[2]
		pose = component.pins[pin_name]
		# print('\t' + inst + '.' + pin_name + ' : ' + str(pose.x) + ' ' + str(pose.y))
		print('\t' + inst + ' B : ' + str(pose.x) + ' ' + str(pose.y))

