"""
Blockchain application developed by Sergio Jiménez Romero and David Tarrasa Puebla
"""

import BlockChain
from uuid import uuid4
import json
from flask import Flask, jsonify, request
from argparse import ArgumentParser
import requests
import time
from threading import Thread
import platform
from multiprocessing import Semaphore

# Node instance
app = Flask(__name__)
# Application instantiation
blockchain = BlockChain.Blockchain()
blockchain_backup = blockchain
mutex = Semaphore(1)
# To know my IP
my_ip = "localhost"  # node address on windows
network_nodes = set()


def backup_copy():
    """
    Function executed by a thread that creates a backup copy of the blockchain every
    60 seconds and saves it in a json. It has a mutual exclusion semaphore to prevent
    the blockchain from being modified during the backup copy
    """
    global blockchain_backup
    while True:
        time.sleep(60)
        mutex.acquire()
        t = time.localtime()
        blockchain_backup = {
            # We only allow the chain of those final blocks that have a hash
            "chain": [b.toDict() for b in blockchain.blocks if b.hash is not None],
            "length": len(blockchain.blocks),
            "date": time.strftime("%d/%m/%Y %H:%M:%S", t),
        }
        with open(f"backup-node{my_ip}-{port}.json", "w") as file:
            json.dump(blockchain_backup, file)
        mutex.release()
        print("backup copy", blockchain_backup)


@app.route("/transactions/new", methods=["POST"])
def new_transaction():
    """
    This function allows us to add a new transaction, which will go to the list of unconfirmed
    transactions of the blockchain

    Returns:
        json, int: message and response code
    """
    values = request.get_json()
    # We check that all transaction data is present
    required = ["origin", "destination", "amount"]
    if not all(k in values for k in required):
        return "Missing values", 400
    # We create a new transaction
    mutex.acquire()
    index = blockchain.new_transaction(
        values["origin"], values["destination"], values["amount"]
    )
    response = {
        "message": f"The transaction will be included in the block with index {index}"
    }
    mutex.release()
    return jsonify(response), 201


@app.route("/chain", methods=["GET"])
def full_blockchain():
    """
    Allows displaying the entire blockchain and its length

    Returns:
        json, int: the response and the response code
    """
    mutex.acquire()
    response = {
        # We only allow the chain of those final blocks that have a hash
        "chain": [b.toDict() for b in blockchain.blocks if b.hash is not None],
        "length": len(blockchain.blocks),
    }
    mutex.release()
    return jsonify(response), 200


@app.route("/system", methods=["GET"])
def get_system_info():
    """
    Displays the information of the system on which it is running

    Returns:
        json, int: message and response code
    """
    response = {
        "machine": platform.machine(),
        "system_name": platform.system(),
        "version": platform.version(),
    }
    return jsonify(response), 200


@app.route("/mine", methods=["GET"])
def mine():
    """
    Allows mining a block (i.e., obtaining a proof of work value such that the
    hash starts with as many zeros as the difficulty). In addition, it adds a transaction
    from 0 to the user with a payment for mining the block and integrates the block into the blockchain.
    Before performing all these tasks, it checks that the blockchain of this node is the longest and,
    if it is not, it updates it to the longest (and does not mine the block, transactions must be reintroduced)

    Returns:
        json, int: the message and the response code
    """
    mutex.acquire()
    blockchain_check = resolve_conflicts(network_nodes)
    if blockchain_check == 400:
        response = {"message": "The network's blockchain is corrupt"}
        mutex.release()
        return jsonify(response), 400
    elif blockchain_check:
        response = {
            "message": "There was a conflict. This chain has been updated with a longer version"
        }
    elif len(blockchain.unconfirmed_transactions) == 0:
        response = {
            "message": "It is not possible to create a new block. There are no transactions"
        }
    else:
        index = blockchain.new_transaction(0, my_ip, 1)
        previous_hash = blockchain.blocks[-1].hash
        new_block = blockchain.new_block(previous_hash)
        block_hash = blockchain.proof_of_work(new_block)
        blockchain.integrate_block(new_block, block_hash)
        print(new_block.transactions)
        response = {
            "block_hash": block_hash,
            "previous_hash": previous_hash,
            "index": index,
            "message": "New block mined",
            "proof": new_block.proof,
            "transactions": new_block.transactions,
        }
    mutex.release()
    return jsonify(response), 200


@app.route("/nodes/register", methods=["POST"])
def register_full_nodes():
    """
    This function is performed by a node that registers the nodes and updates
    its blockchain to that of the node executing this function

    Returns:
        json, int: the message and response code
    """
    values = request.get_json()
    global blockchain, network_nodes

    new_nodes = values.get("node_addresses")
    if new_nodes is None:
        return "Error: A list of nodes was not provided", 400
    all_correct = True
    network_nodes = set(new_nodes)

    mutex.acquire()
    for node in new_nodes:
        data = {
            "node_addresses": list(network_nodes - {node}) + [f"http://{my_ip}:{port}"],
            "blockchain": [
                block.toDict() for block in blockchain.blocks if block.hash is not None
            ],
        }
        # Send the data to the new node
        response = requests.post(
            node + "/nodes/simple_register",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )
        if response.status_code == 201:
            all_correct = True
    mutex.release()
    if all_correct:
        response = {
            "message": "New nodes have been included in the network",
            "total_nodes": list(network_nodes - {f"http://{my_ip}:{port}"}),
        }
    else:
        response = {
            "message": "Error notifying the stipulated node",
        }
    return jsonify(response), 201


