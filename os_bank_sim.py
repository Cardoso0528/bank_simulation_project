#!/usr/bin/env python3
"""
Bank/Teller Simulation - OS Project 2
Simulates a bank with 3 tellers and 50 customers using threads and semaphores.
"""

import threading
import time
import random
from queue import Queue

# Constants
NUM_TELLERS = 3
NUM_CUSTOMERS = 50

# Semaphores for shared resources
door_semaphore = threading.Semaphore(2)  # Max 2 customers entering at once
manager_semaphore = threading.Semaphore(1)  # Max 1 teller with manager
safe_semaphore = threading.Semaphore(2)  # Max 2 tellers in safe

# Synchronization primitives
bank_open = threading.Event()  # Signals when bank is open
print_lock = threading.Lock()  # For thread-safe printing
teller_ready_lock = threading.Lock()
teller_ready_count = 0

# Customer-teller communication
# Dictionary to store events and teller ID for each customer
customer_events = {}
customer_teller_map = {}  # Maps customer_id to teller_id

# Queue for customers waiting to be served
customer_queue = Queue()

# Counter for customers served
customers_served_lock = threading.Lock()
customers_served = 0


def print_log(thread_type, thread_id, other_type=None, other_id=None, message=""):
    """
    Thread-safe logging function.
    Format: THREAD_TYPE ID [THREAD_TYPE ID]: MSG
    """
    with print_lock:
        if other_type and other_id is not None:
            print(f"{thread_type} {thread_id} [{other_type} {other_id}]: {message}")
        else:
            print(f"{thread_type} {thread_id}: {message}")


def teller_thread(teller_id):
    """
    Teller thread function.
    Each teller serves customers until all are served.
    """
    global teller_ready_count, customers_served
    
    # Step 1: Signal ready
    with teller_ready_lock:
        teller_ready_count += 1
        print_log("Teller", teller_id, message="ready to serve")
        if teller_ready_count == NUM_TELLERS:
            bank_open.set()
    
    # Step 2: Loop until all customers served
    while True:
        # Check if all customers have been served
        with customers_served_lock:
            if customers_served >= NUM_CUSTOMERS:
                break
        
        # Wait for a customer to approach (blocking get from queue)
        try:
            customer_id = customer_queue.get(timeout=0.5)
        except:
            continue
        
        # Store which teller is serving this customer
        customer_teller_map[customer_id] = teller_id
        
        # Customer has approached - get their events
        events = customer_events[customer_id]
        
        # Signal customer we're ready and ask for transaction
        events['teller_ready'].set()
        print_log("Teller", teller_id, "Customer", customer_id, "asks for transaction")
        
        # Wait for customer to provide transaction
        events['transaction_given'].wait()
        events['transaction_given'].clear()
        
        transaction_type = events['transaction_type']
        
        # If withdrawal, go to manager
        if transaction_type == "WITHDRAWAL":
            print_log("Teller", teller_id, "Customer", customer_id, "goes to the manager for permission")
            manager_semaphore.acquire()
            print_log("Teller", teller_id, "Customer", customer_id, "getting permission from manager")
            time.sleep(random.uniform(0.005, 0.030))  # 5-30ms
            print_log("Teller", teller_id, "Customer", customer_id, "got permission from manager")
            manager_semaphore.release()
        
        # Go to safe
        print_log("Teller", teller_id, "Customer", customer_id, "goes to the safe")
        safe_semaphore.acquire()
        print_log("Teller", teller_id, "Customer", customer_id, "enters safe")
        time.sleep(random.uniform(0.010, 0.050))  # 10-50ms
        print_log("Teller", teller_id, "Customer", customer_id, f"completes {transaction_type.lower()} in safe")
        print_log("Teller", teller_id, "Customer", customer_id, "leaves safe")
        safe_semaphore.release()
        
        # Inform customer transaction is complete
        print_log("Teller", teller_id, "Customer", customer_id, "informs customer transaction is complete")
        events['transaction_complete'].set()
        
        # Wait for customer to leave
        events['customer_left'].wait()
        events['customer_left'].clear()


def customer_thread(customer_id):
    """
    Customer thread function.
    Each customer performs one transaction and leaves.
    """
    global customers_served
    
    # Step 1: Decide transaction type
    transaction_type = random.choice(["DEPOSIT", "WITHDRAWAL"])
    print_log("Customer", customer_id, message=f"decides to make a {transaction_type.lower()}")
    
    # Step 2: Wait random time (0-100ms)
    wait_time = random.uniform(0, 0.100)
    time.sleep(wait_time)
    
    # Wait for bank to open
    bank_open.wait()
    
    # Step 3: Enter bank (door allows max 2)
    door_semaphore.acquire()
    print_log("Customer", customer_id, message="enters bank through door")
    door_semaphore.release()
    
    # Step 4: Get in line
    print_log("Customer", customer_id, message="gets in line")
    
    # Create events for this customer
    customer_events[customer_id] = {
        'teller_ready': threading.Event(),
        'transaction_given': threading.Event(),
        'transaction_complete': threading.Event(),
        'customer_left': threading.Event(),
        'transaction_type': transaction_type
    }
    
    # Put self in customer queue
    customer_queue.put(customer_id)
    
    # Wait for a teller to be ready
    customer_events[customer_id]['teller_ready'].wait()
    customer_events[customer_id]['teller_ready'].clear()
    
    # Get the teller ID assigned to this customer
    teller_id = customer_teller_map[customer_id]
    
    # Step 5: Introduce self to teller
    print_log("Customer", customer_id, "Teller", teller_id, "goes to teller")
    print_log("Customer", customer_id, "Teller", teller_id, f"introduces self and requests {transaction_type.lower()}")
    customer_events[customer_id]['transaction_given'].set()
    
    # Step 8: Wait for transaction to complete
    customer_events[customer_id]['transaction_complete'].wait()
    customer_events[customer_id]['transaction_complete'].clear()
    
    # Step 9: Leave teller and bank
    print_log("Customer", customer_id, "Teller", teller_id, "thanks teller and leaves")
    customer_events[customer_id]['customer_left'].set()
    
    print_log("Customer", customer_id, message="leaves bank through door")
    
    # Increment customers served
    with customers_served_lock:
        customers_served += 1


def main():
    """
    Main function to initialize and run the simulation.
    """
    print("Bank Simulation Starting...")
    print(f"Opening bank with {NUM_TELLERS} tellers and {NUM_CUSTOMERS} customers\n")
    
    # Create and start teller threads
    teller_threads = []
    for i in range(NUM_TELLERS):
        t = threading.Thread(target=teller_thread, args=(i,))
        t.start()
        teller_threads.append(t)
    
    # Wait for bank to open
    bank_open.wait()
    print("\n--- Bank is now OPEN ---\n")
    
    # Create and start customer threads
    customer_threads = []
    for i in range(NUM_CUSTOMERS):
        t = threading.Thread(target=customer_thread, args=(i,))
        t.start()
        customer_threads.append(t)
    
    # Wait for all customers to finish
    for t in customer_threads:
        t.join()
    
    # Wait for all tellers to finish
    for t in teller_threads:
        t.join()
    
    print("\n--- Bank is now CLOSED ---")
    print(f"All {NUM_CUSTOMERS} customers have been served.")


if __name__ == "__main__":
    main()

