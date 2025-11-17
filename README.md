# Bank Simulation - OS Project 2

A multi-threaded simulation of a bank with tellers and customers using Python's threading module and semaphores for synchronization.

## Description
This program simulates a bank with 3 tellers serving 50 customers. The simulation demonstrates:
    Thread synchronization using semaphores and events
    Resource management (door, manager, safe)
    Producer-consumer pattern (tellers and customers)
    Thread-safe logging

## Requirements
Python 3.x

## Run
Run the simulation:

```bash
python3 bank_simulation.py
```

## Configuration
You can modify the constants at the top of `os_bank_sim.py`:

```python
NUM_TELLERS = 3      # Number of teller threads
NUM_CUSTOMERS = 50   # Number of customer threads
```


### Key Components
1. Semaphores:
   - `door_semaphore`: Controls entry (limit 2)
   - `manager_semaphore`: Controls manager access (limit 1)
   - `safe_semaphore`: Controls safe access (limit 2)

2. Events per Customer:
   - `teller_ready`: Teller is ready to serve
   - `transaction_given`: Customer provided transaction type
   - `transaction_complete`: Teller finished transaction
   - `customer_left`: Customer has left

3. Data Structures:
   - `customer_queue`: Queue of customers waiting for tellers
   - `customer_teller_map`: Maps customer IDs to assigned teller IDs
   - `customer_events`: Dictionary of event objects for each customer


## Project Structure
```
OS Project2/
├── bank_simulation.py    # Main simulation program
├── project2.pdf         # Project requirements
└── README.md           # This file
```


CS4348 - Operating Systems Concepts
Fall 2025

