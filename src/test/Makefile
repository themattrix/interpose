CC = gcc
FLAGS = -fPIC -Wall -Werror -std=c99
UNAME := $(shell uname)

ifeq ($(UNAME),Darwin)
SHARED = -dynamiclib
SO = dylib
LIB_NAME = libtest_api.$(SO)
LIBS = $(LIB_NAME)
else
SHARED = -shared
SO = so
LIB_NAME = libtest_api.$(SO)
LIBS = -L. -ltest_api
endif

all: test-app

test-api:
	@echo
	@echo "===================================================[ Compiling 'test_api.c' ]==="
	gcc $(SHARED) $(FLAGS) -o $(LIB_NAME) test_api.c

test-app: test-api
	@echo
	@echo "===================================================[ Compiling 'test_app.c' ]==="
	gcc $(FLAGS) -o test_app test_app.c $(LIBS)

clean:
	@echo
	@echo "========================================================[ Cleaning test_api ]==="
	rm -f $(LIB_NAME)
	rm -f test_app
