"""
Author: Sumukha Radhakrishna
Client Program.
Run: client.py a

"""

import socket
import sys
import time
import threading
from random import randint

import util
from session import session

CLIENT_ADDR = util.getClientAddress(str(sys.argv[1]))
print(CLIENT_ADDR)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(CLIENT_ADDR)
session_lock = threading.Lock()
_session_ = session()
curctr = 1


def recclient():
    while True:
        time.sleep(0.5)
        data, addr = s.recvfrom(1024)

        length = 9 + int(data[3])

        if data[0] != util.MYINIT_1 or data[1] != util.MYINIT_2:
            print('\t\t\t\t\t\t\tHeader Unknown format.')
            continue

        if data[2] == util.OPCODE_LOGIN_ACK:
            token = data[4:8].decode('utf-8')
            if token != '####':
                with session_lock:
                    _session_.updatestate('ON')
                    _session_.updatetoken(token)
            msg = data[9: length].decode('utf-8')
            print("\t\t\t\t\t\t\t"+msg)

        elif data[2] == util.OPCODE_SESSION_TERMINATED_ACK:
            msg = data[9: length].decode('utf-8')
            with session_lock:
                _session_.updatetoken('#')
                _session_.updatestate('OFF')
            print('\t\t\t\t\t\t\t'+msg)
            print('\t\t\t\t\t\t\t Session Terminated. Login Again.')
            print('\nEnter login#username&password to login \n(Q to quit the program) \n')

        elif data[2] == util.OPCODE_LOGOUT_ACK:
            with session_lock:
                _session_.updatetoken('#')
                _session_.updatestate('OFF')
            print('\t\t\t\t\t\t\tLogged out. Login Again.')
            print('\nEnter login#username&password to login \n(Q to quit the program) \n')

        elif data[2] == util.OPCODE_SUBSCRIBE_ACK:
            print('\t\t\t\t\t\t\tSubscribed.')

        elif data[2] == util.OPCODE_SUBSCRIBE_FAILED_ACK:
            print('\t\t\t\t\t\t\tSubscribe Failed.')

        elif data[2] == util.OPCODE_UNSUBSCRIBE_FAILED_ACK:
            print('\t\t\t\t\t\t\tUnsubscribe Failed.')

        elif data[2] == util.OPCODE_RETRIEVE_FAILED_ACK:
            print('\t\t\t\t\t\t\tRetrieve Failed.')

        elif data[2] == util.OPCODE_UNSUBSCRIBE_ACK:
            print('\t\t\t\t\t\t\tUnsubscribed.')

        elif data[2] == util.OPCODE_POST_ACK:
            print('\t\t\t\t\t\t\tPOST successful.')

        elif data[2] == util.OPCODE_RETRIEVE_ACK:
            ntweets = int(data[9: length].decode('utf-8'))
            while ntweets:
                data, addr = s.recvfrom(1024)
                length = 9 + int(data[3])
                tweet = data[9: length].decode('utf-8')
                print('\t\t\t\t\t\t\t\tTweet No-'+str(ntweets))
                print('\t\t\t\t\t\t\t\t'+tweet)
                ntweets -=1
            print('\t\t\t\t\t\t\t Retrieve Done.\n')

        elif data[2] == util.OPCODE_POSTPICMSG:
            bytestoberead = data[9: length].decode('utf-8')
            create_destroy_thread(handle_pic_post, bytestoberead)
            print('\t\t\t\t\t\t\t SOMEONEPOSTED A PICTURE.\n')



        elif data[2] == util.OPCODE_REALTIMETWEET:
            msg, client = data[9: length].decode('utf-8').split('&')
            print("\t\t\t\t\t\t\tClient- "+client+" Tweeted.")
            print("\t\t\t\t\t\t\t"+msg)

        elif data[2] == util.OPCODE_RESET_ACK:
            print("\t\t\t\t\t\t\t\tSession RESET has been done..")
            with session_lock:
                _session_.updatetoken('#')
                _session_.updatestate('OFF')


        else:
            print("\t\t\t\t\t\t\t\tSession RESET by CLIENT")
            with session_lock:
                current_token = _session_.gettoken()
            m = util.message(util.OPCODE_RESET, "Session RESET by CLIENT", current_token)
            s.sendto(m.getencodedmsg(), util.SERVER_ADDR)


