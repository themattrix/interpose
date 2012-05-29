CC     = gcc
FLAGS  = -fPIC -Wall -Werror -std=c99
UNAME := $(shell uname)

ifeq ($(UNAME),Darwin)
   SHARED   = -dynamiclib
   SO       = dylib
   LIB_NAME = libint_args.$(SO)
   LIBS     = $(LIB_NAME)
else
   SHARED   = -shared
   SO       = so
   LIB_NAME = libint_args.$(SO)
   LIBS     = -L. -lint_args
endif

all: add

lib-int-args:
	@echo
	@echo "===================================================[ Compiling 'int_args.c' ]==="
	$(CC) $(SHARED) $(FLAGS) -o $(LIB_NAME) int_args.c

add: lib-int-args
	@echo
	@echo "========================================================[ Compiling 'app.c' ]==="
	$(CC) $(FLAGS) -o add add.c $(LIBS)

clean:
	@echo
	@echo "====================================================[ Cleaning the test API ]==="
	rm -f $(LIB_NAME)
	rm -f add

.PHONY: lib-int-args add clean
