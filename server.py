"""
Author: Sumukha Radhakrishna
Server Program.
Run: server.py

login#client_a&pass_a
login#client_b&pass_b
login#client_c&pass_c



"""
import socket
import sys
import util
import time
import threading
import secrets
import collections
import heapq


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(util.SERVER_ADDR)

tweet = collections.defaultdict(collections.deque)
time_ = 0

subdict = {
	"client_a":set(),
	"client_b":set(),
	"client_c":set()
}
subdict['client_a'].add('client_a')
subdict['client_b'].add('client_b')
subdict['client_c'].add('client_c')
subdict_2 = {
	"client_a":set(),
	"client_b":set(),
	"client_c":set()
}
subdict_2['client_a'].add('client_a')
subdict_2['client_b'].add('client_b')
subdict_2['client_c'].add('client_c')

updict = {
	"client_a":"pass_a",
	"client_b":"pass_b",
	"client_c":"pass_c"
}
tokens = {}
authdict = {}
auth_lock = threading.Lock()

sendack_lock = threading.Lock()


def post(userId, t):
	global time_
	tweet[userId].appendleft([time_, t])
	time_ += 1

def getNewsFeed(userId, n):
	result = []
	heap = []
	followers = list(subdict_2[userId])
	fset = set()
	for follower in followers:
		if len(tweet[follower]) != 0:
			heapq.heappush(heap, (-1 * tweet[follower][0][0], tweet[follower][0][1], 0, follower))
			fset.add(follower)
	while len(heap) != 0 and len(result) < n and fset:
		m, t, idx, f = heapq.heappop(heap)
		result.append(t)
		if idx == len(tweet[f]) - 1:
			fset.remove(f)
		else:
			idx += 1
			heapq.heappush(heap, (-1 * tweet[f][idx][0], tweet[f][idx][1], idx, f))
	return result

def getClient(s):
	if s == 'client_a':
		p = 32001
	if s == 'client_b':
		p = 32002
	if s == 'client_c':
		p = 32003
	return ('127.0.0.1', p)

def checkauth():
	while True:
		time.sleep(5)
		if len(authdict) == None:
			continue
		with auth_lock:
			arr = list(authdict.keys())
		for client in arr:
			endtime = time.time()
			with auth_lock:
				if endtime-authdict[client] > 60:
					print("\t\t\t\t\t\t\t\t"+client+' Session Terminated.')
					del authdict[client]
					sendack(util.OPCODE_SESSION_TERMINATED_ACK, 'Session Terminated.', getClient(client))
					del tokens[client]


def sendack(opcode, msg, CLIENT_ADDR, token=None):
	with sendack_lock:
		print("\t\t\t\t\t\t\t\tSending the ack back.\n")
		m = util.message(opcode, msg,token, ack=True )
		s.sendto(m.getencodedmsg(), CLIENT_ADDR)


