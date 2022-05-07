import socket
import time
import random
import threading
import json
import string
import cryptography
# from rsa import *
# import rsa as rsa
from itertools import islice
import base64
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

UDP_PORT_NO = 2500
hostName = socket.gethostname()
HOST_IP = socket.gethostbyname(hostName)
UDP_SEND = (HOST_IP, UDP_PORT_NO)

buffer_size = 1024
uniqueKey = get_random_string(random.randint(5, 10))

timeout = random.randint(1, 4)
connectionEstablished = False
watingForACK = False
retransmitionCount = 0
instructions = ["Instructions:\nPress 1 to send any symptoms you are experiencing\nPress 0 to leave the server\n", "How are you feeling today?\nEnter symptoms seperated by comma and space\n"]

ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
Intrcution = "What is your name"

global DataPacket
global clientName

#Threads
global outT
global inT

# myPrivate, myPublic = rsa.newkeys(1024)
global SERVER_PUBLIC_KEY

myPrivate = RSA.generate(128 * 8)
myPublic = myPrivate.publickey()


####################################################    
def sendData(dataMessage, checksum, flagType):
    global watingForACK
    global DataPacket
    global data
        
    if not connectionEstablished:
        data = {
            "message": dataMessage,
            "flagType": flagType,
            "public_key": myPublic.exportKey().decode()
        }
        DataPacket = data
        data = json.dumps(data)
        data = data.encode('ascii')
    else:
        data = {
            "message": dataMessage,
            "flagType": flagType
        }
        DataPacket = data
        data = json.dumps(data)

        n = 116 # chunk length
        chunks = [data[i:i+n] for i in range(0, len(data), n)]
        key = PKCS1_OAEP.new(SERVER_PUBLIC_KEY)

        encrypted_data = b''
        for chunk in chunks:
            encrypted_data += key.encrypt(chunk)
        
            while len(encrypted_data) < 117:
                encrypted_data += "\x00" + encrypted_data

        if len(bytes) < 127:
            encrypted_data = "\x00" + encrypted_data 
        data = encrypted_data


    ClientSocket.sendto(data, UDP_SEND)
    watingForACK = True


    if DataPacket["flagType"] != "ACK":     
        print('Waiting for AKC packet............\n')

    if not connectionEstablished:
        #Start reciving thread when connection is getting established
        inT.start()
#################################################### 



####################################################
def checksum(msg):
    s = 0
    for i in range(0, len(msg)):
        s += ord(msg[i])
    return s
####################################################



####################################################
def respond():
    global connectionEstablished
    global clientName

    inputData = f'{input("")}'

    while True:
        if (instructions[0] == Intrcution):
            if str(inputData) == "1" or str(inputData) == "0":
                break
            print("Please enter either 1 or 0 to proceed, try again...")
        
        elif (instructions[1] == Intrcution) and inputData.isnumeric():
            print("Numbers are not allowed for this instruction, try again...")

        elif inputData == "" or inputData == None:
              print("Empty string is not allowed as input, try agian...\n")

        else:
            break

        print(Intrcution)
        inputData = f'{input("")}'

    checkSum = checksum(inputData)
    flagType = ""

    if not connectionEstablished:
        clientName = inputData
        flagType = "ESTAB"

    elif inputData == "0":
        flagType = "QUIT"

    else:
        flagType = "REPLY"
 
    sendData(inputData, checkSum, flagType) 
####################################################



####################################################
def receiveData():
    global Intrcution
    global watingForACK
    global retransmitionCount
    global connectionEstablished
    global SERVER_PUBLIC_KEY

    while True:
        try:
            dataPacket = ClientSocket.recvfrom(buffer_size)   
            s_data = (dataPacket[0])
            s_address = (dataPacket[1])

            if connectionEstablished:
                cipher = PKCS1_OAEP.new(myPrivate)
                s_data = cipher.decrypt(s_data)
            else:
                s_data.decode('ascii')

            data = json.loads(s_data)

            if data["flagType"] == "NAK":
                print("NAK packet recived, retransmitting..............\n")
                sendData(DataPacket["message"], DataPacket["checksum"], DataPacket["flagType"])


            if data["flagType"] == "BROADCAST":
                print("Broadcast from server")
                print(data["message"] + "\n")
                sendData("BROADCAST RECVIVED", checksum("BROADCAST RECVIVED"), "ACK")

            elif data["flagType"] == "QUIT":
                retransmitionCount = 0
                watingForACK = False
                print(data["message"] + "\n")

                ClientSocket.close()
                break
            
            elif data["flagType"] == "ACK":
                retransmitionCount = 0
                watingForACK = False
                print("ACK packet recived succesfully\n")


            elif data["flagType"] == "ESTAB":
                print(data["message"])
                SERVER_PUBLIC_KEY = RSA.import_key(data["public_key"].encode())
                # SERVER_PUBLIC_KEY = rsa.PublicKey((data["public_key"]), 1024)
                print(SERVER_PUBLIC_KEY.n)
                connectionEstablished = True

            elif data["flagType"] == "REPLY":
                print("Message from server")
                print(data["message"] + "\n")

                Intrcution = data["message"]

                outT = threading.Thread(target=respond)
                outT.start()
            # else:
            #     sendData("Retransmit, data loss", checksum("Retransmit, data loss"), "NAK")    
                                    
        except socket.error:
            #Catch any timed out retransmition errors, and handle according to retransmition count
            if watingForACK and retransmitionCount < 3:
                retransmitionCount+=1
                print("Time out, retransmitting......\n")  
                sendData(DataPacket["message"], DataPacket["checksum"], DataPacket["flagType"])

            elif retransmitionCount == 3:
                print("Retransmition limit reached\nServer seems to be off\nexiting....")
                ClientSocket.close()
                break

            else:
                break                                
####################################################           
    


####################################################
#Cleint Just started
print("HOST IP: " + HOST_IP + "\n")
print(Intrcution)

inT = threading.Thread(target=receiveData)
respond()
####################################################




