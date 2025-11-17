#!/usr/bin/env python3
"""
Bank/Teller Simulation - OS Project 2
Simulates a bank with 3 tellers and 50 customers using threads and semaphores.
"""

import threading
import time
import random
from queue import Queue

#global constants per the project requirements
num_tellers = 3
num_customers = 50

#semaphores to determine the numbers of customers and tellers that can be in the bank at once
door_sem = threading.Semaphore(2)
manager_sem = threading.Semaphore(1)
safe_sem = threading.Semaphore(2)

#synchronization to ensure the correct order of events
bank_open = threading.Event()  
print_lock = threading.Lock()  # to make sure we print the events in the correct order
teller_ready_lock = threading.Lock()
teller_ready_count = 0

# dictionary to store events and teller ID for each customer
customer_events = {}
customer_teller_map = {}

# the line for customers to wait in
customer_queue = Queue()

# counter to keep track of the number of customers served
customers_served_lock = threading.Lock()
customers_served = 0

# function to print the events in the correct order
def print_log(thread_type, thread_id, other_type=None, other_id=None, message=""):
    with print_lock:
        if other_type and other_id is not None:
            print(f"{thread_type} {thread_id} [{other_type} {other_id}]: {message}")
        else:
            print(f"{thread_type} {thread_id}: {message}")

# teller thread function
def teller_thread(teller_id):
    global teller_ready_count, customers_served
    
    # signal the teller is ready to serve
    with teller_ready_lock:
        teller_ready_count += 1
        print_log("Teller", teller_id, message="ready to serve")
        if teller_ready_count == num_tellers:
            bank_open.set()
    
    # loop until all customers have been served
    while True:
        with customers_served_lock:
            if customers_served >= num_customers:
                break
        
        # wait for a customer to approach the teller
        try:
            customer_id = customer_queue.get(timeout=0.5)
        except:
            continue
        
        # store which teller is serving this customer
        customer_teller_map[customer_id] = teller_id
        
        # get the events for the customer
        events = customer_events[customer_id]
        
        # signal the customer is ready to give a transaction
        events['teller_ready'].set()
        print_log("Teller", teller_id, "Customer", customer_id, "asks for transaction")
        
        # wait for the customer to provide a transaction
        events['transaction_given'].wait()
        events['transaction_given'].clear()
        
        trans_type = events['transaction_type']
        
        # if the transaction is a withdrawal, go to the manager
        if trans_type == "WITHDRAWAL":
            print_log("Teller", teller_id, "Customer", customer_id, "goes to the manager for permission")
            manager_sem.acquire()
            print_log("Teller", teller_id, "Customer", customer_id, "getting permission from manager")
            time.sleep(random.uniform(0.005, 0.030))
            print_log("Teller", teller_id, "Customer", customer_id, "got permission from manager")
            manager_sem.release()
        
        # go to the safe
        print_log("Teller", teller_id, "Customer", customer_id, "goes to the safe")
        safe_sem.acquire()
        print_log("Teller", teller_id, "Customer", customer_id, "enters safe")
        time.sleep(random.uniform(0.010, 0.050))
        print_log("Teller", teller_id, "Customer", customer_id, f"completes {trans_type.lower()} in safe")
        print_log("Teller", teller_id, "Customer", customer_id, "leaves safe")
        safe_sem.release()
        
        # inform the customer that the transaction is complete
        print_log("Teller", teller_id, "Customer", customer_id, "informs customer transaction is complete")
        events['transaction_complete'].set()
        
        # wait for the customer to leave
        events['customer_left'].wait()
        events['customer_left'].clear()


def customer_thread(customer_id):
    global customers_served
    
    # decide the transaction type
    trans_type = random.choice(["DEPOSIT", "WITHDRAWAL"])
    print_log("Customer", customer_id, message=f"decides to make a {trans_type.lower()}")
    
    # wait for a random time (0-100ms)
    wait_time = random.uniform(0, 0.100)
    time.sleep(wait_time)
    
    # wait for the bank to open
    bank_open.wait()
    
    # enter the bank (door allows max 2)
    door_sem.acquire()
    print_log("Customer", customer_id, message="enters bank through door")
    door_sem.release()
    
    # get in line
    print_log("Customer", customer_id, message="gets in line")
    
    # create events for this customer
    customer_events[customer_id] = {
        'teller_ready': threading.Event(),
        'transaction_given': threading.Event(),
        'transaction_complete': threading.Event(),
        'customer_left': threading.Event(),
        'transaction_type': trans_type
    }
    
    # put the customer in the customer queue
    customer_queue.put(customer_id)
    
    # wait for a teller to be ready
    customer_events[customer_id]['teller_ready'].wait()
    customer_events[customer_id]['teller_ready'].clear()
    
    # get the teller ID assigned to the customer
    teller_id = customer_teller_map[customer_id]
    
    # introduce the customer to the teller
    print_log("Customer", customer_id, "Teller", teller_id, "goes to teller")
    print_log("Customer", customer_id, "Teller", teller_id, f"introduces self and requests {trans_type.lower()}")
    customer_events[customer_id]['transaction_given'].set()
    
    # wait for the transaction to complete
    customer_events[customer_id]['transaction_complete'].wait()
    customer_events[customer_id]['transaction_complete'].clear()
    
    # leave the teller and bank
    print_log("Customer", customer_id, "Teller", teller_id, "thanks teller and leaves")
    customer_events[customer_id]['customer_left'].set()
    
    print_log("Customer", customer_id, message="leaves bank through door")
    
    # increment the number of customers served
    with customers_served_lock:
        customers_served += 1


# main function to initialize and run the simulation
def main():
    print("Bank Simulation Starting...")
    print(f"Opening bank with {num_tellers} tellers and {num_customers} customers\n")
    
    # create and start teller threads
    teller_threads = []
    for i in range(num_tellers):
        t = threading.Thread(target=teller_thread, args=(i,))
        t.start()
        teller_threads.append(t)
    
    # wait for the bank to open
    bank_open.wait()
    print("\nBank is now open\n")
    
    # create and start customer threads
    customer_threads = []
    for i in range(num_customers):
        t = threading.Thread(target=customer_thread, args=(i,))
        t.start()
        customer_threads.append(t)
    
    # wait for all customers to finish
    for t in customer_threads:
        t.join()
    
    # wait for all tellers to finish
    for t in teller_threads:
        t.join()
    
    print("\nBank is now closed")
    print(f"All {num_customers} customers have been served.")


if __name__ == "__main__":
    main()

