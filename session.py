"""
Author: Sumukha Radhakrishna

"""

class session():
	def __init__(self, s='OFF', t='#'):
		self.state = s
		self.token = t

	def updatestate(self, st):
		self.state = st

	def updatetoken(self, to):
		self.token = to

	def getstate(self):
		return self.state

	def gettoken(self):
		return self.token