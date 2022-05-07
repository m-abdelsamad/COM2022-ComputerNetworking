import random
from socket import *
import threading
import json
import cryptography
# from rsa import *
# import rsa as rsa
from itertools import islice
import base64
# from Crypto.PublicKey import RSA
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

#Cryptodome

####################################################
#Simple Class for creating client object
class ClientObject:
	def __init__(self, name, tuple_address, pub_key):
		self.name = name
		self.tuple_address = tuple_address
		self.pub_key = pub_key
		self.recivedACK = True
		self.currentInstruction = None
		self.currentPacket = None
####################################################


serverSocket = socket(AF_INET, SOCK_DGRAM)
portNumber = 2500
hostName = gethostname()
HOST_IP = gethostbyname(hostName)
serverSocket.bind((HOST_IP, portNumber))

bufferSize = 1024
retransmitionCount = 0

clientsCount = 0
clients = []
CLIENT_CONNECTION_LIMIT = 3

mild_symptoms = [
	"cough",
	"sneeze",
	"fever",
	"headache"
]
severe_symptoms = [
	"loss of smell",
	"loss of taste",
]

instructions = ["Instructions:\nPress 1 to send any symptoms you are experiencing\nPress 0 to leave the server\n", "How are you feeling today?\nEnter symptoms seperated by comma and space\n"]

myPrivate = RSA.generate(128 * 8)
myPublic = myPrivate.publickey()

#FOMAT FOR SENDING DATA JSON OBJECT
#
# data = {
# 		"message": message,
# 		"flagType": "BROADCAST",
# 	}
#
# Flag Types
# BROADCAST, ESTAB, ACK, NAK, REPLY


####################################################
def symptomTestResult(msg):
	array = msg.split(", ")

	mildCount = 0
	severeCount = 0

	for i in range(0, len(mild_symptoms)):
		for j in range(0, len(array)):
			if array[j].lower() == mild_symptoms[i].lower():
				mildCount = mildCount+1

	for i in range(0, len(severe_symptoms)):
		for j in range(0, len(array)):
			if array[j].lower() == severe_symptoms[i].lower():
				severeCount = severeCount+1

	response = ""
	if severeCount > 0:
		response = "severe symptoms"
	elif severeCount == 0 and mildCount >= 0 and mildCount <= 2:
		response = "no symptoms"
	elif severeCount == 0 and mildCount >= 3:
		response = "mild symptoms"
	
	return response
####################################################



####################################################
def getClientObject(c_address):
	client = None
	for client in clients:
		if c_address == client.tuple_address:
			client = client
			break
	return client
####################################################



####################################################
def printConnectedClients():
	for client in clients:
		print("client: " + client.name + "\n")
####################################################



####################################################
def sendData(message, tuple_address):
	
	client = getClientObject(tuple_address)
	if client is not None:
		
		n = 117 # chunk length
		chunks = [message[i:i+n] for i in range(0, len(message), n)]
		key = PKCS1_OAEP.new(client.pub_key)

		print(len(chunks))
		print(chunks)
		encrypted_data = b''
		for chunk in chunks:
			encrypted_data += key.encrypt(chunk)
		
			while len(encrypted_data) < 117:
				encrypted_data += "\x00" + encrypted_data

		if len(bytes) < 127:
			encrypted_data = "\x00" + encrypted_data
	
		serverSocket.sendto(encrypted_data, tuple_address)
	else:
		message = message.encode('ascii')
		serverSocket.sendto(message, tuple_address)
####################################################



####################################################
def checksum(msg):
    s = 0
    for i in range(0, len(msg)):
        s += ord(msg[i])
    return s
#####################################################



###################################################
def broadcast(message):	
	global watingForACK

	data = {
		"message": message,
		"flagType": "BROADCAST",
	}
	data = json.dumps(data)

	for client in clients:
		client.recivedACK = False
		sendData(data, client.tuple_address)
####################################################
	


####################################################
def sendInstructions(c_address):
	
	client = getClientObject(c_address)
	message = "Instructions:\nPress 1 to send any symptoms you are experiencing\nPress 0 to leave the server\n"
	client.currentInstruction = message
	data = {
		"message": message,
		"flagType": "REPLY",
	}
	data = json.dumps(data)
	client.currentPacket = data

	sendData(data, c_address)
####################################################



####################################################
def handleClientSymptoms(response, c_address):
	symptomsResult = symptomTestResult(response)
	client = getClientObject(c_address)
	message = client.name + " has " + symptomsResult
	broadcast(message)

	sendInstructions(c_address)
####################################################



