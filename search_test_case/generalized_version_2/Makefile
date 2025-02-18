# Variables
CC = gcc
CFLAGS = -Wall -Wextra
EXEC = search_test
SRC = search_module.c search_test.c

# The default rule
all: $(EXEC)

# Rule to compile the program
$(EXEC): $(SRC)
	$(CC) -o $(EXEC) $(SRC) $(CFLAGS)

# Clean up compiled files
clean:
	rm -f $(EXEC)

# Run the program
run: $(EXEC)
	./$(EXEC)

.PHONY: all clean run

