#  Blockchain-based Web Application 🛠️🌐


Blockchain is a repository for developing a blockchain-based web application as part of the "Fundamentos de Sistemas Operativos" course.

<!-- TABLE OF CONTENTS -->
- [Blockchain-based Web Application 🛠️🌐](#blockchain-based-web-application-️)
  - [About the Project](#about-the-project)
  - [Key Features ✨](#key-features-)
    - [Blockchain Implementation](#blockchain-implementation)
    - [Web Application](#web-application)
    - [Decentralized Application (DApp)](#decentralized-application-dapp)
    - [Backup and Reliability 💾](#backup-and-reliability-)
  - [Libraries and Dependencies 📚](#libraries-and-dependencies-)
  - [Running the Application 🚀](#running-the-application-)
  - [Developers 🔧](#developers-)

## About the Project 

**Blockchain_app** is a blockchain-based web application developed as part of the "Fundamentos de Sistemas Operativos" course. The project aims to understand and implement decentralized technologies, highlighting their advantages over traditional centralized systems.

## Key Features ✨

### Blockchain Implementation
- **Decentralized Network:** Distributes workload across multiple nodes, eliminating single points of failure and enhancing scalability and privacy.
- **Security and Integrity:** Utilizes cryptographic hashes and a Proof of Work (PoW) algorithm to ensure data integrity and prevent tampering.
- **Block and Transaction Structure:** Each block contains a hash of the previous block, a list of transactions, a timestamp, and a nonce, ensuring data consistency and security.

### Web Application
- **Built with Flask:** The web interface allows users to interact with the blockchain, including mining new blocks, creating transactions, and viewing the current blockchain state.
- **Endpoints:**
  - `/mine`: Mines a new block and adds it to the blockchain.
  - `/transactions/new`: Creates a new transaction to be added to the next mined block.
  - `/chain`: Displays the current state of the blockchain.

### Decentralized Application (DApp)
- **Node Registration and Synchronization:** New nodes can join the network, register themselves, and receive a copy of the current blockchain to stay synchronized.
- **Conflict Resolution:** Implements the longest chain rule to ensure all nodes agree on the blockchain state, resolving any conflicts that arise.
  
### Backup and Reliability 💾

Regular backups are crucial for maintaining blockchain integrity. In case of failures, administrators can restore the blockchain to a known consistent state, ensuring network reliability.

A backup of the entire blockchain is created every 60 seconds to enable the reconstruction of the blockchain to a recent state

## Libraries and Dependencies 📚

> It is recommended to use Python version 3.x to avoid possible incompatibilities with dependencies and libraries.

The `requirements.txt` file contains all the necessary libraries to run the code without errors.

```bash
pip install -r requirements.txt
```
## Running the Application 🚀

Start the Flask application:

```bash

python Blockchain_app.py
```

Access the web interface at http://127.0.0.1:5000.


  * Mining a Block: Send a GET request to /mine.
  * Creating a Transaction: Send a POST request to /transactions/new with the transaction details.
  * Viewing the Blockchain: Send a GET request to /chain.



## Developers 🔧

   * [Sergio Jimenez](https://github.com/sjrom47)
   * [David Tarrasa](https://github.com/davidtarrasa)