####################################################
def establishCon(c_address, c_name, pub_key):
	global clientsCount
	
	if clientsCount <= CLIENT_CONNECTION_LIMIT:

		establishmentPacket = {
			"message": "Connetion Established with server",
			"flagType": "ESTAB",
			"public_key": myPublic.exportKey().decode()
		}
		establishmentPacket = json.dumps(establishmentPacket)
		sendData(establishmentPacket, c_address)

		pub_key = RSA.import_key(pub_key.encode())
		client = ClientObject(c_name, c_address, pub_key)
		clientsCount+=1

		message = "Client " + c_name + " has joined the server"
		broadcast(message)

		clients.append(client)
		print(message)

		sendInstructions(c_address)
		
	else:
		message = "Denial of Service, Server connection reached its capcity"
		dataToSend = {
			"message": message,
			"flagType": "QUIT",
		}	
		dataToSend = json.dumps(dataToSend)
		sendData(dataToSend, c_address)
####################################################



####################################################
def sendACK(c_address):
	message = "Data Pakcet recived, sending ACK back"
	ACKmsg = {
		"message": message,
		"flagType": "ACK"
	}
	ACKmsg = json.dumps(ACKmsg)
	sendData(ACKmsg, c_address)
####################################################



####################################################
def disconnectClient(c_address):
	global clientsCount
	#send ACK for quiting the server (QUIT ACK)
	client = getClientObject(c_address)
	message = "You have left the server"
	dataToSend = {
		"message": message,
		"flagType": "QUIT",
	}	
	dataToSend = json.dumps(dataToSend)
	sendData(dataToSend, c_address)

	clientsCount-=1	
	message = "Client " + str(client.name) + " has left the server\n" + str(clientsCount) + " clients connected to server."
	print(message)
	clients.remove(client)
	
	broadcast(message)
####################################################



####################################################
def getNonrespondingClient():
	x = None
	for client in clients:
		if not client.recivedACK:
			x = client
			break
	return x
####################################################



####################################################
def getCurrentPacket(c_address):
	client = getClientObject(c_address)
	packet = None

	if client is None:
		packet = {
			"message": "Connected",
			"flagType": "ESTAB",
		}
		packet = json.dumps(packet)
	else:
		packet = client.currentPacket
	
	return packet
####################################################



####################################################
def recData():
	global clientsCount
	global watingForACK
	global retransmitionCount

	while True:

		dataPacket = serverSocket.recvfrom(bufferSize)
		c_data = (dataPacket[0])
		c_address = dataPacket[1]

		client = getClientObject(c_address)

		if client is not None:
			cipher = PKCS1_OAEP.new(myPrivate)
			c_data = cipher.decrypt(c_data)
		else:
			c_data = c_data.decode('ascii')

		data = json.loads(c_data)			
		
		if data["flagType"] == "NAK": 
			packet = getCurrentPacket(c_address)
			sendData(packet, c_address)
		
		
		#First Time Conneting		
		if data["flagType"] == "ESTAB":
			sendACK(c_address)
			#Client just connected to server
			establishCon(c_address, data["message"], data["public_key"])

		elif data["flagType"] == "REPLY":
			sendACK(c_address)
			
			instruction = client.currentInstruction

			if instruction == instructions[0]:
				if data["message"] != "1":
					message = "Please enter either 1 or 0 to proceed, try again...\n" + instructions[0]
					dataToSend = {
						"message": message,
						"flagType": "REPLY",
					}
					dataToSend = json.dumps(dataToSend)
					sendData(dataToSend, c_address)
				else:
					#send question 'How are you feeling'
					message = "How are you feeling today?\nEnter symptoms seperated by comma and space\n"
					client.currentInstruction = message
					dataToSend = {
						"message": message,
						"flagType": "REPLY",
					}	
					dataToSend = json.dumps(dataToSend)
					client.currentPacket = dataToSend
					sendData(dataToSend, c_address)

			elif instruction == instructions[1]: 
				if (data["message"]).isnumeric():	
					message = "Numbers are not allowed for this instruction, try again...\n" + instructions[1]
					dataToSend = {
						"message": message,
						"flagType": "REPLY",
					}
					dataToSend = json.dumps(dataToSend)
					sendData(dataToSend, c_address)
				else:
					#Then it is the response to a question sent before
					handleClientSymptoms(data["message"], c_address)
			
		#Client wants to quit
		elif data["message"] == "0" and data["flagType"] == "QUIT":
			sendACK(c_address)
			#client wants to exit the server
			disconnectClient(c_address)

		#Client confirmed that BROADCAST has been recived by server
		elif data["flagType"] == "ACK":
			retransmitionCount = 0
			getClientObject(c_address).recivedACK = True
			recData()
####################################################



####################################################
#Starting server
print('Server Listening...')
print("Server IP: " + HOST_IP + "\n")
print(str(myPublic.n))
#Using threading to support mnultiple client connections
inT = threading.Thread(target=recData)
inT.start()
####################################################