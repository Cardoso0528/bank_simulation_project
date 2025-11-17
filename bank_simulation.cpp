/**
 * Bank/Teller Simulation - OS Project 2
 * Simulates a bank with 3 tellers and 50 customers using threads and semaphores.
 * 
 * Compile with: g++ -std=c++20 -pthread bank_simulation.cpp -o bank_simulation
 * Or if C++20 not available: g++ -std=c++17 -pthread bank_simulation.cpp -o bank_simulation
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <map>
#include <random>
#include <chrono>
#include <atomic>
#include <string>
#include <sstream>
#include <iomanip>

// Constants
const int NUM_TELLERS = 3;
const int NUM_CUSTOMERS = 50;

// Simple Semaphore implementation (for compatibility)
class Semaphore {
private:
    std::mutex mtx;
    std::condition_variable cv;
    int count;

public:
    explicit Semaphore(int initial_count) : count(initial_count) {}

    void acquire() {
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [this] { return count > 0; });
        --count;
    }

    void release() {
        std::lock_guard<std::mutex> lock(mtx);
        ++count;
        cv.notify_one();
    }
};

// Customer events structure for synchronization
struct CustomerEvents {
    std::shared_ptr<std::condition_variable> teller_ready;
    std::shared_ptr<std::condition_variable> transaction_given;
    std::shared_ptr<std::condition_variable> transaction_complete;
    std::shared_ptr<std::condition_variable> customer_left;
    std::shared_ptr<std::mutex> mtx;
    std::atomic<bool> teller_ready_flag{false};
    std::atomic<bool> transaction_given_flag{false};
    std::atomic<bool> transaction_complete_flag{false};
    std::atomic<bool> customer_left_flag{false};
    std::string transaction_type;
    
    CustomerEvents() {
        teller_ready = std::make_shared<std::condition_variable>();
        transaction_given = std::make_shared<std::condition_variable>();
        transaction_complete = std::make_shared<std::condition_variable>();
        customer_left = std::make_shared<std::condition_variable>();
        mtx = std::make_shared<std::mutex>();
    }
};

// Global synchronization primitives
Semaphore door_semaphore(2);      // Max 2 customers entering at once
Semaphore manager_semaphore(1);   // Max 1 teller with manager
Semaphore safe_semaphore(2);      // Max 2 tellers in safe

std::mutex print_lock;
std::mutex teller_ready_lock;
std::mutex customers_served_lock;
std::mutex customer_queue_lock;
std::mutex customer_map_lock;

int teller_ready_count = 0;
std::atomic<int> customers_served(0);
std::atomic<bool> bank_open(false);

std::queue<int> customer_queue;
std::condition_variable customer_queue_cv;
std::map<int, std::shared_ptr<CustomerEvents>> customer_events;
std::map<int, int> customer_teller_map;

// Random number generation
std::random_device rd;
std::mt19937 gen(rd());

// Thread-safe logging function
void print_log(const std::string& thread_type, int thread_id, 
               const std::string& other_type = "", int other_id = -1, 
               const std::string& message = "") {
    std::lock_guard<std::mutex> lock(print_lock);
    if (!other_type.empty() && other_id >= 0) {
        std::cout << thread_type << " " << thread_id << " [" 
                  << other_type << " " << other_id << "]: " << message << std::endl;
    } else {
        std::cout << thread_type << " " << thread_id << ": " << message << std::endl;
    }
}

// Teller thread function
void teller_thread(int teller_id) {
    // Step 1: Signal ready
    {
        std::lock_guard<std::mutex> lock(teller_ready_lock);
        teller_ready_count++;
        print_log("Teller", teller_id, "", -1, "ready to serve");
        if (teller_ready_count == NUM_TELLERS) {
            bank_open = true;
        }
    }

    // Step 2: Loop until all customers served
    while (true) {
        // Check if all customers have been served
        if (customers_served >= NUM_CUSTOMERS) {
            break;
        }

        // Wait for a customer to approach
        int customer_id = -1;
        {
            std::unique_lock<std::mutex> lock(customer_queue_lock);
            if (customer_queue_cv.wait_for(lock, std::chrono::milliseconds(500),
                [&] { return !customer_queue.empty(); })) {
                customer_id = customer_queue.front();
                customer_queue.pop();
            } else {
                continue;
            }
        }

        // Store which teller is serving this customer
        {
            std::lock_guard<std::mutex> lock(customer_map_lock);
            customer_teller_map[customer_id] = teller_id;
        }

        // Get customer events
        std::shared_ptr<CustomerEvents> events = customer_events[customer_id];

        // Signal customer we're ready and ask for transaction
        {
            std::lock_guard<std::mutex> lock(*events->mtx);
            events->teller_ready_flag = true;
        }
        events->teller_ready->notify_one();
        print_log("Teller", teller_id, "Customer", customer_id, "asks for transaction");

        // Wait for customer to provide transaction
        {
            std::unique_lock<std::mutex> lock(*events->mtx);
            events->transaction_given->wait(lock, [events] { 
                return events->transaction_given_flag.load(); 
            });
            events->transaction_given_flag = false;
        }

        std::string transaction_type = events->transaction_type;

        // If withdrawal, go to manager
        if (transaction_type == "WITHDRAWAL") {
            print_log("Teller", teller_id, "Customer", customer_id, "going to manager");
            manager_semaphore.acquire();
            print_log("Teller", teller_id, "Customer", customer_id, "interacting with manager");
            
            std::uniform_int_distribution<> dist(5, 30);
            std::this_thread::sleep_for(std::chrono::milliseconds(dist(gen)));
            
            print_log("Teller", teller_id, "Customer", customer_id, "done with manager");
            manager_semaphore.release();
        }

        // Go to safe
        print_log("Teller", teller_id, "Customer", customer_id, "going to safe");
        safe_semaphore.acquire();
        print_log("Teller", teller_id, "Customer", customer_id, "in safe");
        
        std::uniform_int_distribution<> dist(10, 50);
        std::this_thread::sleep_for(std::chrono::milliseconds(dist(gen)));
        
        print_log("Teller", teller_id, "Customer", customer_id, "done with safe");
        safe_semaphore.release();

        // Inform customer transaction is complete
        print_log("Teller", teller_id, "Customer", customer_id, "transaction complete");
        {
            std::lock_guard<std::mutex> lock(*events->mtx);
            events->transaction_complete_flag = true;
        }
        events->transaction_complete->notify_one();

        // Wait for customer to leave
        {
            std::unique_lock<std::mutex> lock(*events->mtx);
            events->customer_left->wait(lock, [events] { 
                return events->customer_left_flag.load(); 
            });
            events->customer_left_flag = false;
        }
    }
}

// Customer thread function
void customer_thread(int customer_id) {
    // Step 1: Decide transaction type
    std::uniform_int_distribution<> type_dist(0, 1);
    std::string transaction_type = (type_dist(gen) == 0) ? "DEPOSIT" : "WITHDRAWAL";

    // Step 2: Wait random time (0-100ms)
    std::uniform_int_distribution<> wait_dist(0, 100);
    int wait_time = wait_dist(gen);
    print_log("Customer", customer_id, "", -1, "waits " + std::to_string(wait_time) + "ms");
    std::this_thread::sleep_for(std::chrono::milliseconds(wait_time));

    // Wait for bank to open
    while (!bank_open) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    // Step 3: Enter bank (door allows max 2)
    door_semaphore.acquire();
    print_log("Customer", customer_id, "", -1, "enters bank");
    door_semaphore.release();

    // Step 4: Get in line
    print_log("Customer", customer_id, "", -1, "gets in line");

    // Create events for this customer
    auto events = std::make_shared<CustomerEvents>();
    events->transaction_type = transaction_type;
    customer_events[customer_id] = events;

    // Put self in customer queue
    {
        std::lock_guard<std::mutex> lock(customer_queue_lock);
        customer_queue.push(customer_id);
    }
    customer_queue_cv.notify_one();

    // Wait for a teller to be ready
    {
        std::unique_lock<std::mutex> lock(*events->mtx);
        events->teller_ready->wait(lock, [events] { 
            return events->teller_ready_flag.load(); 
        });
        events->teller_ready_flag = false;
    }

    // Get the teller ID assigned to this customer
    int teller_id;
    {
        std::lock_guard<std::mutex> lock(customer_map_lock);
        teller_id = customer_teller_map[customer_id];
    }

    // Step 5: Introduce self to teller
    print_log("Customer", customer_id, "Teller", teller_id, "selects teller");

    // Step 7: Tell teller the transaction
    print_log("Customer", customer_id, "Teller", teller_id, 
              "gives transaction (" + transaction_type + ")");
    {
        std::lock_guard<std::mutex> lock(*events->mtx);
        events->transaction_given_flag = true;
    }
    events->transaction_given->notify_one();

    // Step 8: Wait for transaction to complete
    {
        std::unique_lock<std::mutex> lock(*events->mtx);
        events->transaction_complete->wait(lock, [events] { 
            return events->transaction_complete_flag.load(); 
        });
        events->transaction_complete_flag = false;
    }

    // Step 9: Leave teller and bank
    print_log("Customer", customer_id, "Teller", teller_id, "leaves teller");
    {
        std::lock_guard<std::mutex> lock(*events->mtx);
        events->customer_left_flag = true;
    }
    events->customer_left->notify_one();

    print_log("Customer", customer_id, "", -1, "leaves bank");

    // Increment customers served
    customers_served++;

    // The shared_ptr will automatically clean up when no longer referenced
}

int main() {
    std::cout << "Bank Simulation Starting..." << std::endl;
    std::cout << "Opening bank with " << NUM_TELLERS << " tellers and " 
              << NUM_CUSTOMERS << " customers\n" << std::endl;

    // Create and start teller threads
    std::vector<std::thread> teller_threads;
    for (int i = 0; i < NUM_TELLERS; ++i) {
        teller_threads.emplace_back(teller_thread, i);
    }

    // Wait for bank to open
    while (!bank_open) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    std::cout << "\n--- Bank is now OPEN ---\n" << std::endl;

    // Create and start customer threads
    std::vector<std::thread> customer_threads;
    for (int i = 0; i < NUM_CUSTOMERS; ++i) {
        customer_threads.emplace_back(customer_thread, i);
    }

    // Wait for all customers to finish
    for (auto& t : customer_threads) {
        t.join();
    }

    // Wait for all tellers to finish
    for (auto& t : teller_threads) {
        t.join();
    }

    std::cout << "\n--- Bank is now CLOSED ---" << std::endl;
    std::cout << "All " << NUM_CUSTOMERS << " customers have been served." << std::endl;

    return 0;
}