def runserver():
	while True:
		print('\nWaiting for Client...')
		with auth_lock:
			for i in authdict.keys():
				print(""+i+" is Logged in.\n")
		data, addr = s.recvfrom(1024)
		print('Server connected to '+repr(addr))
		if data[0] != util.MYINIT_1 or data[1] != util.MYINIT_2:
			print('Header Unknown format.')
			continue
		#login
		length = 8 + int(data[3])
		if data[2] == util.OPCODE_LOGIN:
			token = "####"
			uname, password = data[8: length].decode('utf-8').split('&')

			if uname in updict and updict[uname] == password:
				replymsg = 'Login Successful.'
				token = secrets.token_hex(2)
				with auth_lock:
					authdict[uname] = time.time()
					tokens[uname] = token
			else:
				replymsg = 'Username and Password incorrect.'
			print(replymsg+ " Token - "+token)
			sendack(util.OPCODE_LOGIN_ACK, replymsg,addr, token)
			continue



		else:
			clienttoken = data[4:8].decode('utf-8')
			currentclient = ""
			with auth_lock:
				for k, v in tokens.items():
					if clienttoken == v:
						currentclient = k
						authdict[currentclient] = time.time()

			if currentclient == "":
				sendack(util.OPCODE_UNRECOGNIZED_SESSION, "Unrecognized Session.", addr)
				continue

			if data[2] == util.OPCODE_LOGOUT_ACK:
				print('\t\t\t\t\t\t\t\tLogout Successful.\n')
				del authdict[currentclient]
				del tokens[currentclient]
				sendack(util.OPCODE_LOGOUT_ACK, "Logout Successful.", addr)
				continue

			elif data[2] == util.OPCODE_SUBSCRIBE:
				newsub = data[8: length].decode('utf-8')
				with auth_lock:
					if not newsub in subdict:
						print('\t\t\t\t\t\t\t\tSubscribe Failed.\n')
						sendack(util.OPCODE_SUBSCRIBE_FAILED_ACK, "Subscribe Failed.", addr)
					else:
						print('\t\t\t\t\t\t\t\tSubscribe Successful.\n')
						subdict[newsub].add(currentclient)
						subdict_2[currentclient].add(newsub)
						sendack(util.OPCODE_SUBSCRIBE_ACK, "Subscribe Successful.", addr)

			elif data[2] == util.OPCODE_UNSUBSCRIBE:
				unsub = data[8: length].decode('utf-8')
				with auth_lock:
					if not unsub in subdict:
						print('\t\t\t\t\t\t\t\tUnsubscribe Failed.\n')
						sendack(util.OPCODE_SUBSCRIBE_FAILED_ACK, "Unsubscribe Failed.", addr)
					else:
						print('\t\t\t\t\t\t\t\tUnsubscribe Successful.\n')
						subdict[unsub].remove(currentclient)
						subdict_2[currentclient].remove(unsub)
						sendack(util.OPCODE_UNSUBSCRIBE_ACK, "Unsubscribe Successful.", addr)

			elif data[2] == util.OPCODE_RETRIEVE:
				ntweetstoret = int(data[8: length].decode('utf-8'))
				ntweets = getNewsFeed(currentclient, ntweetstoret)
				if len(ntweets) == 0:
					print('\t\t\t\t\t\t\t\tRetrieve Failed.\n')
					sendack(util.OPCODE_RETRIEVE_FAILED_ACK, "Retrieve Failed.", addr)
				else:
					sendack(util.OPCODE_RETRIEVE_ACK, str(ntweetstoret), addr)
					while ntweetstoret:
						sendack(util.OPCODE_RETRIEVE_TWEET, ntweets[ntweetstoret-1], addr)
						ntweetstoret -= 1
					print('\t\t\t\t\t\t\t\tRetrieve Successful.\n')


			elif data[2] == util.OPCODE_POST:
				currenttweet = data[8: length].decode('utf-8')
				post(currentclient, currenttweet)
				subscribers = subdict[currentclient]
				for sub in subscribers:
					sendack(util.OPCODE_REALTIMETWEET, currenttweet+'&'+currentclient, getClient(sub))
				sendack(util.OPCODE_POST_ACK, "POST Successful.", addr)
				print('\t\t\t\t\t\t\t\tPOST Successful.\n')

			elif data[2] == util.OPCODE_SPURIOUS:
				print('\t\t\t\t\t\t\t\tSession RESET by Client\n')
				sendack(0xFF, 'Session RESET by CLIENT.', addr)

			elif data[2] == util.OPCODE_RESET:
				del authdict[currentclient]
				sendack(util.OPCODE_RESET_ACK, 'Session RESET by CLIENT.', addr)
				del tokens[currentclient]

			else:
				print('Unrecognized OPCODE. Resetting Session\n')
				del authdict[currentclient]
				sendack(util.OPCODE_SESSION_TERMINATED_ACK, 'Session RESET by SERVER.', addr)
				del tokens[currentclient]





if __name__ == '__main__':
	x = threading.Thread(target=runserver)
	y = threading.Thread(target=checkauth)
	x.start()
	y.start()
