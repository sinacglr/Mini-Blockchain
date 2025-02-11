from flask import Flask, jsonify, request
from blockchain import Blockchain, Block, Transaction

app = Flask(__name__)
blockchain = Blockchain()

@app.route("/chain", methods=['GET'])
def get_chain():
    chain_data = list(blockchain.blocks_collection.find({}, {"_id": 0}).sort("index", 1))

    response = {
        'chain': chain_data,
        'length': len(chain_data),
        'is_valid': blockchain.is_chain_valid()
    }
    return jsonify(response), 200


@app.route('/mine', methods=['POST'])
def mine_block():
    pending_transactions = list(blockchain.transactions_collection.find({}, {"_id": 0}))

    if not pending_transactions:
        return jsonify({'message': 'No transactions exist to mine'}), 400

    new_block = Block(
        blockchain.blocks_collection.count_documents({}),
        blockchain.get_latest_block().hash,
        pending_transactions
    )
    blockchain.add_block(new_block)

    blockchain.transactions_collection.delete_many({})

    response = {
        'message': 'New block mined',
        'block': {
            'index': new_block.index,
            'previous_hash': new_block.previous_hash,
            'timestamp': new_block.timestamp,
            'data': new_block.data,
            'hash': new_block.hash
        }
    }
    return jsonify(response), 201


@app.route('/transaction', methods=['POST'])
def add_transaction():
    data = request.get_json()

    if not data or 'sender' not in data or 'receiver' not in data or 'amount' not in data:
        return jsonify({'message': 'Invalid transaction data'}), 400

    existing_tx = blockchain.transactions_collection.find_one(data)
    if existing_tx:
        return jsonify({'message': 'Transaction already exists in mempool'}), 400

    transaction = Transaction(data['sender'], data['receiver'], data['amount'])
    blockchain.transactions_collection.insert_one(transaction.to_dict())

    response = {
        'message': 'Transaction added successfully',
        'transaction': transaction.to_dict()
    }
    return jsonify(response), 201

@app.route('/validate', methods=['GET'])
def validate_chain():
    is_valid = blockchain.is_chain_valid()
    response = {
        'message': 'Blockchain is valid' if is_valid else 'Blockchain is NOT valid!',
        'status': is_valid
    }
    return jsonify(response), 200


@app.route('/pending_transactions', methods=['GET'])
def get_pending_transactions():
    pending_transactions = list(blockchain.transactions_collection.find({}, {"_id": 0}))

    response = {
        'pending_transactions': pending_transactions,
        'count': len(pending_transactions)
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(debug=True)
