# Development Log - Bank/Teller Simulation

November 14, 2025 9:45AM

Starting the bank/teller simulation project. This is going to be a multi-threaded application simulating a bank with 3 tellers and 50 customers.

## Project Overview
Building a concurrent bank simulation with proper thread synchronization:
1. **Tellers (3 threads)** - Serve customers, access manager for withdrawals, use the safe
2. **Customers (50 threads)** - Randomly select transactions, wait in line, complete banking
3. **Synchronization** - Semaphores for resource management (door, manager, safe)
4. **Output** - Formatted logging of all thread actions

## Python Implementation

### Thought Process for Initial Setup

November 14, 10:23 AM

1) Need to understand the synchronization requirements:
   - Door: Max 2 customers entering simultaneously
   - Manager: Max 1 teller accessing (for withdrawals)
   - Safe: Max 2 tellers accessing simultaneously
   - Bank must open only when all 3 tellers are ready

2) Thread communication will be tricky:
   - Tellers need to know when customers approach
   - Customers need to wait for teller to be ready
   - Both need to coordinate transaction handoff
   - Customer must wait for transaction completion

3) Plan the data structures:
   - Semaphores for door (2), manager (1), safe (2)
   - Event objects for teller-customer handshaking
   - Queue for customers waiting to be served
   - Dictionary to map customers to their assigned tellers

Starting with a simple version with just 3 customers to test the logic before scaling to 50.

### Implementing Basic Structure

November 14, 11:15 AM

Created the basic skeleton with imports and constants. Set up semaphores for the shared resources.

Problems encountered:

I'm having trouble with the teller-customer synchronization. At first, I tried using just a simple queue, but customers and tellers weren't coordinating properly.

- Potential Issues:
  - Simple queue doesn't provide enough coordination
  - Need bidirectional communication between threads
  - Customer needs to wait for specific events from teller
  - Teller needs to wait for specific events from customer

- Solution: Created a CustomerEvents class with multiple Event objects for each step of the interaction:
  - teller_ready: Teller signals they're ready to serve
  - transaction_given: Customer provides transaction type
  - transaction_complete: Teller finishes transaction
  - customer_left: Customer leaves the teller

This allows for proper handshaking between threads.

### Teller Thread Logic

November 14, 1:45 PM

Came back from lunch break.

Implementing the teller thread function:

1) Each teller needs a unique ID
2) Signal when ready to serve
3) Wait for bank to open (all 3 tellers must be ready)
4) Loop: wait for customer, serve them, repeat
5) For withdrawals: access manager (semaphore with limit 1)
6) Always access safe (semaphore with limit 2)
7) Use random sleep times to simulate work

Problems:

The teller threads are all trying to serve the same customer! Multiple tellers are printing that they're serving Customer 0.

- Potential Issues:
  - Race condition in customer assignment
  - Not properly tracking which teller serves which customer
  - Queue operations not atomic enough

- Solution: Added a customer_teller_map dictionary to track assignments. Also needed to ensure that the teller ID is stored BEFORE the customer starts waiting for the teller_ready event. Used proper locking around the critical section where we assign teller to customer.

### Customer Thread Logic

November 14, 3:20 PM

Implementing customer threads:

1) Each customer needs unique ID
2) Randomly decide: DEPOSIT or WITHDRAWAL
3) Random wait time (0-100ms) before entering bank
4) Enter through door (max 2 at once - door semaphore)
5) Get in line (add to queue)
6) Wait for teller to be ready
7) Introduce self and give transaction
8) Wait for completion
9) Leave

Problems:

Deadlock! The program is hanging after a few customers are served. Looking at the output, it seems like customers are waiting forever for tellers to be ready.

- Potential Issues:
  - Event flags not being reset properly
  - Teller might be waiting while customer is waiting (circular wait)
  - Event.wait() not being called in correct order
  - Missing notify_one() calls

- Solution: The issue was with event flag management. I was setting flags but not resetting them after use. Changed to explicitly set flags to False after waiting on them. Also ensured that events are created fresh for each customer rather than reusing old ones.

End Session: Taking a break. Got basic teller-customer interaction working with 3 customers. Next: test with increasing numbers and fix any race conditions.

### Testing and Scaling

November 14, 5:30 PM

