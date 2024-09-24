"""
Test module by Sergio Jiménez Romero and David Tarrasa Puebla
"""

import requests
import json

headers = {"Content-type": "application/json", "Accept": "text/plain"}

# Node addresses
nodes = [
    "http://192.168.0.27:5000",
    "http://192.168.0.63:5001",
]  # Address of node 5000 on Windows, Address of 5001 on Ubuntu in VirtualBox (virtual machine), can also be the address of 5001 on Windows


def send_transaction(node, transaction):
    response = requests.post(
        f"{node}/transactions/new", data=json.dumps(transaction), headers=headers
    )
    print(f"Response from node {node}:")
    print(response.text)


def mine_block(node):
    response = requests.get(f"{node}/mine")
    print(f"Response from node {node} when mining:")
    print(response.text)


def get_chain(node):
    response = requests.get(f"{node}/chain")
    print(f"Chain of node {node}:")
    print(response.text)


def get_system_info(node):
    response = requests.get(f"{node}/system")
    print(f"Details of node {node}:")
    print(response.text)


def register_nodes_in_first():
    first_node = nodes[0]
    nodes_to_register = {"node_addresses": nodes[1:]}
    response = requests.post(
        f"{first_node}/nodes/register",
        data=json.dumps(nodes_to_register),
        headers=headers,
    )
    print("Register nodes in the first node:")
    print(response.text)


def send_ping():
    for node in nodes:
        response = requests.get(f"{node}/ping", headers=headers)
        print(f"Ping to node {node}:")
        print(response.text)


register_nodes_in_first()
send_ping()

new_transaction = {"origin": "nodeA", "destination": "nodeB", "amount": 10}
send_transaction(nodes[0], new_transaction)
mine_block(nodes[0])

send_transaction(nodes[1], new_transaction)
mine_block(nodes[1])

for node in nodes:
    get_chain(node)
    get_system_info(node)
