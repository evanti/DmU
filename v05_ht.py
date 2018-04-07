import gc, select, sys, time, socket, selectors, os, subprocess
from multiprocessing import Process, Manager
from worker import *

class Task(object):
	def __init__(self, sock):
		self.target=worker() # this must be the name of the target function
		self.status=True
		self.socket=sock
		self.stillworking=self.target.send(None) #send False from worker if we're finished, use StopIter exception in worker
		if self.stillworking:
			fisrt_conn_res = self.target.send(sock)
			if fisrt_conn_res[0]=='start':
				self.first_mask = fisrt_conn_res[1]
				self.ttime = int(time.time() + fisrt_conn_res[2])
				return
		self.close()
		self.status=False
		return

	def close(self):
		self.target.close()
		self.socket.close()

	def run(self):
		try:
			output=self.target.send(None)
		except StopIteration:
			self.target.close()
			output=('fin', 0)
		return output
	def __repr__(self):
		q=('-').join((str(self.target),  str(self.fd), str(self.ttime - int(time.time()))))
		return q

def showstats(taskdict):
	global p_success_list
	bb=[]
	for i in taskdict:
		bb.append(taskdict[i].target.gi_frame.f_lineno)
	cc=set(bb)
	dd={}
	for i in cc:
		dd[i]=bb.count(i)
	with open("attack_stats.txt", 'a') as fi:
		print('Total tasks:', len(taskdict), file=fi)
		for key in sorted(dd):
			print('%s: %s' % (key, dd[key]), file=fi)

def process(max_work, attack_chunk, attack_timeout, cycles_num):
	still_working=True
	first=time.time()
	last=time.time()
	lastres=0
	def add_new_task():
		try:
			s=socket.socket()
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s.setblocking(False)
		except OSError:
			return False
		a = Task(s)
		if a.stillworking and a.status:
			sel.register(s.fileno(), 4)# select.EPOLLOUT | select.EPOLLET)
			taskmap[s.fileno()]=a
			task_counter.append(1)
			return True
		if not a.stillworking:
			return 'Exhausted'
		if not a.status:
			return 'Retry'

	def ready():
		ready=sel.poll(0)
		if not ready: print('bad')
		return ready

	''' First the setup '''
	sel = select.epoll()
	# sel=selectors.DefaultSelector()
	taskmap = {}
	attacklist=[]
	k=0
	'''Now execution'''
	while 1:

		'''Main loop'''
		while 1:
			events=ready()
			if not events and len(taskmap)<max_work and still_working:
				for i in range(20000):
					res=add_new_task()
					if res=='Exhausted':
						still_working=False
						break
					elif res=='Retry':
						break
			else:
				if len(taskmap)==0: exit()
				break
		if time.time() > last + 1:
			last = time.time()
			print('Done in last second', len(task_counter) - lastres, 'working', len(taskmap), 'totally', len(task_counter))
			lastres = len(task_counter)
		for key, event in events:
			if event not in [1,4]:
				sel.unregister(key)
				taskmap[key].target.close()
				del taskmap[key]
				continue
			res = taskmap[key].run()
			if res[0]=='mask':
				sel.modify(key, res[1])
				taskmap[key].ttime=int(time.time()+res[2])
			# print('Time set', taskmap[key].ttime)
			elif res[0]=='fin':
				sel.unregister(key)
				taskmap[key].close()
				del taskmap[key]
				continue
			elif res[0]=='ready':
				sel.unregister(key)
				attacklist.append(res[1])
				taskmap[key].close()
				del taskmap[key]

		'''Attack launcher'''
		if len(attacklist)>=attack_chunk:

			p1 = Process(target=attack, args=(attacklist,))
			p1.start()
			# showstats(taskmap)
			p_success_list.append(len(attacklist))

			attacklist.clear()

		'''Gagbage cleaning'''
		if time.time()>=first+3:
			first=time.time()
			now = int(time.time())
			del_list=[]
			for i in taskmap:
				if taskmap[i].ttime and taskmap[i].ttime < now:
					sel.unregister(i)
					taskmap[i].close()
					del_list.append(i)
			if len(del_list)==0: print('BAD', len(del_list))
			for i in del_list:
				del taskmap[i]


def attack(strikelist):
	res = []
	for i in strikelist:
		res.append((':').join((i[0], str(i[1]))))
	with open('scanres.txt', 'a') as fi:
		for i in res:
			fi.write(str(i)+'\n')
	sys.exit(0)

manager = Manager()
p_success_list=manager.list()
task_counter=manager.list()
eff_list=manager.list()

def mainloop():
	global p_success_list
	maximum_workers = 500000
	attack_chunk=1
	cycles = 50000  # before respawning processes
	conc_proc = 1  # concurrent processes
	repetitions=1 # NUMBER OF PROCESS RESPAWNS


	attack_time_limit = 55
	starttime = time.time()
	total_number=0
	for _ in range(repetitions):
		process_time=time.time()
		jobs=[]
		try:
			for j in range(conc_proc):
				p=Process(target=process, args=(maximum_workers, attack_chunk, attack_time_limit, cycles ))
				jobs.append(p)
			for p in jobs:
				p.start()
			for p in jobs:
				p.join()
		except:
			pass
		finally:
			total_time = time.time() - starttime
			total_number = sum(p_success_list)
			efficiency = int(total_number / total_time)
			# eff_list.append((efficiency, attack_number, attack_chunk,conc_proc))
			print("Total efficiency", int(efficiency), "total number:", total_number, 'time', str(int(total_time)))



if __name__=='__main__':
	mainloop()
