from flask import Flask
from flask import request
# from .NEMRangeFinder import NEMRangeFinder
# from .BitcoinRangeFinder import BitcoinRangeFinder

app = Flask(__name__)

import json
import urllib.request
import datetime
import sys
import csv
import argparse
# from datetime import datetime, timedelta



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


class BitcoinRangeFinder:
	def __init__(self):
		self.uniqueNodes = set()
		self.sourceID = dict()
	def getTransactionHistory(self,address, pageNum):
		request = "https://blockchain.info/rawaddr/"
		offsetRequest = "?offset=" + str(pageNum * 50)
		rawaddrResponse = urllib.request.urlopen(request + address + offsetRequest)
		rawaddr = json.loads(rawaddrResponse.read())
		return rawaddr


	def dateRangeBounds(self,rawaddr, startTime, endTime):
		rawtrans = rawaddr['txs']
		for trans in rawtrans:
			time = trans['time']
			transtime = datetime.datetime.fromtimestamp(time)
			if transtime < startTime:
				return True
		return False


	def getAllTransactions(self,address, startTime, endTime):
		allRawTrans = []
		pageNum = 0
		while 1:
			rawaddr = self.getTransactionHistory(address,pageNum)
			if rawaddr['txs']!=[]:
				if self.dateRangeBounds(rawaddr, startTime, endTime):
					return allRawTrans
				allRawTrans.append(rawaddr)
			else:
				return allRawTrans
			pageNum = pageNum + 1

	def processTransactions(self,allRawTrans, startTime, endTime):
		cleanedtrans = []
		for fullrawtrans in allRawTrans:
			rawtrans = fullrawtrans['txs']
			for trans in rawtrans:
				inputs = trans['inputs']
				senders = []
				inValues = []
				for sender in inputs:
					senders.append(sender['prev_out']['addr'])
					inValues.append(sender['prev_out']['value'])

				outputs = trans['out']
				recievers = []
				outValues = []
				for reciever in outputs:
					if 'addr' in reciever:
						recievers.append(reciever['addr'])
					outValues.append(reciever['value'])

				time = trans['time']
				transtime = datetime.datetime.fromtimestamp(time)

				txHash = trans['hash']
				if(startTime<=transtime<=endTime):
					transaction = {}
					transaction['source'] = senders[0]
					transaction['value'] = inValues[0]
					transaction['target'] = recievers[0]

					transaction['sendingAddress'] = senders[0]
					transaction['receivingAddress'] = recievers[0]

					transaction['id'] = txHash
					cleanedtrans.append(transaction)
		return cleanedtrans


	def transactionsByDate(self,address, firstDate, lastDate, uniqueTrasnactions):
		allRawTrans = self.getAllTransactions(address, firstDate, lastDate)
		cleanedTrans = self.processTransactions(allRawTrans, firstDate, lastDate)
		uniqueTrans = []
		for transaction in cleanedTrans:
			if transaction['id'] not in uniqueTrasnactions:
				uniqueTrasnactions.add(transaction['id'])
				uniqueTrans.append(transaction)
				self.uniqueNodes.add(transaction['source'])
				self.uniqueNodes.add(transaction['target'])
		return uniqueTrans

	def transactionGraph(self,addressList, firstDate, lastDate):
		graph = []
		uniqueTransactions = set()
		for address in addressList:
			graph.extend(self.transactionsByDate(address, firstDate, lastDate, uniqueTransactions))
		return graph

	def formatTransactionNodes(self,transactionNodes):
		nodes = []
		count = 0
		for node in transactionNodes:
			nodeDict = {}
			nodeDict['address'] = node
			nodeDict['id'] = count
			nodes.append(nodeDict)
			self.sourceID[node] = count
			count = count + 1

		return nodes

	def updateSource(self,transactionGraphOutput):
		for link in transactionGraphOutput['links']:
			link["source"] = self.sourceID[link["source"]]
			link["target"] = self.sourceID[link["target"]]
		return transactionGraphOutput

	def getMyData(self,addresses, start, end):
		firstDate = datetime.datetime.strptime(start, '%m/%d/%Y')#datetime(2016, 3, 4, 1, 1, 1) 2016-03-04
		lastDate =datetime.datetime.strptime(end, '%m/%d/%Y')#datetime(2018, 3, 5, 1, 1, 1) 2018-03-05

		transactionLinks = self.transactionGraph(addresses, firstDate, lastDate)
		transactionGraphOutput = {}

		transactionGraphOutput['nodes'] =  self.formatTransactionNodes(self.uniqueNodes)
		transactionGraphOutput['links'] = transactionLinks
		return self.updateSource(transactionGraphOutput)


@app.route('/btc', methods=['GET', 'POST'])
def btc():
	start = request.form['start']
	end = request.form['end']
	addresses = request.form.getlist('addresses')
	print(addresses)
	btcFinder = BitcoinRangeFinder()
	answer = btcFinder.getMyData(addresses,start,end)
	return json.dumps(answer)	

@app.route('/nem', methods=['GET', 'POST'])
def nem():
	start = request.form['start']
	end = request.form['end']
	addresses = request.form.getlist('addresses')
	print(addresses)
	nemFinder = NEMRangeFinder()
	answer = nemFinder.getMyData(addresses,start,end)
	return json.dumps(answer)	

if __name__ == "__main__":
	app.run()	