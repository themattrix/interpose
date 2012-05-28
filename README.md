Interpose
=========

This program will generate the code for _interposing_ (intercepting) library calls based upon a given C header file.

For a quick demo, run:
    
    $ make demo

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

_Without_ the interposing library loaded, the application output looks like this:

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
   return timestamp(original(argc, argv));
}
```

The goal is to make the 'usr' file as simple as possible by abstracting all of the dirty work into the 'lib' file. The original function is located and sent as the first argument into the wrapper function. If you want to do something special, this function is the place to do it. Possibilities include printing the arguments, modifying the arguments, returning an unexpected value, delaying, _not_ printing time-stamps, etc.

For example, let's add some code to print the arguments to `api_call()`:
```C++
#include <iostream>
#include <sstream>

template<typename Function>
auto api_call(Function original, int argc, char **argv) -> int
{
   typedef std::ostringstream oss;

   std::cout
      << "[INTERCEPTED] api_call("
      << argc
      << ", {"
      << [&]{oss o; for(int i{}; i < argc; ++i){if(i) o << ", "; o << argv[i];} return o.str();}()
      << "})\n";

   return timestamp(original(argc, argv));
}
```
...then we'll build the new interposing library:
    
    $ make interpose-lib HEADER=test/test_api.h
    
...and try it out:

    $ make do-interpose HEADER=test/test_api.h APP="test/test_app one two three"

<pre>
<b>[INTERCEPTED] api_call(4, {test_api/test_app, one, two, three})</b>
[1338087686.971837][call] api_call()
libtest_api::api_call(int, char **)
[1338087686.971861][done][0.000024] api_call()
result[1] = 4
[1338087686.971889][call] api_simple()
libtest_api::api_simple()
[1338087686.971899][done][0.000010] api_simple()
<b>[INTERCEPTED] api_call(4, {test_api/test_app, one, two, three})</b>
[1338087686.971915][call] api_call()
libtest_api::api_call(int, char **)
[1338087686.971923][done][0.000008] api_call()
result[2] = 4
</pre>

Requirements
------------
- Python 2.6 and [pycparser](http://code.google.com/p/pycparser/) (also [available in pip](http://pypi.python.org/pypi/pip)) for generating the interposing code
- C++11-compatible compiler for compiling the interposing code
- C99-compatible compiler for compiling the demo
- Linux or OS X

Notes
-----

By default, the time-stamps are calculated with `<chrono>`. To drop `<chrono>` and fall back to `<sys/time.h>`, specify the `NO_CHRONO=1` flag. Doing this avoids a dependency on libstdc++.

For OS X users: In addition to specifying `HEADER`, you must also specify `API_LIB` because the method for finding the original library call requires the original library (unlike on Linux).

For users of compilers in non-standard locations: You can specify `CXX` as the path to the C++ compiler.
