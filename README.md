# Computer Networking (COM2022) CW

This repository contains the files that I have tested with my team, and the extensions put into a separate folder 'Potential Extensions'

For running the files, please use:
```bash
python UDPServer.py
```
and
```bash
python UDPClient.py
```

## Set up for Client code for testing with other team memebers

First run the server, It will print It's IP address. This address needs to be put into the client code.\
Open UDPClient.py file, on line 16

```python
16 HOST_IP = socket.gethostbyname(hostName) #This should be the IP addres of the server
```

Change the 'HOST_IP' variable to the IP address printed by the server (after running the UDPserver.py)

## Set up for Potential Extensions

For this section I used an encryption library provided by Crypto.\
In order to run the code, please do:

```bash
pip install pycrypto
```
before running both the client and the server



