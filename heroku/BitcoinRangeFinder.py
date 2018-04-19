import json
import datetime
from datetime import datetime

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
			transtime = datetime.fromtimestamp(time)
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
				transtime = datetime.fromtimestamp(time)

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
				uniqueNodes.add(transaction['source'])
				uniqueNodes.add(transaction['target'])
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
			sourceID[node] = count
			count = count + 1

		return nodes

	def updateSource(self,transactionGraphOutput):
		for link in transactionGraphOutput['links']:
			link["source"] = sourceID[link["source"]]
			link["target"] = sourceID[link["target"]]
		return transactionGraphOutput

	def getMyData(self,addresses, start, end):
		firstDate = datetime.strptime(start, '%m/%d/%Y')#datetime(2016, 3, 4, 1, 1, 1) 2016-03-04
		lastDate = datetime.strptime(end, '%m/%d/%Y')#datetime(2018, 3, 5, 1, 1, 1) 2018-03-05

		transactionLinks = self.transactionGraph(addresses, firstDate, lastDate)
		transactionGraphOutput = {}

		transactionGraphOutput['nodes'] =  self.formatTransactionNodes(uniqueNodes)
		transactionGraphOutput['links'] = transactionLinks
		return self.updateSource(transactionGraphOutput)

btcFinder = BitcoinRangeFinder()
btcFinder.getMyData(['a'],'02/02/1997', ['02/02/2018'])