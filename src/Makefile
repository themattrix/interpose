ifeq ($(HEADER),)
   HEADER = test/int_args.h
   $(warning No header file specified with "HEADER=...", defaulting to "HEADER=$(HEADER)")
endif

EXT           = cpp
CXX          ?= g++
LANG_STD     ?= c++0x
LIB_TEMPLATE ?= interpose_lib.cpp.template
USR_TEMPLATE ?= interpose_usr.cpp.template

STD_LIB ?= -lstdc++

# Use <chrono> by default unless "NO_CHRONO" is specified
ifeq ($(NO_CHRONO),)
   CHRONO_DEF = -DUSE_CHRONO
   CHRONO_LIB = $(STD_LIB)
endif

HEADER_DIR  = $(shell dirname "$(HEADER)")
HEADER_DIR ?= .
HEADER_BASE = $(shell basename "$(HEADER)" .h)

DEST  ?= $(HEADER_DIR)

FLAGS ?= -fPIC -Wall -Werror -std=$(LANG_STD) $(CFLAGS)

UNAME := $(shell uname)

ifeq ($(UNAME),Darwin)
   ifeq ($(API_LIB),)
      API_LIB = test/libint_args.dylib
      $(warning No library file specified with "API=LIB=..." (required on OS X), defaulting to "API_LIB=$(API_LIB)")
   endif
   SHARED        = -dynamiclib
   SO            = dylib
   INTERPOSE_LIB = $(DEST)/libinterpose_$(HEADER_BASE).$(SO)
   INTERPOSE_SRC = $(DEST)/interpose_lib_$(HEADER_BASE).$(EXT)
   PRELOAD       = DYLD_LIBRARY_PATH=$(DEST) DYLD_FORCE_FLAT_NAMESPACE=1 DYLD_INSERT_LIBRARIES=$(INTERPOSE_LIB)
   DEFINES       = $(CHRONO_DEF)
   LIBS          = -ldl $(CHRONO_LIB)
else
   ifeq ($(API_LIB),)
      API_LIB = ""
   endif
   SHARED        = -shared
   SO            = so
   INTERPOSE_LIB = $(DEST)/libinterpose_$(HEADER_BASE).$(SO)
   INTERPOSE_SRC = $(DEST)/interpose_lib_$(HEADER_BASE).$(EXT)
   PRELOAD       = LD_LIBRARY_PATH=$(DEST) LD_PRELOAD=$(INTERPOSE_LIB)
   DEFINES       = -D_GNU_SOURCE $(CHRONO_DEF)
   LIBS          = -ldl $(CHRONO_LIB)
endif

APP           ?= test/add 5 456 23 99 0 -100

TEST_CMD      ?= $(PRELOAD) $(APP)

INTERPOSE_CMD ?= ./interpose.py $(DEST) $(HEADER) $(API_LIB) lib=$(LIB_TEMPLATE) usr=$(USR_TEMPLATE)

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
	$(CXX) $(SHARED) $(FLAGS) $(DEFINES) -o $(INTERPOSE_LIB) $(INTERPOSE_SRC) $(LIBS)

do-interpose:
	@echo
	@echo "=================================================[ Running interposing code ]==="
	@$(PRELOAD) $(APP)

test:
	@echo
	@echo "====================================================[ Building the test API ]==="
	make -C test
	@echo
	@echo "=============================================================[ Running test ]==="
	@echo $(TEST_CMD)
	@echo
	@echo "===[ Results ]:"
	@$(TEST_CMD) 2>&1 | sed 's/^/   /'

demo: interpose-src interpose-lib test

clean-lib:
	@echo
	@echo "=======================================================[ Cleaning libraries ]==="
	rm -f $(INTERPOSE_LIB)

clean-src:
	@echo
	@echo "==========================================================[ Cleaning source ]==="
	rm -f $(INTERPOSE_SRC)
	rm -f $(DEST)/interpose_usr_$(HEADER_BASE).$(EXT)

clean-test:
	make -C test clean

clean-all: clean-lib clean-src clean-test

clean: clean-lib

.PHONY: test
