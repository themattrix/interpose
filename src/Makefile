
UNAME := $(shell uname)

ifeq ($(UNAME),Darwin)
	SHARED = -dynamiclib
	SO = dylib
	LIBS = libtest_api.dylib
	PRELOAD = DYLD_FORCE_FLAT_NAMESPACE=1 DYLD_INSERT_LIBRARIES=./libinterpose_test_api.h.$(SO)
else
	SHARED = -shared
	SO = so
	LIBS = -L. -ltest_api
	PRELOAD = LD_PRELOAD=./libinterpose_test_api.h.$(SO)
endif

all: test-app

test-api:
	gcc $(SHARED) -fPIC -Wall -Werror -std=c99 -o libtest_api.$(SO) test_api.c

test-app: test-api
	gcc -Wall -Werror -std=c99 -o test_app test_app.c $(LIBS)

test: test-api
	$(PRELOAD) ./test_app one two three

clean:
	rm -f libtest_api.so
	rm -f test_app
