# Yet-Another-POC-Blockchain

This is a toy blockchain implementation written in Python partially based off https://hackernoon.com/learn-blockchains-by-building-one-117428612f46.

# Running it
````
git clone https://github.com/yarnspinnered/Yet-Another-POC-Blockchain.git

python3 -m venv venv

source venv/bin/activate

pip install -r requirements

python3 blockchain.py 5000

python3 blockchain.py 5001
````
# How blockchain works
A blockchain is essentially a distributed database.
To be specific, it is a linked list of blocks.
Lastly, the blockchain has a target difficulty, which is the range of hashes it accepts.
The smaller the target, the more difficult it is to adjust the block such that it results with an acceptable hash.

Each block has an index, previous block's hash, it's own hash, a set of transactions and a nonce.
As mentioned earlier, the blockchain only accepts blocks which hash to a sufficiently small value (i.e. below the target).
However, to do that, one must be able to change a value in the block in order to attempt getting different hashes.
This value that is varied is called the nonce. 

In this example, the SHA256 hash is used and we set an exceptionally easy target of accepting ~1% of the possible hash outcomes.

# How this specific implementation of blockchain works
We represent blocks with the Block class. 
Each block has an index, previous block's hash, it's own hash, a set of transactions and a nonce.
There are two cases where we need to create blocks. One is when we mine a block and thus create the block within our own node. 
In this case, we create Blocks with just the data and prev_hash then try different nonces till we find a hash that meets the target difficulty.
The second case is when we receive a list of transactions from another node, then we convert them from a JSON object to a dict and finally a block.
In the second case, the hash and nonce already exists, so we just create the block without computing the nonce and hash.

We represent the blockchain with a Blockchain object. It of course contains the list of Blocks as mentioned earlier.
It also contains additional information such as the set of nodes it knows about so it can query them periodically to keep in sync.
For this toy blockchain, it also maintains a set of transactions it wishes to add to the next block.
When the blockchain decides to add transactions to the next block, it creates a new block , computes the nonce and then adds it to the chain.
Every 7 seconds, the blockchain checks the neighboring nodes it knows about and compares blockchain lengths.
If a neighbor has a longer blockchain, it first verifies the blockchain by computing all the hashes.
If it is valid, it then replaces it's own chain with it's neighbor's chain.

Lastly, communication is implemented via HTTP messages. 
In order to get the blockchain to mine, we send a GET request to the "/mine" endpoint.
To get the current chain, either as a user or another blockchain node, a GET request is sent to the "/chain" endpoint.
To add transactions to the set of transactions the blockchain will be adding next, a POST request is sent to the "/transactions/new" endpoint.
To register other nodes in the network, a POST request with the host of the registrant node is sent to the node that doesn't know about it yet.

# Log of it in action

After POSTing a transaction from fooman to barman and mining one block at the node using port 5000.

````
127.0.0.1 - - [07/Aug/2018 21:42:45] "POST /transactions/new HTTP/1.1" 200 -
We used  52  attempts before succeeding in setting the nonce.
We used  52  attempts before succeeding in setting the nonce.
127.0.0.1 - - [07/Aug/2018 21:42:46] "GET /mine HTTP/1.1" 200 -
127.0.0.1 - - [07/Aug/2018 21:42:46] "GET /chain HTTP/1.1" 200 -
Consensus begins! Attempting to connect to:  []
Current chain
[OrderedDict([('prev_hash', None), ('nonce', 53), ('index', 0), ('hash', 1020927793593912140819426550356994498379306788437712821133320908185758475865), ('data', [])]),
 OrderedDict([('prev_hash', 1020927793593912140819426550356994498379306788437712821133320908185758475865), ('nonce', 52), ('index', 1), ('hash', 825007783000051959672595478140960382480379273434266641137213138993897408836), ('data', [transaction(From='fooman', To='barman', Amount=123), transaction(From='0', To='00367c75-acda-2c61-9183-379f50ca802b', Amount=1)])])]
Consensus ends!

````
The second node at port 5001 which only has a genesis block but registers the first node at 5001 going through the consensus protocol.

````
127.0.0.1 - - [07/Aug/2018 21:42:21] "POST /register HTTP/1.1" 200 -
Consensus begins! Attempting to connect to:  ['127.0.0.1:5000']
Current chain
[OrderedDict([('prev_hash', None), ('nonce', 53), ('index', 0), ('hash', 1020927793593912140819426550356994498379306788437712821133320908185758475865), ('data', [])])]
Switching to chain from  127.0.0.1:5000
This is the new chain!
[OrderedDict([('prev_hash', None), ('nonce', 53), ('index', 0), ('hash', 1020927793593912140819426550356994498379306788437712821133320908185758475865), ('data', [])]),
 OrderedDict([('prev_hash', 1020927793593912140819426550356994498379306788437712821133320908185758475865), ('nonce', 52), ('index', 1), ('hash', 825007783000051959672595478140960382480379273434266641137213138993897408836), ('data', [transaction(From='fooman', To='barman', Amount=123), transaction(From='0', To='00367c75-acda-2c61-9183-379f50ca802b', Amount=1)])])]
Consensus ends!
````