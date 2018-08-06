from flask import Flask, request, jsonify
import simplejson
from flask_restful import Resource, Api
import hashlib, binascii
import pickle
from datetime import datetime
from uuid1 import uuid1

class Block(object):
    def __init__(self, data, prev_hash, index=0):
        self.index = index
        self.data = data
        self.prev_hash = prev_hash
        self.nounce = 100
        self.hash = self.__hash__()

    # (self.index, self.timestamp, self.data, self.prev_hash, self.nounce)

    def set_hash(self):
        self.hash = self.__hash__()
        return self

    def validate(self):
        return self.hash == self.__hash__()

    def __hash__(self):
        hashId = hashlib.md5()
        hashId.update(pickle.dumps((self.index, self.data, self.prev_hash, self.nounce)))
        return int(hashId.hexdigest()[-2:],16)

    def _asdict(self):
        return self.__dict__

class Blockchain(object):
    def __init__(self):
        self.genesis_block = Block(data=[], prev_hash=None, index=0)
        self.genesis_block.set_hash()
        self.chain = [self.genesis_block]
        self.transactions = []

    def get_latest(self):
        return self.chain[-1]

    def add_block(self, new_block):
        print(self.get_latest().hash)
        print(new_block.prev_hash)
        if new_block.prev_hash == self.get_latest().hash and new_block.validate():
            self.chain.append(new_block)
        else:
            raise Exception("This hash is wrong!")

    def transactions_to_block(self):
        curr_block = Block(data = self.transactions,
                           prev_hash = self.get_latest().hash,
                           index = self.get_latest().index + 1)
        for i in range(1000):
            curr_block.hash = i
            if curr_block.validate():
                print(curr_block.hash)
                break
        self.add_block(curr_block)

    def validate(self):
        bools = [x.validate() for i,x in enumerate(self.chain)]
        return False not in bools

    def add_transaction(self, src, dst, amount):
        self.transactions.append({
            "From":src,
            "To":dst,
            "Amount":amount
        })


# x = Block(1, [1,2,3], None)
# chain = Blockchain()
# chain.add_block(x)
# chain.validate()

app = Flask(__name__)
api = Api(app)

node_identifier = str(uuid1()).replace("-","-")
blockchain = Blockchain()

class mine(Resource):
    def get(self):
        blockchain.transactions_to_block()
        return {'mined': 'new block'}

class new_transaction(Resource):
    def post(self):
        transaction_dict = request.get_json()
        blockchain.add_transaction(transaction_dict)
        return "Transaction added"

class chain(Resource):
    def get(self):
        response = {
            'chain': blockchain.chain,
            'length': len(blockchain.chain),
        }
        return simplejson.dumps(response), 200


api.add_resource(mine, '/mine')
api.add_resource(new_transaction, '/transactions/new')
api.add_resource(chain, '/chain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)