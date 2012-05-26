Interpose
=========

For a quick demo, run:
    
    $ make test-demo

Requires:
- C99 compatible compiler
- [for C++ support] C++11 (0x)-compatible compiler
- Python 2.7 and pycparser (available in PIP)
- Linux or OS X

Note for OS X users: In addition to specifying `HEADER`, you must also specify `API_LIB` because the method for finding the original library call requires the original library (unlike on Linux).

Note for users of compilers in non-standard locations (like me): You can specify `CC` as the path to the C++ compiler.

Otherwise, run:
    
    $ make interpose-src HEADER='api_header.h'

That will create a few files based on the header filename; in this case:
    
    interpose_lib_api_header.cpp
    interpose_usr_api_header.cpp

The 'usr' C++ file should be all you have to modify for deciding what to do with each intercepted call.

After you're done modifying the 'usr' file, run:
    
    $ make interpose-lib HEADER='api_header.h'

If no compilation errors occurred, then an interposing library should have been built. To use it with an application that uses the intercepted API, run:
    $ make do-interpose HEADER='api_header.h' APP='api_test_app'

To delete the generated library and clean the test directory, run:
    
    $ make clean HEADER=...

(`HEADER` is still required here because the header name determines the generated file names.)

Note that the above command does not delete the generated (and possibly modified interposer files. To clean everything including the generated source files, run:
    
    $ make clean-all HEADER=...

By default, interposing C++ code is generated and the time-stamps are calculated with `<chrono>`. To drop `<chrono>` and fall back to `<sys/time.h>`, specify the `NO_CHRONO=1` flag. To fall back to C instead of C++, specify the `NO_CPP=1` flag (implies `NO_CHRONO`).
