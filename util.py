"""
Author: Sumukha Radhakrishna

"""
MYINIT_1 = 0x53
MYINIT_2 = 0x52
OPCODE_LOGIN = 0x01
OPCODE_LOGIN_ACK = 0x02
OPCODE_POST = 0x03
OPCODE_POST_ACK = 0x04
OPCODE_LOGOUT_ACK = 0x05

OPCODE_SUBSCRIBE = 0x07
OPCODE_SUBSCRIBE_ACK = 0x08
OPCODE_UNSUBSCRIBE = 0x09
OPCODE_UNSUBSCRIBE_ACK = 0x0A
OPCODE_RETRIEVE = 0x0B
OPCODE_RETRIEVE_ACK = 0x0C
OPCODE_UNRECOGNIZED_SESSION = 0x0D
OPCODE_REALTIMETWEET = 0x0E
OPCODE_RETRIEVE_TWEET = 0x0F
OPCODE_SESSION_TERMINATED_ACK = 0x11
OPCODE_SPURIOUS = 0xFA
OPCODE_SUBSCRIBE_FAILED_ACK = 0xFB
OPCODE_UNSUBSCRIBE_FAILED_ACK = 0xFC
OPCODE_RETRIEVE_FAILED_ACK = 0xFD
OPCODE_RESET_ACK = 0xBB
OPCODE_RESET = 0xBA
OPCODE_POSTPICMSG = 0xCD

HOST_IP = '127.0.0.1'
SERVER_PORT = 32000  # port to listen on
def getClientAddress(s):
    global CLIENT_PORT
    if s == 'a':
        CLIENT_PORT = 32001
    if s == 'b':
        CLIENT_PORT = 32002
    if s == 'c':
        CLIENT_PORT = 32003
    return (HOST_IP, CLIENT_PORT)


SERVER_ADDR = (HOST_IP, SERVER_PORT)
ACK_COUNT = int(0)

import threading
ack_count_lock = threading.Lock()


class message():
    def __init__(self, opcode, m, token = "####", ack=False):
        self.message = bytearray(1024)
        self.message[0] = MYINIT_1
        self.message[1] = MYINIT_2
        self.message[2] = opcode
        self.message[3] = len(m)
        self.message[4:8] = str(token).encode('utf-8')
        offset = 8
        if ack:
            with ack_count_lock:
                global ACK_COUNT
                ACK_COUNT += 1
                self.message[8] = int(ACK_COUNT)
            offset = 9
        self.message[offset:] =  bytearray(m.encode('utf-8'))

    def getencodedmsg(self):
        return self.message