import sys
import threading
import socket
import time


def getsock():
    """ Returns a socket broadcasting/listening on port 6454 """
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind(('', 6454))
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	return sock


class ArtPollListener(threading.Thread):
    """ Listener thread after a PollRequest """

	def __init__(self, sock, broadcast_address):
		threading.Thread.__init__(self)
		self.running = False
		self.sock = sock
		self.broadcast_address = broadcast_address

	def stop(self):
        """ Enable stopping thread without deleting object """
		self.running = False

	def run(self):
		from artnet import packet

		ip_address = socket.gethostbyname(socket.gethostname())
		last_poll = time.time()

		def _poll():
            """ Send the PollPacket """
			p = packet.PollPacket(source=(ip_address, 6454))
			l = self.sock.sendto(p.encode(), (self.broadcast_address, packet.ARTNET_PORT))
			print 'poll packet: %s' % p

		self.sock.settimeout(0.0)
		self.running = True

        # send a PollPacket
		_poll()

		while(self.running):

            # resend a PollPacket every 4 seconds
			if(time.time() - last_poll >= 4):
				last_poll = time.time()
				_poll()

            # read then parse responses and respond to the poll when a
            # PollPacket incoming is identified
			try:
				data, addr = self.sock.recvfrom(1024)
			except socket.error, e:
				time.sleep(0.1)
				continue

			p = packet.ArtNetPacket.parse(addr, data)

			if(isinstance(p, packet.PollPacket)):
				r = packet.PollReplyPacket([], source=(ip_address, 6454))
				l = self.sock.sendto(r.encode(), (p.source[0], packet.ARTNET_PORT))
				print 'poll reply packet: %s' % r


def main():
	if(len(sys.argv) < 2):
		print "\nUsage:\n\tartnet_listener [address]\n"
		sys.exit(1)

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind(('', 6454))
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	l = ArtPollListener(sock, sys.argv[1])
	l.run()

if __name__=='__main__':
    main()

