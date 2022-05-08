from email import message
import socket
import time
import random
import threading
import json
import string


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



#FOMAT FOR SENDING DATA JSON OBJECT
#
# data = {
# 		"checksum": checksum(message),
# 		"message": message,
# 		"flagType": "BROADCAST",
# 	}
#
# Flag Types
# BROADCAST, ESTAB, ACK, NAK, REPLY, QUIT



####################################################    
def sendData(dataMessage, checksum, flagType):
    global watingForACK
    global DataPacket

    try:
        data = {
            "checksum": checksum,
            "message": dataMessage,
            "flagType": flagType
        }

        DataPacket = data

        data = json.dumps(data)
        ClientSocket.sendto(data.encode('ascii'), UDP_SEND)
        watingForACK = True

    except Exception as e:
        print("\nSomething went wrong:\n" + str(e))
        ClientSocket.close()

    if DataPacket["flagType"] != "ACK":     
        print('Waiting for AKC packet............\n')

    if not connectionEstablished and retransmitionCount == 0:
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

    while True:
        try:
            dataPacket = ClientSocket.recvfrom(buffer_size)   
            s_data = (dataPacket[0]).decode('ascii')
            s_address = (dataPacket[1])

            data = json.loads(s_data)
            clientChecksum = checksum(data["message"])

            if data["flagType"] == "NAK":
                print("NAK packet recived, retransmitting..............\n")
                sendData(DataPacket["message"], DataPacket["checksum"], DataPacket["flagType"])

            elif clientChecksum == data["checksum"]:

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
                    connectionEstablished = True
                    print(data["message"])

                elif data["flagType"] == "REPLY":
                    print("Message from server")
                    message = data["message"]

                    if data["message"] == instructions[1]:
                        message += "Enter from the following sypmtoms: cough, sneeze, fever, headache, loss of smell, loss of taste"

                    print(message + "\n")
                    Intrcution = data["message"]

                    outT = threading.Thread(target=respond)
                    outT.start()
            else:
                sendData("Retransmit, data loss", checksum("Retransmit, data loss"), "NAK")    
                                    
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




