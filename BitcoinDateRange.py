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
firstDate = datetime(2016, 3, 4, 1, 1, 1)
lastDate = datetime(2018, 3, 5, 1, 1, 1)
transactionLinks = transactionGraph(addresses, firstDate, lastDate)
transactionGraph = {}

transactionGraph['nodes'] =  formatTransactionNodes(uniqueNodes)
transactionGraph['links'] = transactionLinks
updateSource()

with open('data/set.json', 'w') as outfile:
    json_str = json.dumps(transactionGraph, outfile)
    outfile.write(json_str)


########################################################################################################################
# This class contains methods to handle our requests to different URIs in the app
class MyHandler(SimpleHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    # Check the URI of the request to serve the proper content.
    def do_GET(self):
        if "URLToTriggerGetRequestHandler" in self.path:
        	# If URI contains URLToTriggerGetRequestHandler, execute the python script that corresponds to it and get that data
            # whatever we send to "respond" as an argument will be sent back to client
            #content = pythonScriptMethod()
			content = [3,4,5,6]
			print(content)
            self.respond(content) # we can retrieve response within this scope and then pass info to self.respond
        else:
            super(MyHandler, self).do_GET() #serves the static src file by default

    def handle_http(self, data):
        self.send_response(200)
        # set the data type for the response header. In this case it will be json.
        # setting these headers is important for the browser to know what 	to do with
        # the response. Browsers can be very picky this way.
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        return bytes(data, 'UTF-8')

     # store response for delivery back to client. This is good to do so
     # the user has a way of knowing what the server's response was.
    def respond(self, data):
        response = self.handle_http(data)
        self.wfile.write(response)

# This is the main method that will fire off the server.
if __name__ == '__main__':
    server_class = HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print(time.asctime(), 'Server Starts - %s:%s' % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), 'Server Stops - %s:%s' % (HOST_NAME, PORT_NUMBER))
