# Very rudimentary protection agains DDoS
import time

class Connection():
	def __init__(self, addr):
		self.addr = addr
		self.time = time.time()

#1 for new conn, 0 for old but acceptable, -1 for deniable
def check_connection(conn_list, addr):
	for c in conn_list:
		if c.addr == addr:
			old_t = c.time
			c.time = time.time()
			return -1 if (c.time - old_t < 0.5) else 0
	return 1
def cleanup_old_connections(conn_list):
	for c in conn_list:
		t = time.time()
		if (t - c.time) > 20:
			conn_list.remove(c)
	return