@app.route("/nodes/simple_register", methods=["POST"])
def register_node_update_blockchain():
    """
    With this function, we update the blockchain of a node that
    registers to that of the node performing the registration

    Returns:
        str, int: the message and the response code
    """
    # We obtain the global blockchain variable
    global blockchain
    read_json = request.get_json()
    node_addresses = read_json.get("node_addresses")
    received_blockchain = read_json.get("blockchain")
    read_blockchain = None
    temporary_blockchain = BlockChain.Blockchain(received_blockchain[0]["timestamp"])
    for block_json in received_blockchain[1:]:
        block = BlockChain.Block(
            index=block_json["index"],
            transactions=block_json["transactions"],
            timestamp=block_json["timestamp"],
            previous_hash=block_json["previous_hash"],
            proof=block_json["proof"],
        )
        if not temporary_blockchain.integrate_block(block, block_json["hash"]):
            return "The network's blockchain is corrupt", 400
    read_blockchain = temporary_blockchain
    # We update the list of nodes
    network_nodes.update(node_addresses)
    if read_blockchain is None:
        return "The network's blockchain is corrupt", 400
    else:
        blockchain = read_blockchain
        return (
            "The blockchain of the node"
            + str(my_ip)
            + ":"
            + str(port)
            + "has been successfully updated",
            200,
        )


@app.route("/ping", methods=["GET"])
def ping():
    """
    The node sends a request to the rest of the nodes to see if they are working

    Returns:
        json, int: the message and the response code
    """
    host_info = request.host_url  # IP address and port of the node initiating the PING
    ping_message = {"origin": host_info, "message": "PING", "timestamp": time.time()}
    responses = []
    for node in network_nodes:
        start_time = time.time()
        response = requests.post(node + "/pong", json=ping_message)
        end_time = time.time()

        if response.status_code == 200:
            delay = end_time - start_time
            pong_response = response.json()
            pong_response["Delay"] = delay
            responses.append(pong_response)

    final_response = "#".join(
        [
            f"PING from {ping_message['origin']} Response: PONG {r['response_origin']} Delay: {r['Delay']}"
            for r in responses
        ]
    )

    if len(responses) == len(network_nodes):
        final_response += "#All nodes respond"
    else:
        final_response += "#Some nodes did not respond"

    return jsonify({"final_response": final_response}), 200


@app.route("/pong", methods=["POST"])
def pong():
    """
    The nodes respond according to the IMC protocol

    Returns:
        json, int: the message and the response code
    """
    data = request.get_json()
    response = {
        "response_origin": request.host_url,  # IP address and port of the responding node
        "original_message": data["message"],
        "response_message": "PONG",
    }
    return jsonify(response), 200


def resolve_conflicts(nodes_addresses):
    """
    Mechanism to establish consensus and resolve conflicts by comparing the
    length of the node's blockchain with that of the rest of the registered nodes

    Args:
        nodes_addresses (set): the IPs of the nodes

    Returns:
        bool/int: Whether the blockchain has been replaced or not, or 400 if there was an error
    """
    global blockchain
    current_length = len(blockchain.blocks)
    has_changed = False
    temporary_blockchain = blockchain
    # [Code to complete]
    addresses = nodes_addresses.copy()
    own_address = f"http://{my_ip}:{port}"
    if own_address in addresses:
        addresses.remove(f"http://{my_ip}:{port}")
    for node in addresses:
        response = requests.get(str(node) + "/chain")
        if response.status_code == 200:
            node_chain = response.json()["chain"]

            if len(node_chain) > current_length:
                has_changed = True
                temporary_blockchain = BlockChain.Blockchain(node_chain[0]["timestamp"])

                for block_json in node_chain[1:]:
                    block = BlockChain.Block(
                        index=block_json["index"],
                        transactions=block_json["transactions"],
                        timestamp=block_json["timestamp"],
                        previous_hash=block_json["previous_hash"],
                        proof=block_json["proof"],
                    )

                    if not temporary_blockchain.integrate_block(
                        block, block_json["hash"]
                    ):
                        return 400
    blockchain = temporary_blockchain
    return True if has_changed else False


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-p", "--port", default=5000, type=int, help="port to listen on"
    )
    args = parser.parse_args()
    port = args.port
    t = Thread(target=backup_copy)
    t.start()
    app.run(host="0.0.0.0", port=port)
    t.join()
