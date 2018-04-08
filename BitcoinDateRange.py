import urllib, json
import datetime
import sys
import csv
import argparse
from datetime import datetime


uniqueNodes = set()
sourceID = dict()

def getInputAddresses(inputFile):
	inputFile="input.csv"
	inputAddresses=[]

	with open(inputFile, 'rb') as infile:
		addressReader = csv.reader(infile)
		for fileAddress in addressReader:
			inputAddresses.append(fileAddress[0])
	return inputAddresses


def getTransactionHistory(address, pageNum):
	request = "https://blockchain.info/rawaddr/"
	offsetRequest = "?offset=" + str(pageNum * 50)
	rawaddrResponse = urllib.urlopen(request + address + offsetRequest)
	rawaddr = json.loads(rawaddrResponse.read())
	return rawaddr


def dateRangeBounds(rawaddr, startTime, endTime):
	rawtrans = rawaddr['txs']
	for trans in rawtrans:
		time = trans['time']
		transtime = datetime.fromtimestamp(time)
		if transtime < startTime:
			return True
	return False


def getAllTransactions(address, startTime, endTime):
	allRawTrans = []
	pageNum = 0
	while 1:
		rawaddr = getTransactionHistory(address,pageNum)
		if rawaddr['txs']!=[]:
			if dateRangeBounds(rawaddr, startTime, endTime):
				return allRawTrans
			allRawTrans.append(rawaddr)
		else:
			return allRawTrans
		pageNum = pageNum + 1
		# print("Searching Page #" + str(pageNum))

def processTransactions(allRawTrans, startTime, endTime):
	#rawtrans = allRawTrans[0]['txs']
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


def transactionsByDate(address, firstDate, lastDate, uniqueTrasnactions):
	allRawTrans = getAllTransactions(address, firstDate, lastDate)
	cleanedTrans = processTransactions(allRawTrans, firstDate, lastDate)
	uniqueTrans = []
	for transaction in cleanedTrans:
		if transaction['id'] not in uniqueTrasnactions:
			uniqueTrasnactions.add(transaction['id'])
			uniqueTrans.append(transaction)
			uniqueNodes.add(transaction['source'])
			uniqueNodes.add(transaction['target'])
	# print "Found: " + str(len(uniqueTrans))
	return uniqueTrans

def transactionGraph(addressList, firstDate, lastDate):
	graph = []
	uniqueTransactions = set()
	for address in addressList:
		graph.extend(transactionsByDate(address, firstDate, lastDate, uniqueTransactions))
	return graph

def formatTransactionNodes(transactionNodes):
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

def updateSource():
	for link in transactionGraph['links']:
		link["source"] = sourceID[link["source"]]
		link["target"] = sourceID[link["target"]]

# def init(addresses = ["1BoatSLRHtKNngkdXEeobR76b53LETtpyT"], firstDate = datetime(2017, 3, 4, 1, 1, 1)
# ,lastDate = datetime(2017, 3, 5, 1, 1, 1)):
addresses = ["3HHvdMBiMDjDmLVTXXSnkTVhpGvK6f4HtC"]
firstDate = datetime(2017, 3, 4, 1, 1, 1)
lastDate = datetime(2016, 3, 5, 1, 1, 1)
transactionLinks = transactionGraph(addresses, firstDate, lastDate)
transactionGraph = {}

transactionGraph['nodes'] =  formatTransactionNodes(uniqueNodes)
transactionGraph['links'] = transactionLinks
updateSource()
print json.dumps(transactionGraph)
