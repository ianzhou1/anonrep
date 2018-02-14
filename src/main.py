from threading import Thread
from client import Client
from server import Server
from util import Constants

# main class
def main():
	s = Server('localhost', 1234)
	thread = Thread(target=s.run)
	thread.start()

	c = Client('localhost', 1234)

if __name__ == '__main__':
	main()