from pymongo import MongoClient
import hashlib
import time


class Transaction:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount

    def __str__(self):
        return f"Transaction from {self.sender} to {self.receiver} for {self.amount}"

    def to_dict(self):
        return {"sender": self.sender, "receiver": self.receiver, "amount": self.amount}


class Block:
    def __init__(self, index, previous_hash, data, timestamp=None, nonce=0, hash_val=None):
        self.index = index
        self.previous_hash = previous_hash
        self.data = data  # List of transactions
        self.timestamp = timestamp or time.time()
        self.nonce = nonce
        self.hash = hash_val or self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}{self.previous_hash}{self.data}{self.timestamp}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()


class Blockchain:    
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["blockchainDB"]
        self.blocks_collection = self.db["blocks"]
        self.transactions_collection = self.db["transactions"]
        self.difficulty = 4  # Proof-of-Work difficulty

        # Create the genesis block if blockchain is empty
        if self.blocks_collection.count_documents({}) == 0:
            self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, "0", "Genesis Block")
        self.save_block_to_db(genesis_block)

    def get_latest_block(self):
        latest_block = self.blocks_collection.find_one(sort=[("index", -1)])
        if latest_block:
            return Block(
                latest_block["index"],
                latest_block["previous_hash"],
                latest_block["data"],
                latest_block["timestamp"],
                latest_block["nonce"],
                latest_block["hash"]
            )
        return None

    def add_block(self, new_block):
        latest_block = self.get_latest_block()
        if latest_block:
            new_block.previous_hash = latest_block.hash
        new_block.mine_block(self.difficulty)
        self.save_block_to_db(new_block)

    def save_block_to_db(self, block):
        block_data = {
            "index": block.index,
            "previous_hash": block.previous_hash,
            "data": block.data,
            "timestamp": block.timestamp,
            "nonce": block.nonce,
            "hash": block.hash
        }
        self.blocks_collection.insert_one(block_data)

    def add_transaction(self, transaction):
        self.transactions_collection.insert_one(transaction.to_dict())

    def get_pending_transactions(self):
        return list(self.transactions_collection.find({}, {"_id": 0}))

    def mine_pending_transactions(self):
        pending_transactions = self.get_pending_transactions()
        if not pending_transactions:
            return "No transactions to mine"

        new_block = Block(
            self.blocks_collection.count_documents({}),
            self.get_latest_block().hash,
            pending_transactions
        )
        self.add_block(new_block)

        # Clear mined transactions
        self.transactions_collection.delete_many({})
        return f"Block {new_block.index} mined successfully!"

    def is_chain_valid(self):
        blocks = list(self.blocks_collection.find().sort("index", 1))
        
        for i in range(1, len(blocks)):
            current_block = Block(
                blocks[i]["index"],
                blocks[i]["previous_hash"],
                blocks[i]["data"],
                blocks[i]["timestamp"],
                blocks[i]["nonce"],
                blocks[i]["hash"]
            )

            previous_block = Block(
                blocks[i - 1]["index"],
                blocks[i - 1]["previous_hash"],
                blocks[i - 1]["data"],
                blocks[i - 1]["timestamp"],
                blocks[i - 1]["nonce"],
                blocks[i - 1]["hash"]
            )

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True


blockchain = Blockchain()


transaction1 = Transaction("Jack", "Bob", 50)
transaction2 = Transaction("Charlie", "Jack", 30)


blockchain.add_transaction(transaction1)
blockchain.add_transaction(transaction2)


print("Mining block 1...")
print(blockchain.mine_pending_transactions())

print("Mining block 2...")
print(blockchain.mine_pending_transactions())


print("Is blockchain valid?", blockchain.is_chain_valid())


for block in blockchain.blocks_collection.find().sort("index", 1):
    print(f"Index: {block['index']}, Hash: {block['hash']}, Data: {block['data']}, Previous Hash: {block['previous_hash']}")
