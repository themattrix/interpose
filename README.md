Interpose
=========

This program will generate the code for _interposing_ (intercepting) library calls based upon a given C header file.

For a quick demo, run:
```bash
$ make demo
```

In this demo, the files `test/interpose_lib_int_args.cpp` (the 'lib' file) and `test/interpose_usr_int_args.cpp` (the 'usr' file) will be generated then compiled into the shared library `libinterpose_int_args.so` (`.dylib` on OS X).

The output should contain something like:
<pre>
[1338250882.859208][call].......... extract_int_args()
[1338250882.859327][done][0.000119] extract_int_args()
[1338250882.859373][call].......... add_int_args()
[1338250882.859380][done][0.000007] add_int_args()
[1338250882.859412][call].......... join_int_args()
[1338250882.859430][done][0.000018] join_int_args()
[1338250882.859457][call].......... release_int_args()
[1338250882.859462][done][0.000005] release_int_args()
5 + 456 + 23 + 99 + 0 + -100 = 483
</pre>

What's happening here? All calls to this test library were interposed by our custom library. In this simple example the API calls are timestamped. All `[call]` and `[done]` lines contain a precise seconds-since-epoc timestamp plus the name of the function being called. `[done]` lines also contain a duration (in seconds) for that call.

_Without_ the interposing library loaded, the application output contains just the final line:
<pre>
5 + 456 + 23 + 99 + 0 + -100 = 483
</pre>

Let's look at the `extract_int_args()` function declaration in `test/int_args.h`:
```C
int extract_int_args(int argc, char *argv[], int **args);
```

By default, the following C++11 code will be generated as part of the 'usr' file for `extract_int_args()`:
```C++
template<typename Function>
auto extract_int_args(Function original, int argc, char *argv[], int **args) -> int
{
   return timestamp(original(argc, argv, args));
}
```
_The function `timestamp()` is syntactic sugar defined in the generated 'lib' file. It timestamps the supplied function before and after it's called._

The goal is to make the 'usr' file as simple as possible by abstracting all of the dirty work into the 'lib' file. The original function is located and sent as the first argument into the wrapper function. If you want to do something special, this function is the place to do it. Possibilities include printing the arguments, modifying the arguments, returning an unexpected value, delaying, _not_ printing time-stamps, etc.

For example, let's add some code to print the arguments to `extract_int_args()`:
```C++
#include <iostream>
#include <sstream>

template<typename Function>
auto extract_int_args(Function original, int argc, char *argv[], int **args) -> int
{
   typedef std::ostringstream oss;

   std::cout
      << "[INTERCEPTED] "
      << __func__
      << '('
      << argc
      << ", {"
      << [&]{oss o; for(int i{}; i < argc; ++i){if(i) o << ", "; o << argv[i];} return o.str();}()
      << "}, "
      << static_cast<void *>(args)
      << ")\n";

   return timestamp(original(argc, argv, args));
}
```
...then we'll build the new interposing library:
```bash
$ make interpose-lib HEADER=test/int_args.h
```
    
...and try it out:
```bash
$ make do-interpose HEADER=test/int_args.h APP="test/app 5 456 23 99 0 -100"
```

<pre>
<b>[INTERCEPTED] extract_int_args(6, {5, 456, 23, 99, 0, -100}, 0x7fff5fbff5e0)</b>
[1338251018.159458][call].......... extract_int_args()
[1338251018.159486][done][0.000028] extract_int_args()
[1338251018.159511][call].......... add_int_args()
[1338251018.159518][done][0.000007] add_int_args()
[1338251018.159539][call].......... join_int_args()
[1338251018.159553][done][0.000014] join_int_args()
[1338251018.159572][call].......... release_int_args()
[1338251018.159581][done][0.000009] release_int_args()
5 + 456 + 23 + 99 + 0 + -100 = 483
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