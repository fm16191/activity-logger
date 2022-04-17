CC=gcc
CFLAGS=-Wall -Wextra
OFLAGS=-march=native -mtune=native -O2 -Os

TARGET=target
LIBS= -lX11
EXE=status

.PHONY: all mem

all: logger.o
	$(CC) $(CFLAGS) $(OFLAGS) $? -o $(EXE) $(LIBS)

%.o: %.c
	$(CC) $(CFLAGS) $(OFLAGS) -c $^ -o $@

clean:
	rm -Rf $(TARGET) $(EXE)
