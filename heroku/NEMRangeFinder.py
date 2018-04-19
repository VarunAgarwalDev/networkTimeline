#TO USE: python NEMDateRange.py -i input.csv -o output.csv -s 01/30/2018 -e 02/02/2018
#to find open nodes: https://nodeexplorer.com/api_openapi_version

import urllib.request
import json
import datetime

class NEMRangeFinder:
	
	def __init__(self):
		self.baseUrl = "http://202.5.19.142:7890"#"http://66.228.48.37:7890/"#"
		self.nemBlockTimeStamp = datetime.datetime(2015, 3, 28, 16, 6, 25) #2015-03-28 16:06:25 - i think this is the nemisis block start time

	def prettyPrint(self, transaction, adjustedTime, address):
		address = address
		recipient = "N/A"
		amount = -1
		time = str(adjustedTime)
		messagePayload = "N/A"
		outgoing = 0
		incoming = 0
		signer = ""
		sender = ""
		machineTime = str(int(adjustedTime.strftime("%s")) * 1000)
		if 'recipient' in transaction:
			recipient = transaction['recipient']
			if recipient == address:
				incoming = 1
			else:
				outgoing = 1

		if 'amount' in transaction:
			amount = (transaction['amount'] / 1000000.0)

		if 'message' in transaction:
			message = transaction['message']
			if 'payload' in message:
				messagePayload = str(message['payload'])

		if 'signer' in transaction:
			signer = transaction['signer']
			sender = self.getSender(self.baseUrl, signer)


		return (address, sender, recipient, time, amount, outgoing, incoming, messagePayload, machineTime)


	def getTransactions(self, baseUrl, parameters, requestCount):
		request = "/account/transfers/all?"
		# print "...search number #" + str(requestCount) + " ..."
		transferResponse = urllib.request.urlopen(self.baseUrl + request + parameters)
		transferRaw = json.loads(transferResponse.read())
		return transferRaw

	def getSender(self, baseUrl, pubKey):
		request = "/account/get/from-public-key?publicKey="
		transferResponse = urllib.request.urlopen(self.baseUrl + request + pubKey)
		transferRaw = json.loads(transferResponse.read())
		return transferRaw["account"]["address"]

	def getHistory(self,parameters, startDate, endDate, address):
		transactionsRecord = []
		requestCount = 0
		forceQuit = False
		while True:
			if forceQuit:
				break
			requestCount = requestCount + 1
			transferRaw = self.getTransactions(self.baseUrl, parameters, requestCount)
			if len(transferRaw['data']) == 0:
				return transactionsRecord

			transferData = transferRaw['data']
			for transfer in transferData:
				transaction = transfer['transaction']
				timeStamp = transaction['timeStamp']
				adjustedTime = self.nemBlockTimeStamp + datetime.timedelta(seconds = timeStamp)

				if startDate <= adjustedTime <= endDate:	
					transactionsRecord.append(self.prettyPrint(transaction, adjustedTime, address))
				elif adjustedTime < startDate:
					forceQuit = True

			#keep searching after the end? the api only returns the last 25 transactions - this might work?
			lastTransfer = transferData[-1]
			lastTransferHash = lastTransfer['meta']['hash']['data']
			lastTransferId = lastTransfer['meta']['id']
			parameters = "address=" + address + "&hash=" + str(lastTransferHash) + "&id=" + str(lastTransferId)
		return transactionsRecord


	#{'sendingAddress': u'3HHvdMBiMDjDmLVTXXSnkTVhpGvK6f4HtC', 'target': 1, 'receivingAddress': u'3JFHRGhbfFXTnLWqz5PaGnEfcFSSxM3Nqr', 'value': 7974520, 'source': 0, 'id': u'02ce0752f4c7170eba73971d487a0be2438d716eea14c6e75b8b483070d7e82d'}
	def formatTransaction(self,uniqueWallets, transaction, transKey):
		trans = {}
		trans['sendingAddress'] = transaction[1]
		trans['source'] = uniqueWallets[transaction[2]]
		trans['receivingAddress'] = transaction[2]
		trans['target'] = uniqueWallets[transaction[2]]
		trans['value'] = transaction[4]
		trans['id'] = transKey
		return trans

	def formatNodes(self,uniqueWallets):
		nodes = []
		for key in uniqueWallets:
			node = {}
			node['address'] = key
			node['id'] = uniqueWallets[key]
			nodes.append(node)
		return nodes
	def getMyData(self,addressReader, start, end):
		duplicates = set()
		uniqueWallets = {}
		walletId = 0
		finalTransactions = []
		addressReader = ['NC4C6PSUW5CLTDT5SXAGJDQJGZNESKFK5MCN77OG']
		startDate = datetime.datetime.strptime(start, '%m/%d/%Y')
		endDate = datetime.datetime.strptime(end, '%m/%d/%Y')

		for address in addressReader:
			# print "Fetching " + address[0]
			
			#summary statistics
			numTransactions = 0
			firstDate = datetime.datetime(3000, 1,1, 1, 1, 1)
			lastDate = datetime.datetime(1900, 1, 1, 1, 1, 1)  
			totalAmount = 0
			outgoingAmount = 0
			incomingAmount = 0
			totalRecieved = 0
			totalSent = 0

			parameters = "address=" + address
			history = self.getHistory(parameters, startDate, endDate, address)
			for transaction in history:
				transKey = ""
				if transaction[1] > transaction[2]:
					transKey = transaction[1] + transaction[2] + transaction[3]
				else:
					transKey = transaction[2] + transaction[1] + transaction[3]

				if transKey not in duplicates:
					if transaction[1] not in uniqueWallets:
						uniqueWallets[transaction[1]] = walletId
						walletId = walletId + 1
					if transaction[2] not in uniqueWallets:
						uniqueWallets[transaction[2]] = walletId
						walletId = walletId + 1
					formattedTransaction = self.formatTransaction(uniqueWallets, transaction, transKey)
					finalTransactions.append(formattedTransaction)
					duplicates.add(transKey)
		nodes = self.formatNodes(uniqueWallets)
		answer = {}
		answer['nodes'] = nodes
		answer['links'] = finalTransactions
		return answer

# newFinder = NEMRangeFinder()
# answer = newFinder.getMyData(['NC4C6PSUW5CLTDT5SXAGJDQJGZNESKFK5MCN77OG','NCTWFIOOVITRZYSYIGQ3PEI3IMVB25KMED53EWFQ'],"01/30/2018","02/02/2018")
# print answer



