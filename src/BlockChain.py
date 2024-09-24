"""
Blockchain implementation by Sergio Jiménez Romero and David Tarrasa Puebla
"""

from typing import List
import json
import hashlib
import time


class Block:
    def __init__(
        self,
        index: int,
        transactions: List,
        timestamp: int,
        previous_hash: str,
        proof: int = 0,
    ):
        """
        Constructor of the 'Block' class

        Args:
            index (int): Unique ID of the block
            transactions (List): List of transactions
            timestamp (int): Time when the block was generated.
            previous_hash (str): Previous hash
            proof (int, optional): Proof of work. Default is 0.
        """
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.proof = proof
        self.hash = None

    def calculate_hash(self):
        """
        Returns the hash of a block

        Returns:
            str: the hash of the block
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def toDict(self):
        """
        This method returns the parameters of a block as a dictionary

        Returns:
            dict: the different parameters of the block in a dictionary
        """
        return {
            "hash": self.hash,
            "previous_hash": self.previous_hash,
            "index": self.index,
            "proof": self.proof,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
        }


class Blockchain(object):
    def __init__(self, time=time.time()):
        """
        Constructor of the 'Blockchain' class. When initializing the class, we also generate the first
        block. The time argument is optional to specify a timestamp if we want to reconstruct a blockchain

        Args:
            time (float, optional): Specific timestamp if we want to reconstruct a blockchain. Defaults to time.time().
        """
        self.difficulty = 4
        self.blocks = []
        self.unconfirmed_transactions = []
        self.index = 1
        self.create_genesis_block(time)

    def create_genesis_block(self, time):
        genesis_block = Block(1, [], time, 1)
        genesis_block.hash = genesis_block.calculate_hash()
        self.index += 1
        self.blocks.append(genesis_block)

    def new_block(self, previous_hash: str) -> Block:
        """
        Creates a new block from the unconfirmed transactions

        Args:
            previous_hash (str): the hash of the previous block in the chain

        Returns:
            Block: the new block
        """

        transactions = self.unconfirmed_transactions.copy()
        new_block = Block(self.index, transactions, time.time(), previous_hash)
        self.unconfirmed_transactions.clear()
        self.index += 1
        return new_block

    def new_transaction(self, origin: str, destination: str, amount: int) -> int:
        """
        Creates a new transaction from an origin, a destination, and an amount
        and includes it in the list of transactions

        Args:
            origin (str): the sender of the transaction
            destination (str): the receiver of the transaction
            amount (int): the amount

        Returns:
            int: the index of the block that will store the transaction
        """
        self.unconfirmed_transactions.append(
            {
                "origin": origin,
                "destination": destination,
                "amount": amount,
                "time": time.time(),
            }
        )
        return self.index

    def proof_of_work(self, block: Block) -> str:
        """
        Simple proof of work algorithm:
        - It will calculate the hash of the block until it finds a hash that starts
        with as many zeros as the difficulty.
        - Each time the block gets a hash that is not suitable,
        it will increment the 'proof' field of the block by one

        Args:
            block (Block): block object

        Returns:
            str: the hash of the new block (it will leave the block's hash field unmodified)
        """
        hash = block.calculate_hash()
        while hash[: self.difficulty] != "0" * self.difficulty:
            block.proof += 1
            hash = block.calculate_hash()
        return hash

    def valid_proof(self, block: Block, block_hash: str) -> bool:
        """
        Method that checks if the block_hash starts with as many zeros as the
        difficulty stipulated in the blockchain
        It will also check that block_hash matches the value returned by the
        block's calculate_hash method.

        Args:
            block (Block): a block object
            block_hash (str): the block's hash

        Returns:
            bool: indicates if the proof value is correct
        """
        try:
            return (
                block_hash == block.calculate_hash()
                and block_hash[: self.difficulty] == "0" * self.difficulty
            )
        except:
            return False

    def integrate_block(self, new_block: Block, proof_hash: str) -> bool:
        """
        Method to correctly integrate a block into the blockchain.
        It must check that proof_hash is valid and that the hash of the last block
        in the chain matches the previous_hash of the block to be integrated.
        If it passes the checks, it updates the hash of the new block to integrate
        with proof_hash, inserts it into the chain, and resets the unconfirmed transactions
        (clears the list of unconfirmed transactions)

        Args:
            new_block (Block): the new block to be integrated
            proof_hash (str): the proof hash

        Returns:
            bool: True if it was executed correctly and False otherwise (if
                  it did not pass some check)
        """
        if new_block.previous_hash == self.blocks[-1].hash and self.valid_proof(
            new_block, proof_hash
        ):
            new_block.hash = proof_hash
            self.blocks.append(new_block)
            return True
        else:
            return False
