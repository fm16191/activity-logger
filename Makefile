CC=gcc
CFLAGS=-Wall -Wextra -g3
OFLAGS=-march=native -mtune=native
#-O2 -Os

LIBS= -lX11
EXE=status

.PHONY: all mem

build: logger.o
	$(CC) $(CFLAGS) $(OFLAGS) $? -o $(EXE) $(LIBS)

%.o: %.c
	$(CC) $(CFLAGS) $(OFLAGS) -c $^ -o $@

clean:
	rm -Rf $(EXE) *.o

mem: build
	valgrind --track-origins=yes --leak-check=full --show-leak-kinds=all -s ./$(EXE)