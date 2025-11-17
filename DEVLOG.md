# Dev Log - Bank Simulation

November 15, 2025 3:30PM

Starting the bank/teller simulation project. This is going to be a multi-threaded application simulating a bank with 3 tellers and 50 customers.

Building a bank simulation using synchronization:
1. Tellers (3 threads): Serve customers, access manager for withdrawals, use the safe
2. Customers (50 threads): Randomly select transactions, wait in line, complete banking
3. Synchronization: Semaphores for resource management (door, manager, safe)
4. Output: Formatted logging of all thread actions



November 15, 4:16PM

1) Need to understand the synchronization requirements:
    Door: 2 customers entering simultaneously
    Manager: 1 teller accessing (for withdrawals)
    Safe: 2 tellers accessing simultaneously
    Bank must open only when all 3 tellers are ready

2) Thread communication:
    Tellers need to know when customers approach
    Customers need to wait for teller to be ready
    Both need to be present for transaction
    Customer must wait for transaction completion

3) how will the structure  work:
    Semaphores for door (2), manager (1), safe (2)
    Event objects for teller-customer communication
    Queue for customers line
    Dictionary to map customers to the tellers

I will start with 3 customers, 1 per teller so i can make sure they are able to communicate.



November 15, 6:20PM

Created the basic imports and constants. Set up semaphores for the shared resources.

Problems:
I'm having trouble with the teller-customer synchronization. At first, I tried using just a simple queue, but customers and tellers weren't able to communicate properly.

Potential Issues:
   Simple queue doesn't provide enough coordination
   Need bidirectional communication between threads
   Customer needs to wait for specific events from teller
   Teller needs to wait for specific events from customer

Solution: 
Created a CustomerEvents class with multiple Event objects for each step of the interaction:
  teller_ready: Teller signals they're ready to serve
  transaction_given: Customer provides transaction type
  transaction_complete: Teller finishes transaction
  customer_left: Customer leaves the teller

Summary: I was able to impement proper communcation between the threads. The teller will be able to signal when
they are ready. and also the type of transaction wether its a deposit or withdrawal. And signal off when the 
customer has left. I will continue tommorrow



November 16,  9:12AM

Starting the project again

Teller thread function:
1) Each teller needs a unique ID, so there isnt overlap
2) Signal when ready to serve
3) Wait for bank to open (all 3 tellers must be ready)
4) Loop: wait for customer, serve them, repeat
5) For withdrawals: access manager (only one semaphore for manager)
6) Always access safe
7) Use random sleep times to simulate work

Problems:
The teller threads are all trying to serve the same customer. Multiple tellers are printing that they're serving
 Customer 0.

Potential Issues:
   Race condition in customer
   Not properly tracking which teller serves which customer

Solution: Added a customer_teller_map dictionary to track assignments. Also needed to make sure that the teller
 ID is stored before the customer starts waiting for the teller_ready event. Used proper locking around the 
 critical section where we assign teller to customer. Now we can make sure the teller thread is working.



November 16 1:34 PM

Customer threads:
1) Each customer needs unique ID
2) Random: DEPOSIT or WITHDRAWAL
3) Random wait time before entering bank
4) Enter through door (max 2 customers at a time)
5) Get in line
6) Wait for teller to be ready
7) Introduce self and give transaction
8) Wait for completion
9) Leave

Problems:
Im having trouble with deadlock, The program is hanging after a few customers are served. Looking at the output, it seems like customers are waiting forever for tellers to be ready.

Potential Issues:
  Event flags not being reset properly
  Teller might be waiting while customer is waiting
  Event.wait() not being called in correct order

Solution: The issue was with event flag management. I was setting flags but not resetting them after use. Changed
to explicitly set flags to False after waiting on them. Also made sure that events are new for each customer 
rather than reusing old ones.



November 16, 5:30PM

Trying to add more customers.

Problems with 5 customers:
Sometimes customers are getting stuck, they enter the bank but never get served.

Potential Issues:
  Queue.get() might be getting timed out
  Tellers might be exiting loop to early
  customers served counter might be wrong

Solution: The problem was in the teller loop exit condition. I was checking if customers were getting served, but 
i was checking before all customers had a chance to get in line. Added a small timeout to Queue.get() and used 
try-except to handle empty queue. Also moved the exit check to only happen when queue is actually empty.


November 16, 7:39PM

Final Session complete.
I fixed the output message structure to match the example given, and wrote the read me file.


Key Take aways: Something i really learned thorugh this experiment was the race conditions. I had to make sure i 
handeling them the right way. and make sure that i was locking properly. I had to make sure the flags were being turned on and off correctly. It was a difficult project but overall i learned a lot.