Back from break. Time to scale up and test thoroughly.

Testing progression:
- 3 customers: ✓ Works
- 5 customers: Testing now

Problems with 5 customers:

Sometimes customers are getting "stuck" - they enter the bank but never get served.

- Potential Issues:
  - Queue.get() might be timing out
  - Tellers might be exiting loop prematurely
  - Race condition in queue operations
  - customers_served counter might be wrong

- Solution: The problem was in the teller loop exit condition. I was checking `if customers_served >= NUM_CUSTOMERS` but this check happened too early, before all customers had a chance to get in line. Added a small timeout to Queue.get() and used try-except to handle empty queue gracefully. Also moved the exit check to only happen when queue is genuinely empty.

Testing with 10 customers: Works!
Testing with 50 customers: Works!

### Output Formatting Issues

November 14, 6:15 PM

The output format isn't matching the requirements exactly. The PDF says format should be:
`THREAD_TYPE ID [THREAD_TYPE ID]: MSG`

But I had some inconsistencies:
- Empty brackets when no other thread involved
- Missing colons in some places
- Messages not clear enough

Fixed the print_log function to handle cases where there's no "other thread" involved (like when customer decides on transaction type).

Also noticed that the withdrawal transactions weren't explicitly showing the manager access in a clear way. Added more descriptive messages.

### Final Testing and Verification

November 14, 7:00 PM

Running final comprehensive tests:

Tested multiple times with 50 customers - no deadlocks detected!
Verified output format matches PDF requirements exactly.
Checked all synchronization constraints:
- ✓ Door: Max 2 customers entering simultaneously
- ✓ Manager: Max 1 teller accessing at once
- ✓ Safe: Max 2 tellers accessing simultaneously
- ✓ Bank opens only when all 3 tellers ready

### Documentation

November 14, 7:30 PM

Created README.md with:
- Project description
- Requirements and usage instructions
- Implementation details
- Example output

End Session: Python implementation is complete and working perfectly! All requirements met, output looks professional, no bugs found after extensive testing. Ready for submission.

---

## Lessons Learned

### Development Process
1. **Start Small**: Testing with 3 customers first before scaling to 50 was crucial for catching basic issues
2. **Incremental Testing**: Going 3 → 5 → 10 → 50 helped identify different classes of bugs at each level
3. **Logging is Essential**: Clear, formatted output made debugging thread interactions much easier
4. **One Change at a Time**: Changed one thing between tests to isolate problems

### Technical Insights
1. **Event-based synchronization**: More complex than just semaphores but necessary for bidirectional communication between threads
2. **Queue timeout handling**: Needed to handle empty queues gracefully to avoid busy-waiting
3. **Deadlock prevention**: Careful ordering of lock acquisition and proper use of timeouts prevented hangs
4. **Race conditions are subtle**: The customers_served counter issue wasn't immediately obvious

### Thread Synchronization
- **Semaphores**: Perfect for limiting resource access (door, safe, manager)
- **Events**: Great for wait/notify patterns between specific threads
- **Queues**: Built-in thread-safety made customer queue implementation simple
- **Locks**: Critical for protecting shared state like counters

## Time Breakdown

**Planning and Design**: 1 hour
- Understanding requirements
- Planning synchronization strategy
- Designing thread communication protocol

**Implementation**: 2 hours
- Basic thread structure
- Teller and customer logic
- Semaphore setup

**Debugging**: 2 hours
- Event coordination issues
- Race condition with customers_served
- Queue timeout handling
- Output formatting

**Testing and Refinement**: 1 hour
- Testing with 3, 5, 10, 50 customers
- Final verification of all requirements
- Multiple test runs for reliability

**Total**: ~6 hours

## Final Notes

This project really helped me understand:
- How to coordinate multiple threads with different synchronization primitives
- The producer-consumer pattern with multiple producers and consumers
- Resource management with limited concurrent access
- The importance of proper thread lifecycle management
- How to debug multithreaded programs effectively

Key success factors:
- Starting with small test cases
- Clear output format that shows thread interactions
- Incremental development and testing
- Proper use of Python's threading primitives

The final implementation successfully handles 50 customers with 3 tellers, properly enforcing all resource constraints, with no deadlocks or race conditions detected across multiple test runs.

