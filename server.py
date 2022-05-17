from socket import *
import csv
from datetime import datetime
Cache = {}
HITS = 0
WAS_A_HIT = False
MISSES = 0
TOTAL_BYTES = 0
HIT_BYTES  = 0
REQUESTS = 0

def getNames(str):
	if str =="":
	   return "", ""
	if str.find('/') == -1:
		return str, '/'
	else:
		return str[:str.find('/')], str[str.find('/'):]
def getNewHeader(str):
	temp = str.decode()
	temp = temp.split(' ')
	if len(temp) > 1:
		code = temp[1]
	else: return 'HTTP/1.1 400 NOT FOUND\r\nConnection: close\r\n\r\n'.encode()

	newHeader = ''
	if code == '200':
		newHeader = 'HTTP/1.1 200 OK\r\n';
		newHeader += 'Connection: close\r\n'
		newHeader += '\r\n'
	else:
		return str

	
	return newHeader.encode()

def getFromWeb(serverName, fileName):
	try:
		webIP = gethostbyname(serverName)
		clientSocket= socket(AF_INET, SOCK_STREAM)
		clientSocket.connect((webIP, 80))#default https 443 port
		clientSocket.send(('GET ' + fileName + ' HTTP/1.1\r\n').encode())
		clientSocket.send(('Host: ' + serverName + '\r\n\r\n').encode())
		data = b''
		clientSocket.settimeout(2)

	except: 
		return b'', b'HTTP/1.1 400 NOT FOUND\r\n\r\n'
	try:
		while True:
			blob = clientSocket.recv(2048)
			if not blob: break
			data += blob
			
	except timeout:
		
		if data.find('\r\n\r\n'.encode()) != -1:
			headerMessage = data[:data.find('\r\n\r\n'.encode()) + 4]
			newHeader = getNewHeader(headerMessage)
			data = data[data.find('\r\n\r\n'.encode()) + 4:]
			
		else:
			print('couldn\'t remove header')
		clientSocket.close()
		return data, newHeader

	if data.find('\r\n\r\n'.encode()) != -1:
		data = data[data.find('\r\n\r\n'.encode()) + 4:]
		headerMessage = data[:data.find('\r\n\r\n'.encode()) + 4]
		newHeader = getNewHeader(headerMessage)
	else:
		print('couldn\'t remove header')
	clientSocket.close()
	return data, newHeader
def getTable():
	table = '<table><tr><th>REQUESTS---</th><th>TOTAL BYTES---</th><th>HITS---</th><th>HIT BYTES</th></tr>'
	table += '<tr><td>'+ str(REQUESTS) + '</td>' + '<td>'+ str(TOTAL_BYTES) + '</td>' + '<td>'+ str(HITS) + '</td>' + '<td>'+ str(HIT_BYTES) + '</td></tr>'
	table += '</table>'
	return table
def GetFile(str):
	global HITS, MISSES, HIT_BYTES, WAS_A_HIT

	serverName, fileName = getNames(str)
	print('serverName: ' + serverName + '\n' + 'FileName: ' + fileName + '\n')
	if serverName in Cache:
		if fileName in Cache[serverName]:
			print('Cache HIT!')
			HITS +=1
			header = 'HTTP/1.1 200 OK\r\n'; 
			header +='Connection: close\r\n'
			header+= '\r\n'
			WAS_A_HIT = True
			HIT_BYTES += len(Cache[serverName][fileName]) + len(header)
			data = Cache[serverName][fileName]
			header = header.encode()
		else:
			print('Cache MISS!')
			++MISSES
			data, header = getFromWeb(serverName, fileName)
			if header != b'HTTP/1.1 400 NOT FOUND\r\n\r\n':
				Cache[serverName][fileName] = data
	else:
		print('Cache MISS!')
		++MISSES
		
		
		data, header = getFromWeb(serverName, fileName)
		if header.split(' '.encode())[1] ==b'200':
			Cache[serverName] = {}
			Cache[serverName][fileName]= data
	
	return data, header

#################################################
##########################################
#################################
serverPort   = 80
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(100)
file = open('./log.csv', 'w', encoding='UTF8', newline='')
writer = csv.writer(file)
writer.writerow(['REQUEST TIME', 'RESPONSE TIME', 'HIT?MISS', 'REQUEST'])
file.close()
while True:
	print('The server is read to recieve')
	row = ['', '', '', '']
	connectionSocket, addr = serverSocket.accept()
	with connectionSocket:
		
		request = connectionSocket.recv(2048)
		print(request.decode())
		row[0] = datetime.now().strftime("%H:%M:%S")
		request = request.decode()
		splitted = request.split(' ')
		if(splitted[0] == 'GET'):
			if splitted[1][1:] == 'proxy_usage?':
				data = getTable().encode()
				header = 'HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n'.encode()
			elif splitted[1][1:] == 'proxy_usage_reset?':
				HITS = 0
				REQUESTS = 0
				TOTAL_BYTES = 0
				HIT_BYTES = 0
				MISSES = 0
				data = getTable().encode()
				header = 'HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n'.encode()
			elif splitted[1][1:] == 'proxy_log?':
				file = open('./log.csv', 'r')
				reader = csv.reader(file)
				
				data = '<!DOCTYPE><html><head><title>log</title></head><body><table>'
				i = True
				for row in reader:
					data += '<tr>'
					for temp in row:
						data += '<th>' + temp + '</th>' if i == True else '<td>' + temp + '</td>'
					i = False
					data += '</tr>'
				data += '</table></body></html>'
				data = data.encode()
				header = 'HTTP/1.1 200 OK\r\nConnection: close\r\nContent-Type: text/html\r\ncharset=UFT-8\r\n\r\n '.encode()
			else:
				REQUESTS +=1
				data, header = GetFile(splitted[1][1:])
				TOTAL_BYTES += len(data) + len(header) #since every character is  8 bits (1 byte long)
			print('(REQUESTS: ' + str(REQUESTS) + ' | TOTAL BYTES: ' + str(TOTAL_BYTES) + ' | HITS: ' + str(HITS) + ' | HIT BYTES: ' + str(HIT_BYTES))
			connectionSocket.send(header)
			connectionSocket.send(data)
			file = open('./log.csv', 'a', encoding='UTF8', newline='')
			writer = csv.writer(file)
			row[2] = 'HIT' if WAS_A_HIT else 'MISS'
			row[3] = request.split('\n')[0]
			row[1] = datetime.now().strftime("%H:%M:%S")
			writer.writerow(row)
			file.close()
	print('\n-----------------------------\n')
	connectionSocket.close()
	WAS_A_HIT = False

