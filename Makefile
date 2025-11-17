# Makefile for Bank/Teller Simulation

CXX = clang++
SDK_PATH = $(shell xcrun --show-sdk-path)
CXXFLAGS = -std=c++17 -isysroot $(SDK_PATH) -I$(SDK_PATH)/usr/include/c++/v1 -Wall -Wextra -O2
TARGET = bank_simulation
SOURCE = bank_simulation.cpp

.PHONY: all clean test run

all: $(TARGET)

$(TARGET): $(SOURCE)
	@echo "Compiling bank simulation..."
	@$(CXX) $(CXXFLAGS) $(SOURCE) -o $(TARGET)
	@echo "Compilation successful!"

run: $(TARGET)
	./$(TARGET)

test: $(TARGET)
	@echo "Running with 5 customers..."
	@./$(TARGET) | head -80

clean:
	rm -f $(TARGET)
	@echo "Cleaned build files."

.DEFAULT_GOAL := all

