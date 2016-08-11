import os, sys, jsonParser, re, json, collections

products = None
listings = None
connections = None
productTree = None

# Get the data into a format we can use
# Use a third-party loader due to unicode issues with the built-in version
def parseJsonFile(fname):
	returnArr = []
	with open(fname, 'r') as f:
		for l in f.readlines():
			returnArr.append(jsonParser.json_loads_byteified(l))
	return returnArr

class ProductNode:

	def __init__(self, idString, tabLevel=0):
		self.idString = idString
		# This way we search for the whole model string first, before searching the model substrings
		self.children = collections.OrderedDict()
		# Just for printing
		self.tabLevel = tabLevel

	def addChild(self, node):
		self.children[node.idString] = node

	def printPretty(self):
		print self.tabLevel * '\t' + self.idString
		for c in self.children:
			self.children[c].printPretty()

# Build the product tree. 
# 4 Levels of nodes: Top -> Manufacturer -> Model -> Product
def checkProductNode(n, idString, k):
	if k == 'model':
		# Split the model string up into multiple parts, because some listings only use part of it
		modelArgs = [idString] + re.findall('[\w\d]+', idString)
		retNodes = []
		
		for arg in modelArgs:
			if len(arg) > 1:
				# If it's only 2 characters, it's fine
				isValidModel = len(arg) <= 3
				# If it's a mix of letters and numbers, it's fine
				isValidModel = isValidModel or not arg.isalpha()
				# If it's a capitalized word like Zoom or Tough, it's not fine.
				isValidModel = isValidModel or not (arg[0].upper() == arg[0] and arg[1:].lower() == arg[1:])
				
				if isValidModel:
					newChild = ProductNode(arg, n.tabLevel + 1)
					n.addChild(newChild)
					retNodes.append(newChild)

		if len(modelArgs) > 2:
			return retNodes

	if not idString in n.children:
		newChild = ProductNode(idString, n.tabLevel + 1)
		n.addChild(newChild)
		return newChild

	else:
		return n.children[idString]

def makeTree():
	# Make tree of Manufacturer -> Model -> Name
	for prod in products:
		currentParent = productTree
		keys = ['manufacturer', 'model', 'product_name']
		
		for k in keys:

			if k in prod:
				v = str(prod[k])
			else:
				v = 'NONE'

			if isinstance(currentParent, list):
				retNodes = []
				for node in currentParent:
					retNodes.append(checkProductNode(node, v, k))
				currentParent = retNodes
			else:
				currentParent = checkProductNode(currentParent, v, k)

# Do some regex to see if the two strings are similar
def compareInfo(idStringPassed, data):
	idString = idStringPassed
	if idString == 'NONE':
		idString = '' 

	idString = re.sub('[_\- ]', '', idString)
	dataString = re.sub('[_\- ]', '', data)

	idSearchString = '.*'+re.escape(idString)+'.*'
	idSearchString = re.sub('[_\- ]', '.?', idSearchString)
	idSearchString = re.compile(idSearchString, re.I)

	found = re.search(idSearchString, dataString)
	return found

def searchTree(n, l):
	global connections
	checkData = l['manufacturer'] + l['title']

	# Traverse the product tree until we find it
	for childId in n.children:

		if n.children[childId].tabLevel == 3:
			if childId in connections:
				connections[childId].append(l)
			else:
				connections[childId] = [l]
			return True

		if compareInfo(childId, checkData):
			found = searchTree(n.children[childId], l)
			if found:
				return found

	return False

def searchListings():
	foundCount = 0
	unFoundCount = 0

	for l in listings:
		ret = searchTree(productTree, l)
		if ret:
			foundCount += 1
		else:
			unFoundCount += 1

	print 'Found: ', foundCount
	print 'Not Found: ', unFoundCount

def printResults():
	global connections
	with open('results.txt', 'w') as f:	
		for k, v in connections.items():
			printObj = {
				'product_name': k,
				'listings': v
			}
			f.write(json.dumps(printObj) + '\n')
			
def main():
	global products, listings, productTree, connections
	products = parseJsonFile('products.txt')
	listings = parseJsonFile('listings.txt')
	productTree = ProductNode('TOP')
	connections = {}

	makeTree()
	searchListings()
	printResults()

main()