CC=gcc
CFLAGS=-Wall -Wextra -g3
OFLAGS=-O2 -march=native -mtune=native
#-O2 -Os

LIBS=-lX11
EXE=status

.PHONY: all memcheck

build: logger.o
	$(CC) $(CFLAGS) $(OFLAGS) $? -o $(EXE) $(LIBS)

%.o: %.c
	$(CC) $(CFLAGS) $(OFLAGS) -c $^ -o $@

clean:
	rm -Rf $(EXE) *.o

memcheck: build
	LOGGER_DIR=memcheck valgrind --track-origins=yes --leak-check=full --show-leak-kinds=all -s ./$(EXE)
	rm -rf memcheck