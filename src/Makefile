ifeq ($(HEADER),)
$(error No header file specified with "HEADER=...")
endif

HEADER_DIR  = $(shell dirname "$(HEADER)")
HEADER_DIR ?= .
HEADER_BASE = $(shell basename "$(HEADER)" .h)

CC = g++
FLAGS = -fPIC -Wall -Werror -std=c++0x

UNAME := $(shell uname)

ifeq ($(UNAME),Darwin)
SHARED = -dynamiclib
SO = dylib
INTERPOSE_LIB = $(HEADER_DIR)/libinterpose_$(HEADER_BASE).$(SO)
INTERPOSE_SRC = $(HEADER_DIR)/interpose_lib_$(HEADER_BASE).cpp
PRELOAD = DYLD_FORCE_FLAT_NAMESPACE=1 DYLD_INSERT_LIBRARIES=$(INTERPOSE_LIB)
DEFINES =
LIBS = -ldl
else
SHARED = -shared
SO = so
INTERPOSE_LIB = $(HEADER_DIR)/libinterpose_$(HEADER_BASE).$(SO)
INTERPOSE_SRC = $(HEADER_DIR)/interpose_lib_$(HEADER_BASE).cpp
PRELOAD = LD_LIBRARY_PATH=$(HEADER_DIR) LD_PRELOAD=$(INTERPOSE_LIB)
DEFINES = -D_GNU_SOURCE
LIBS = -ldl
endif

TEST_CMD = $(PRELOAD) test_api/test_app one two three

INTERPOSE_CMD = ./interpose.py $(HEADER)

all: interpose-src test

interpose-src:
	@echo
	@echo "==============================================[ Generating interposing code ]==="
	@echo $(INTERPOSE_CMD)
	@echo
	@echo "===[ Results ]:"
	@$(INTERPOSE_CMD) 2>&1 | sed 's/^/   /'

interpose-lib:
	@echo
	@echo "===========================================[ Generating interposing library ]==="
	$(CC) $(SHARED) $(FLAGS) $(DEFINES) -o $(INTERPOSE_LIB) $(INTERPOSE_SRC) $(LIBS)

do-interpose:
	@echo
	@echo "=================================================[ Running interposing code ]==="
	@$(PRELOAD) $(APP)

test:
	@echo
	@echo "====================================================[ Building the test API ]==="
	make -C test_api
	@echo
	@echo "=============================================================[ Running test ]==="
	@echo $(TEST_CMD)
	@echo
	@echo "===[ Results ]:"
	@$(TEST_CMD) 2>&1 | sed 's/^/   /'

test-demo: interpose-src interpose-lib test

clean: clean-lib

clean-all: clean-lib clean-src clean-test

clean-lib:
	@echo
	@echo "=======================================================[ Cleaning libraries ]==="
	rm -f $(INTERPOSE_LIB)
	rm -f $(TEST_LIB)

clean-src:
	@echo
	@echo "==========================================================[ Cleaning source ]==="
	rm -f $(INTERPOSE_SRC)
	rm -f $(HEADER_DIR)/interpose_usr_$(HEADER_BASE).cpp

clean-test:
	make -C test_api clean
