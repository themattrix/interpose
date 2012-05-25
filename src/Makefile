ifeq ($(HEADER),)
   HEADER = test_api/test_api.h
   $(warning No header file specified with "HEADER=...", defaulting to "HEADER=$(HEADER)")
endif

# Use C++ by default, unless "NO_CPP" is specified
ifeq ($(NO_CPP),)
   EXT           = cpp
   CC           ?= g++
   LANG_STD     ?= c++0x
   LIB_TEMPLATE ?= interpose_lib.cpp.template
   USR_TEMPLATE ?= interpose_usr.cpp.template
else
   EXT           = c
   NO_CHRONO     = 1
   CC           ?= gcc
   LANG_STD     ?= c99
   LIB_TEMPLATE ?= interpose_lib.c.template
   USR_TEMPLATE ?= interpose_usr.c.template
endif

# When using C++, use <chrono> by default unless "NO_CHRONO" is specified
ifeq ($(NO_CHRONO),)
   CHRONO_DEF = -DUSE_CHRONO
   CHRONO_LIB = -lstdc++
endif

HEADER_DIR  = $(shell dirname "$(HEADER)")
HEADER_DIR ?= .
HEADER_BASE = $(shell basename "$(HEADER)" .h)

FLAGS ?= -fPIC -Wall -Werror -std=$(LANG_STD) $(CFLAGS)

UNAME := $(shell uname)

ifeq ($(UNAME),Darwin)
   ifeq ($(API_LIB),)
      API_LIB = test_api/libtest_api.dylib
      $(warning No library file specified with "API=LIB=..." (required on OS X), defaulting to "API_LIB=$(API_LIB)")
   endif
   SHARED        = -dynamiclib
   SO            = dylib
   INTERPOSE_LIB = $(HEADER_DIR)/libinterpose_$(HEADER_BASE).$(SO)
   INTERPOSE_SRC = $(HEADER_DIR)/interpose_lib_$(HEADER_BASE).$(EXT)
   PRELOAD       = DYLD_LIBRARY_PATH=$(HEADER_DIR) DYLD_FORCE_FLAT_NAMESPACE=1 DYLD_INSERT_LIBRARIES=$(INTERPOSE_LIB)
   DEFINES       = $(CHRONO_DEF)
   LIBS          = -ldl $(CHRONO_LIB)
else
   ifeq ($(API_LIB),)
      API_LIB = ""
   endif
   SHARED        = -shared
   SO            = so
   INTERPOSE_LIB = $(HEADER_DIR)/libinterpose_$(HEADER_BASE).$(SO)
   INTERPOSE_SRC = $(HEADER_DIR)/interpose_lib_$(HEADER_BASE).$(EXT)
   PRELOAD       = LD_LIBRARY_PATH=$(HEADER_DIR) LD_PRELOAD=$(INTERPOSE_LIB)
   DEFINES       = -D_GNU_SOURCE $(CHRONO_DEF)
   LIBS          = -ldl $(CHRONO_LIB)
endif

TEST_CMD      ?= $(PRELOAD) test_api/test_app one two three

INTERPOSE_CMD ?= ./interpose.py $(HEADER) $(API_LIB) lib=$(LIB_TEMPLATE) usr=$(USR_TEMPLATE)

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

clean-src:
	@echo
	@echo "==========================================================[ Cleaning source ]==="
	rm -f $(INTERPOSE_SRC)
	rm -f $(HEADER_DIR)/interpose_usr_$(HEADER_BASE).$(EXT)

clean-test:
	make -C test_api clean
