import re
import sys
from util import Constants, randkey, powm, send

# client class
class Client:
	def __init__(self, server_host, server_port):
		# core variables
		self.pri_key = randkey()
		self.pub_key = powm(Constants.G, self.pri_key)

		# socket variables
		self.server_addr = (server_host, server_port)

		# new client
		send(self.server_addr, [Constants.NEW_CLIENT, self.pub_key])

	def post(self, msg, nym, sig):
		# new message post
		msg = '{} {} {} {}'.format(Constants.NEW_MESSAGE, msg, nym, sig)
		send(self.server_addr, msg)

def show_help():
	print('Instructions:')
	print('--------------------------------------------------------')
	print('HELP           : Displays this help message')
	print('SHOW           : Shows message')
	print('WRITE          : Write a message')
	print('VOTE UP [num]  : Votes up the message with ID [num]')
	print('VOTE DOWN [num]: Votes down the message with ID [num]')
	print('--------------------------------------------------------')

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('USAGE: python client.py server_host server_port')
		sys.exit(1)
	c = Client(sys.argv[1], int(sys.argv[2]))
	show_help()
	while True:
		try:
			s = input('> ').upper()
			# TODO Add actual commands. Possible commands are display messages, add message, vote up/down message
			if s == 'HELP':
				show_help()
			elif s == 'SHOW':
				# TODO
				pass
			elif s == 'WRITE':
				# TODO
				pass
			elif re.match("VOTE UP \d+", s) is not None:
				# TODO
				pass
			elif re.match("VOTE DOWN \d+", s) is not None:
				# TODO
				pass
			else:
				print('Invalid command. Type in HELP for instructions.')
		except KeyboardInterrupt:
			print()
			break
