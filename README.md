Interpose
=========

This program will generate the code for _interposing_ (intercepting) library calls based upon a given C header file.

For a quick demo, run:
    
    $ make test-demo

Files `test_api/interpose_lib_test_api.cpp` (the 'lib' file) and `test_api/interpose_usr_test_api.cpp` (the 'usr' file) will be generated then compiled into the shared library `libinterpose_test_api.so` (`.dylib` on OS X).

The output should contain something like:
<pre>
<b>[1337999139.711980][call] api_call()</b>
  libtest_api::api_call(int, char **)
<b>[1337999139.712053][done][0.000073] api_call()</b>
result[1] = 4
<b>[1337999139.712060][call] api_simple()</b>
  libtest_api::api_simple()
<b>[1337999139.712074][done][0.000014] api_simple()</b>
<b>[1337999139.712078][call] api_call()</b>
   libtest_api::api_call(int, char **)
<b>[1337999139.712080][done][0.000002] api_call()</b>
result[2] = 4
</pre>

What's happening here? All calls to this test library were interposed by our custom library. In this simple example the API calls are timestamped. All `[call]` and `[done]` lines contain a precise seconds-since-epoc timestamp plus the name of the function being called. `[done]` lines also contain a duration (in seconds) for that call.

Without the interposing library loaded, the application output looks like this:

      libtest_api::api_call(int, char **)
    result[1] = 4
      libtest_api::api_simple()
      libtest_api::api_call(int, char **)
    result[2] = 4

Let's look at the `api_call()` function declaration:
```C
int api_call(int argc, char **argv);
```

By default, the following C++11 code will be generated as part of the 'usr' file for `api_call()`:
```C++
template<typename Function>
auto api_call(Function original, int argc, char **argv) -> int
{
   return original(argc, argv);
}
```

The timestamping and other guts are handled by a proxying function within the 'lib' file. The goal is to make the 'usr' file as simple as possible by abstracting all of the dirty work into the 'lib' file. The original function is located and sent as the first argument into the wrapper function. If you want to do something special, this function is the place to do it. Possibilities include printing the arguments, modifying the arguments, returning an unexpected value, delaying, etc.

For example, let's add some code to print the arguments to `api_call()`:
```C++
#include <iostream>
#include <sstream>

template<typename Function>
auto api_call(Function original, int argc, char **argv) -> int
{
   typedef std::ostringstream oss;

   std::cout
      << "   [INTERCEPTED] api_call("
      << argc
      << ", {"
      << [&]{oss o; for(int i{}; i < argc; ++i){if(i) o << ", "; o << argv[i];} return o.str();}()
      << "})\n";

   return original(argc, argv);
}
```
...then we'll build the new interposing library:
    
    $ make interpose-lib HEADER=test_api/test_api.h
    
...and try it out:

    $ make do-interpose HEADER=test_api/test_api.h APP="test_api/test_app one two three"

<pre>
[1338005593.315879][call] api_call()
   <b>[INTERCEPTED] api_call(4, {test_api/test_app, one, two, three})</b>
   libtest_api::api_call(int, char **)
[1338005593.316055][done][0.000176] api_call()
result[1] = 4
[1338005593.316070][call] api_simple()
   libtest_api::api_simple()
[1338005593.316092][done][0.000022] api_simple()
[1338005593.316099][call] api_call()
   <b>[INTERCEPTED] api_call(4, {test_api/test_app, one, two, three})</b>
   libtest_api::api_call(int, char **)
[1338005593.316114][done][0.000015] api_call()
result[2] = 4
</pre>

Requirements
------------

Requires:
- C99 compatible compiler
- [for C++ support] C++11 (0x)-compatible compiler
- Python 2.7 and pycparser (available in PIP)
- Linux or OS X

Notes
-----

By default, interposing C++ code is generated and the time-stamps are calculated with `<chrono>`. To drop `<chrono>` and fall back to `<sys/time.h>`, specify the `NO_CHRONO=1` flag. To fall back to C instead of C++, specify the `NO_CPP=1` flag (which implies `NO_CHRONO`).

For OS X users: In addition to specifying `HEADER`, you must also specify `API_LIB` because the method for finding the original library call requires the original library (unlike on Linux).

For users of compilers in non-standard locations: You can specify `CC` as the path to the C++ compiler.
