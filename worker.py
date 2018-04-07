import socket, itertools, struct
from random import shuffle
print('import worked')

socks51=b'\x05\x01\x00'

def gen_hosts(f_0):
	a=[x for x in range(1)]
	shuffle(a)
	b=[x for x in range(256)]
	shuffle(b)
	c=[x for x in range(256)]
	shuffle(c)
	ports = [8088, 8888, 3128, 33555, 9050, 61177, 8060, 31544, 1080, 8080, 61234, 35618, 53281, 20183, 33012, 39880, 8081, 9999, 65000]
	q=itertools.product(a,b,c)
	while 1:
		try:
			zz = str(f_0) + '.' + ('.').join([str(x) for x in next(q)])
		except StopIteration: break
		zzz=((zz, i) for i in ports)
		while 1:
			try:
				yield next(zzz)
			except StopIteration: break
target=gen_hosts(67)
# target=iter([('127.0.0.1', 9050)])
# counter=0
# while 1:
# 	try:
# 		print(next(target))
# 		counter+=1
# 	except StopIteration:
# 		print(counter)
# 		break


def worker():
	### INDIVIDUAL PARAMETERS ###
	try:
		tartg = next(target)
		# print(tartg)
		s=yield True
	except StopIteration:
		print('out of addresses')
		yield False

	### INDIVIDUAL PARAMETERS ###


	try:
		s.connect(tartg)
	except BlockingIOError:
		pass
	except Exception as e:
		print(31, str(e))
		yield ('fin', 0)
	yield ('start', 4, 5)
	try:
		s.sendall(socks51)
	except Exception as e:
		print(32, str(e))
		yield ('fin', 0)

	yield ('mask', 1, 5)


	try:
		s51resp=s.recv(1024)
	except Exception as e:
		print(33, str(e))
		yield ('fin', 0)
	print('s51 received', s51resp)
	if len(s51resp)>0:
		if [x for x in s51resp]==[5,0]:
			yield ('ready', tartg) # ready socket + message to send
	yield ('fin', 0)