def runclient():
    while True:
        time.sleep(1)
        with session_lock:
            current_token = _session_.gettoken()
            print("Current Token = "+current_token)
            current_state = _session_.getstate()
        if current_state == 'OFF':
            inputmessage = input('\nEnter login#username&password to login \n(Q to quit the program) \n')
            if inputmessage.startswith('login#'):
                logininfo = inputmessage.split('#')[1]
                m = util.message(util.OPCODE_LOGIN, logininfo)
            elif inputmessage == 'Q':
                exit()
            else:
                print("Please Login.\n")
                continue
        else:
            inputmessage = input('\nLogged in.\n(logout#, subscribe#, unsubscribe#, post# retrieve#, spurious_client#, spurious_server#, postpicmsg#)\n')
            with session_lock:
                current_token = _session_.gettoken()
                current_state = _session_.getstate()
            if current_state == 'OFF':
                print("Login First")
                continue
            if inputmessage.startswith('subscribe#'):
                subscribername = inputmessage.split('#')[1]
                m = util.message(util.OPCODE_SUBSCRIBE, subscribername, current_token)

            elif inputmessage.startswith('unsubscribe#'):
                subscribername = inputmessage.split('#')[1]
                m = util.message(util.OPCODE_UNSUBSCRIBE, subscribername, current_token)

            elif inputmessage.startswith('post#'):
                tweet = inputmessage.split('#')[1]
                m = util.message(util.OPCODE_POST, tweet, current_token)

            elif inputmessage.startswith('retrieve#'):
                ret = inputmessage.split('#')[1]
                m = util.message(util.OPCODE_RETRIEVE, ret, current_token)

            elif inputmessage.startswith('spurious_client#'):
                ret = 'logout'
                m = util.message(0xFF, ret, current_token)

            elif inputmessage.startswith('spurious_server#'):
                ret = 'logout'
                m = util.message(util.OPCODE_SPURIOUS, ret, current_token)

            elif inputmessage.startswith('logout#'):
                ret = 'logout'
                m = util.message(util.OPCODE_LOGOUT_ACK, ret, current_token)

            elif inputmessage.startswith('postpicmsg#'):
                imgname = input("Enter the Name of the Image.\n")
                imgpath = "/home/sumukha/CSE434/assignment4/client/"+imgname
                with open(imgpath, 'rb') as f:
                    file_content = f.read()  # Read whole file in the file_content string
                ret =  str(len(file_content))
                m = util.message(util.OPCODE_POSTPICMSG, ret, current_token)
                s.sendto(m.getencodedmsg(), util.SERVER_ADDR)
                create_destroy_thread(SendPicture, file_content)
                continue
            else:
                    print('Unknown Operation/Format.')
                    continue

        s.sendto(m.getencodedmsg(), util.SERVER_ADDR)
    print('Client Exiting..')

def create_destroy_thread(f, args_=None):
    tcp = threading.Thread(target=f, args=(args_,))
    tcp.start()
    tcp.join()

def SendPicture(file_content):
    print("Posting the Picture...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as skt:
        time.sleep(2)
        skt.connect(util.SERVER_ADDR)
        skt.sendall(file_content)
    print("Done Posting pictures.")

def handle_pic_post(bufferlen):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as skt:
        skt.bind(CLIENT_ADDR)
        skt.listen()
        conn, addr = skt.accept()
        with conn:
            print('Receiving Picture', addr)
            data = conn.recv(int(bufferlen))

    with open("/home/sumukha/CSE434/assignment4/client/"+str(sys.argv[1])+"/"+str(randint(1,10))+".jpg", 'wb+') as a:
        a.write(data)

"""
login#client_a&pass_a

"""

if __name__ == "__main__":

    x = threading.Thread(target=runclient)
    y = threading.Thread(target=recclient)
    x.start()
    y.start()
    x.join()
    y.join()