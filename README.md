Interpose
=========

This application will generate the code for _interposing_ (intercepting) library calls based upon a given C header file.

For a quick demo, run:
<pre>
$ make demo
</pre>

In this demo, the files `test/interpose_lib_int_args.cpp` (the 'lib' file) and `test/interpose_usr_int_args.cpp` (the 'usr' file) will be generated then compiled into the shared library `libinterpose_int_args.so` (`.dylib` on OS X).

The output should contain something like:
<pre>
1338250882.859327 [0.000119] extract_int_args()
1338250882.859380 [0.000007] add_int_args()
1338250882.859430 [0.000018] join_int_args()
1338250882.859462 [0.000005] release_int_args()
5 + 456 + 23 + 99 + 0 + -100 = 483
</pre>

What's happening here? All calls to this test library were interposed by our custom library. In this simple example the API calls are timestamped. Each timestamped line contains a precise seconds&ndash;since&ndash;epoc timestamp, the duration of the function call (in seconds), and the name of the function being called.

_Without_ the interposing library loaded, the application output contains just the final line:
<pre>
5 + 456 + 23 + 99 + 0 + -100 = 483
</pre>

The demo application&mdash;which produces the above output&mdash;is pretty simple:
<pre>
$ cat test/add.c
</pre>
```C
/* printf() */
#include <stdio.h>

/* *_int_args() */
#include "int_args.h"

int main(int argc, char *argv[])
{
   argc--;
   argv++;

   if(argc == 0)
   {
      printf("Error: no argument(s) specified; exiting\n");
      return 1;
   }

   int *args = NULL;

   if(extract_int_args(argc, argv, &args))
   {
      int sum = add_int_args(argc, args);

      char pretty[512] = {0};

      join_int_args(pretty, sizeof(pretty), argc, args, " + ");

      release_int_args(&args);

      printf("%s = %d\n", pretty, sum);
   }

   return 0;
}
```

It exercises the following public interface:
<pre>
$ cat test/int_args.h
</pre>
```C
/** Allocate an integer array equal in size to argc and fill it with integer
 ** representations of of the supplied command-line arguments.
 **/
int extract_int_args(int argc, char *argv[], int **args);

/** Return the sum of all integers in 'args'. 
 **/
int add_int_args(int argc, int *args);

/** Joins all of the integers in 'args' with 'delim'. For example, if delim is
 ** " + " and args is (9, 3, 6), the result would be "9 + 3 + 6". The result is
 ** appended to 'out'.
 **/
void join_int_args(char *out, int len, int argc, int *args, const char *delim);

/** Frees 'args' and sets it to NULL.
 **/
void release_int_args(int **args);
```

A block of C++11 code is generated as the 'usr' file for the above interface. These are the so&ndash;called _user-defined functions_:
<pre>
$ cat test/interpose_usr_int_args.cpp
</pre>
```C++
template<typename Function>
auto extract_int_args(Function original, int argc, char *argv[], int **args) -> int
{
   return timestamp(original(argc, argv, args));
}

template<typename Function>
auto add_int_args(Function original, int argc, int *args) -> int
{
   return timestamp(original(argc, args));
}

template<typename Function>
void join_int_args(Function original, char *out, int len, int argc, int *args, const char *delim)
{
   timestamp(original(out, len, argc, args, delim));
}

template<typename Function>
void release_int_args(Function original, int **args)
{
   timestamp(original(args));
}
```
_The `timestamp()` function is syntactic sugar defined in the generated 'lib' file. It timestamps the supplied function before and after it's called._

The goal is to make the 'usr' file as simple as possible by abstracting all of the dirty work into the 'lib' file. The original function is located and sent as the first argument into the wrapper function. If you want to do something special, this function is the place to make it happen. Possibilities include printing the arguments, modifying the arguments, returning an unexpected value, delaying, _not_ printing time-stamps, etc.

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
<pre>
$ make interpose-lib HEADER=test/int_args.h
</pre>

...and try it out:
<pre>
$ make do-interpose HEADER=test/int_args.h APP="test/app 5 456 23 99 0 -100"
</pre>

