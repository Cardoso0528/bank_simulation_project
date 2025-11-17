# Bank/Teller Simulation - C++ Implementation

A multi-threaded bank simulation demonstrating thread synchronization using C++ threads, mutexes, condition variables, and semaphores.

## Overview

This program simulates a bank with:
- **3 Teller Threads**: Serve customers, access the manager for withdrawals, and use the safe
- **50 Customer Threads**: Randomly select transactions, wait in line, and complete their banking
- **Thread Synchronization**: Using semaphores, condition variables, and mutexes
- **Resource Management**: Safe (max 2 tellers), Manager (max 1 teller), Door (max 2 customers)

## Requirements

### Compiler
- **C++17** or later support required
- **clang++** (recommended for macOS) or **g++**
- POSIX threads support

### Operating System
- macOS, Linux, or Unix-like systems
- Tested on macOS with Apple Clang

## Compilation

### Using the Makefile (Recommended)

```bash
# Clean any previous builds
make clean

# Compile the program
make

# Compile and run
make run
```

### Manual Compilation

#### macOS (using clang++)
```bash
clang++ -std=c++17 -isysroot $(xcrun --show-sdk-path) \
        -I$(xcrun --show-sdk-path)/usr/include/c++/v1 \
        -Wall -Wextra -O2 \
        bank_simulation.cpp -o bank_simulation
```

#### Linux (using g++)
```bash
g++ -std=c++17 -pthread -Wall -Wextra -O2 \
    bank_simulation.cpp -o bank_simulation
```

## Running the Simulation

```bash
./bank_simulation
```

### Expected Output

The program will output detailed logs of all thread actions:

```
Bank Simulation Starting...
Teller 0: ready to serve
Teller 1: ready to serve
Teller 2: ready to serve
--- Bank is now OPEN ---
Customer 15 waits 45ms
Customer 3 waits 12ms
Customer 3: enters bank
Customer 3: gets in line
Customer 3 [Teller 0]: selects teller
...
```

The simulation continues until all 50 customers have been served, then outputs:
```
--- Bank is now CLOSED ---
All 50 customers have been served. Bank closing.
```

## Configuration

You can modify the simulation parameters in `bank_simulation.cpp`:

```cpp
// Constants (lines 22-23)
const int NUM_TELLERS = 3;      // Number of teller threads
const int NUM_CUSTOMERS = 50;   // Number of customer threads
```

## Implementation Details

### Key Components

#### 1. Semaphore Class
Custom semaphore implementation using `std::mutex` and `std::condition_variable`:
```cpp
class Semaphore {
    void acquire();  // Wait/P operation
    void release();  // Signal/V operation
};
```

#### 2. Thread Synchronization
- **Door Semaphore**: Limits entry to 2 customers simultaneously
- **Manager Semaphore**: Ensures only 1 teller accesses manager at a time
- **Safe Semaphore**: Allows maximum 2 tellers in safe simultaneously

#### 3. Customer Events Structure
Each customer has a dedicated event structure for bidirectional communication:
```cpp
struct CustomerEvents {
    std::shared_ptr<std::condition_variable> teller_ready;
    std::shared_ptr<std::condition_variable> transaction_given;
    std::shared_ptr<std::condition_variable> transaction_complete;
    std::shared_ptr<std::condition_variable> customer_left;
    // ... flags and transaction data
};
```

#### 4. Thread-Safe Operations
- **Print Logging**: Global mutex ensures output doesn't interleave
- **Customer Queue**: Protected by mutex for thread-safe access
- **Event Signaling**: Condition variables with predicate-based waiting

### Synchronization Flow

1. **Bank Opening**: All tellers signal ready → bank opens
2. **Customer Entry**: Through door semaphore (max 2 at once)
3. **Queuing**: Customer added to queue, teller notified
4. **Service**:
   - Teller asks for transaction
   - Customer provides transaction type
   - If withdrawal: Teller accesses manager (5-30ms)
   - Teller accesses safe (10-50ms)
   - Teller signals completion
5. **Exit**: Customer leaves, teller serves next customer

## Troubleshooting

### Compilation Errors

**Error**: `'thread' file not found`
- **Solution**: Ensure C++17 support and correct SDK path (macOS)
```bash
clang++ -std=c++17 -isysroot $(xcrun --show-sdk-path) ...
```

**Error**: `undefined reference to pthread_create`
- **Solution**: Add `-pthread` flag (Linux)
```bash
g++ -std=c++17 -pthread bank_simulation.cpp -o bank_simulation
```

### Runtime Issues

**Issue**: Deadlock or program hangs
- Check that all condition variables are properly notified
- Verify semaphore counts are correct
- Ensure all threads properly release resources

**Issue**: Garbled output
- The print_lock mutex should prevent this
- Check that all prints use the thread-safe print_log function

## Testing

### Test with Different Customer Counts
Modify `NUM_CUSTOMERS` constant and recompile:

```bash
# Edit bank_simulation.cpp: const int NUM_CUSTOMERS = 10;
make clean && make
./bank_simulation
```

### Verify Output Format
Each action should follow the format:
```
THREAD_TYPE ID [THREAD_TYPE ID]: MESSAGE
```

Examples:
- `Customer 5 [Teller 2]: selects teller`
- `Teller 1 [Customer 10]: asks for transaction`

## Performance Considerations

- **Random Delays**: Simulate realistic timing
  - Customer wait: 0-100ms
  - Manager interaction: 5-30ms
  - Safe transaction: 10-50ms
  
- **Concurrency**: 
  - Up to 3 tellers working simultaneously
  - Up to 2 tellers in safe at once
  - Up to 2 customers entering at once

## Code Structure

```
bank_simulation.cpp (340 lines)
├── Semaphore Class (lines 26-47)
├── Global Variables & Synchronization Primitives (lines 49-73)
├── Helper Functions
│   ├── print_log() - Thread-safe logging (lines 75-99)
│   └── random_sleep() - Random delay generator (lines 101-105)
├── Thread Functions
│   ├── teller_thread() - Teller logic (lines 107-192)
│   └── customer_thread() - Customer logic (lines 194-284)
└── main() - Program initialization (lines 286-338)
```

## Differences from Python Version

1. **Memory Management**: Uses `shared_ptr` for automatic cleanup
2. **Synchronization**: Custom Semaphore class instead of built-in
3. **Events**: Condition variables instead of Event objects
4. **Type Safety**: Strong typing with compile-time checks
5. **Performance**: Generally faster execution due to compiled nature

## Author Notes

This implementation follows the OS Project 2 specifications:
- Proper thread synchronization without deadlocks
- Correct resource access patterns
- Formatted output for easy verification
- Clean shutdown after all customers served

## License

Educational project for Operating Systems coursework.

