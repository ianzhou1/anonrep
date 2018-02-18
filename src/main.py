from threading import Thread
from client import Client
from server import Server
from util import Constants

# main class
def main():
	try:
		s = Server('localhost', 1234, 1)
		s.set_next_server('localhost', 1234)
		s.set_board('localhost', 7777)
		thread = Thread(target=s.run)
		thread.start()

		c = Client('localhost', 1234)
	except:
		s.ss.close()

if __name__ == '__main__':
	main()