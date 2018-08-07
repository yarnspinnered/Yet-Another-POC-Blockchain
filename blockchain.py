# Hosting stuff
from flask import Flask, request
from flask_restful import Resource, Api
# Serializing our objects then hashing them
import hashlib
import pickle
from collections import namedtuple
#Mainly for pretty printing
from collections import OrderedDict
import operator
import pprint
# Generate a uuid
from uuid1 import uuid1
# Making http requests and parsing
import requests
import simplejson
# Getting port number from commandline
import sys
# Scheduling consensus to run every 10 seconds
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

transaction = namedtuple('transaction',['From','To','Amount'])
CONSENSUS_FREQ_IN_SECONDS = 30
HASH_DIFFICULTY = (2**256)/100

class Block(object):
    def __init__(self, data, prev_hash, index=0, hash=None, nonce=None):
        self.index = index
        self.data = data
        self.prev_hash = prev_hash
        if nonce == None:
            self.nonce = self.set_nonce()
        else:
            self.nonce = nonce
        if hash == None:
            self.hash = self.__hash__()
        else:
            self.hash = hash

    def set_hash(self):
        self.hash = self.__hash__()
        return self

    def validate(self):
        return self.hash == self.__hash__() and self.hash < HASH_DIFFICULTY

    def set_nonce(self):
        for i in range(2**256):
            self.nonce = i
            self.set_hash()
            if self.validate():
                print("We used ",i, " attempts before succeeding in setting the nonce.")
                break

    def __hash__(self):
        hashId = hashlib.sha256()
        hashId.update(pickle.dumps((self.index, self.data, self.prev_hash, self.nonce)))
        return int(hashId.hexdigest(),16)

    def __repr__(self):
        return str(OrderedDict(sorted(self.__dict__.items(), key=operator.itemgetter(0), reverse=True)))

    def _asdict(self):
        return self.__dict__

class Blockchain(object):
    def __init__(self):
        self.genesis_block = Block(data=[], prev_hash=None, index=0)
        self.genesis_block.set_hash()
        self.genesis_block.set_nonce()
        self.chain = [self.genesis_block]
        self.transactions = []
        self.nodes = set()

    def get_latest(self):
        return self.chain[-1]

    def add_block(self, new_block):
        if new_block.prev_hash == self.get_latest().hash and new_block.validate():
            self.chain.append(new_block)
        else:
            raise Exception("This hash is wrong!")

    def transactions_to_block(self):
        curr_block = Block(data = self.transactions[:],
                           prev_hash = self.get_latest().hash,
                           index = self.get_latest().index + 1)
        curr_block.set_nonce()
        self.transactions = []
        self.add_block(curr_block)

    def validate(self):
        bools = [x.validate() for i,x in enumerate(self.chain)]
        return False not in bools

    @staticmethod
    def validate_list_of_blocks(list_of_blocks_in_dict_form):
        chain = []
        for block_dict in list_of_blocks_in_dict_form:
            txn_list = []
            for txn in block_dict["data"]:
                txn_list.append(transaction(From=txn["From"],To=txn["To"],Amount=txn["Amount"]))
            chain.append(
                Block(
                  index=block_dict["index"],
                  data=txn_list,
                  prev_hash=block_dict["prev_hash"],
                  nonce=int(block_dict["nonce"]),
                  hash=block_dict["hash"]
                  )
            )
        bools = [x.validate() for x in chain]
        return chain, False not in bools

    def add_transaction(self, src, dst, amount):
        self.transactions.append(transaction(From=src,To=dst,Amount=amount))
        return self.transactions

    def register(self, node_name):
        self.nodes.add(node_name)

    def consensus(self):
        print("Consensus begins! Attempting to connect to: ", list(self.nodes))
        print("Current chain")
        pprint.pprint(self.chain)
        longest_known_length = len(self.chain)
        replacement_chain = None
        replacement_node = None
        for nbr in self.nodes:
            try:
                r = requests.get("http://" + nbr + "/chain")
                nbr_chain_in_dict_form = simplejson.loads(r.json())["chain"]
                list_of_blocks, valid = Blockchain.validate_list_of_blocks(nbr_chain_in_dict_form)
                if valid and len(list_of_blocks) > longest_known_length:
                    replacement_node = nbr
                    longest_known_length = len(list_of_blocks)
                    replacement_chain = list_of_blocks
            except requests.exceptions.ConnectionError:
                print("Failed connecting to", nbr)
                pass
        if longest_known_length > len(self.chain):
            print("Switching to chain from ", replacement_node)
            print("This is the new chain!")
            pprint.pprint(replacement_chain)
            self.chain = replacement_chain
        print("Consensus ends!")

node_identifier = str(uuid1()).replace("-","-")
blockchain = Blockchain()

class mine(Resource):
    def get(self):
        blockchain.add_transaction("0",node_identifier,1)
        blockchain.transactions_to_block()
        return simplejson.dumps({"Block added": blockchain.get_latest()})

class new_transaction(Resource):
    def post(self):
        transaction_dict = request.get_json()
        curr_transactions = blockchain.add_transaction(transaction_dict["From"], transaction_dict["To"], transaction_dict["Amount"])
        return simplejson.dumps({"Current transactions: ": tuple(curr_transactions)})

class chain(Resource):
    def get(self):
        response = {
            'chain': blockchain.chain,
            'length': len(blockchain.chain),
        }
        return simplejson.dumps(response), 200

class register(Resource):
    def post(self):
        registration_dict = request.get_json()
        blockchain.register(registration_dict["node_host"])
        return registration_dict["node_host"]

def main():
    print(sys.argv)
    if len(sys.argv) < 2 or type(int(sys.argv[1])) != type(int(0)):
        print("Please enter exactly one port number!")
        return
    chosen_port = int(sys.argv[1])
    app = Flask(__name__)
    api = Api(app)
    api.add_resource(mine, '/mine')
    api.add_resource(new_transaction, '/transactions/new')
    api.add_resource(chain, '/chain')
    api.add_resource(register, '/register')
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(
        func=blockchain.consensus,
        trigger=IntervalTrigger(seconds=CONSENSUS_FREQ_IN_SECONDS),
        id='Achieving consensus with known nodes',
        name='Consensusing',
        replace_existing=True)
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    app.run(host='localhost', port=chosen_port)

if __name__ == '__main__':
    main()
