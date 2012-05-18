
UNAME := $(shell uname)

CC = gcc

ifeq ($(UNAME),Darwin)
	SHARED = -dynamiclib
	SO = dylib
	LIBS = libtest_api.dylib
	PRELOAD = DYLD_FORCE_FLAT_NAMESPACE=1 DYLD_INSERT_LIBRARIES=./libinterpose_test_api.h.$(SO)
else
	SHARED = -shared
	SO = so
	LIBS = -L. -ltest_api
	PRELOAD = LD_LIBRARY_PATH=. LD_PRELOAD=./libinterpose_test_api.h.$(SO)
endif

TEST_CMD = $(PRELOAD) ./test_app one two three

all: test-app

test-api:
	@echo
	@echo "===================================================[ Compiling 'test_api.c' ]==="
	$(CC) $(SHARED) -fPIC -Wall -Werror -std=c99 -o libtest_api.$(SO) test_api.c

test-app: test-api
	@echo
	@echo "===================================================[ Compiling 'test_app.c' ]==="
	$(CC) -Wall -Werror -std=c99 -o test_app test_app.c $(LIBS)

test: test-app
	@echo
	@echo "=============================================================[ Running test ]==="
	@echo $(TEST_CMD)
	@echo
	@echo "===[ Results ]:"
	@$(TEST_CMD) 2>&1 | sed 's/^/   /'

clean:
	@echo
	@echo "=================================================================[ Cleaning ]==="
	rm -f libtest_api.so
	rm -f test_app