<pre>
<b>[INTERCEPTED] extract_int_args(6, {5, 456, 23, 99, 0, -100}, 0x7fff5fbff5e0)</b>
1338251018.159486 [0.000028] extract_int_args()
1338251018.159518 [0.000007] add_int_args()
1338251018.159553 [0.000014] join_int_args()
1338251018.159581 [0.000009] release_int_args()
5 + 456 + 23 + 99 + 0 + -100 = 483
</pre>

### Error checking

The `original` function pointer is checked against `nullptr` before each call to the user-defined function. If it is `nullptr` (like on the first call to that function), then the original function is queried and saved. _Whether the query returned a valid pointer **or not**_, the user function _will be called_. This is important.
    
    It is entirely up to the user-defined function to provide error handling for an invalid original function.

If the original function was not located and no action was taken in the user function, the program will probably segfault. In most cases, that's probably what you want as it may indicate an error in the environment.

Why not print an error message and exit, or call some user-specified handler for such an error? Consider the case where the user function has been modified to never call the original function; it wouldn't _matter_ if the original were invalid. Verification is left to the user functions for this reason. (In such a case, it would make even more sense to modify the 'lib' file such that the original function is never queried.)

### Environment variables

The makefile uses quite a few variables, some which may need to be redefined by the user. These are listed below. `HEADER` and `APP` have default values specifically for building and running the demo.

#### `HEADER`
_Default: `"test/int_args.h"`_

All generated file names revolve around this. For example, if the default header is used, the following files will be generated:

    test/interpose_lib_int_args.cpp
    test/interpose_usr_int_args.cpp
    test/libinterpose_int_args.so (.dylib on OS X)

If you want to generated code for anything other than the demo, you'll have to redefine this. This must be specified for almost every single make target, including the `clean` targets.

#### `DEST`
_Default: (`HEADER` directory)_

Optionally specify a destination directory for the interposing code and library. This is useful when `HEADER` is set to a system file, for example.

#### `API_LIB` (OS X only)
_Default: `"test/libint_args.dylib"`_

On OS X, you must specify `API_LIB` every time you specify `HEADER` because the method for finding the original library call requires the original library path (unlike on Linux).

#### `APP`
_Default: `"test/add 5 456 23 99 0 -100"`_

Used by the `do-interpose`, `test`, and `demo` targets.

#### `NO_CHRONO`
_Default: (unset)_

By default, the timestamps are calculated with `<chrono>`. To drop `<chrono>` and fall back to `<sys/time.h>`, specify `NO_CHRONO=1`. Doing this avoids a dependency on libstdc++.

#### `CXX`
_Default: `g++`_

C++ compiler path. Use this if your C++11-compatible compiler is not in your `PATH`.

#### `CC`
_Default: `gcc`_

C compiler path, only needed for compiling the demo. Use this if your C99-compatible compiler is not in your `PATH`.

Requirements
------------
- Python 2.6 and [pycparser](http://code.google.com/p/pycparser/) (also [available in pip](http://pypi.python.org/pypi/pip)) for generating the interposing code
- C++11-compatible compiler for compiling the interposing code (I've tested GCC 4.6.3, 4.7, and Clang 3.1)
- C99-compatible compiler for compiling the demo
- Linux or OS X

Q/A
---
> ##### Why generate C++ code instead of C code?

C++ allows for much less redundant code via templates. Templates also allow me to hide the original function type when passing it to the user functions. It's much nicer to deal with this:
```C++
Function original
```
than this:
```C
long long unsigned (*original)(wtf_t*[], int (*)(char, mander_t))
```

Truth be told, I _used_ to allow `NO_CPP=1` to be specified and the application would generate C code instead of C++ code. I removed that functionality because the generated code was gross. I could add it back in, but I really don't want to.

> ##### Why C++11?

Compiler support for C++18 is abysmal right now.

> ##### What's with all the `auto function() -> int` nonsense?

C++11 allows you to specify the return type after the function. It has some practical uses, but honestly I just like the syntax&mdash;it makes all the function names line up. _Just some syn-tac-tic sugar makes the C++ go down..._

> ##### How much work does this actually save me?

Oh, probably not much. The code to retrieve the original function is like two lines and you could just copy it out of my code.

> ##### I was promised diamonds, but this just seems like a weak version of dtrace&mdash;why don't I use that instead?

Yeah, dtrace would probably be easier.
