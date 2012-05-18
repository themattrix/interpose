#!/usr/bin/python

import platform
import subprocess

from textwrap import dedent

if platform.system() == 'Darwin':
   SO_EXTENSION = 'dylib'
   CC           = 'gcc'
   CC_FLAGS     = ['-fPIC', '-Wall', '-Werror', '-std=c99', '-flat_namespace', '-dynamiclib']
   CC_LIBS      = ['-ldl']
else:
   SO_EXTENSION = 'so'
   CC           = 'gcc'
   CC_FLAGS     = ['-fPIC', '-Wall', '-Werror', '-std=c99', '-shared', '-D_GNU_SOURCE']
   CC_LIBS      = ['-ldl']

def audit(message):
   """Currently just a wrapper for print()."""
   print(message)

class Interpose(object):
   """
   Generate, write out, and compile C code for interposing API calls. The resulting library can be
   used to intercept API calls for the specified function signatures if it is loaded before the
   original library. On linux, this is achieved with the 'LD_PRELOAD=/path/to/lib.so' variable. On
   OS X, use the 'DYLD_FORCE_FLAT_NAMESPACE=1 DYLD_INSERT_LIBRARIES=/path/to/lib.dylib' variables.
   """
   def __init__(self, header, lib, api):
      self.real_header = header
      self.real_lib = lib
      self.interpose_lib = 'libinterpose_{0}.{1}'.format(self.real_header, SO_EXTENSION)
      self.interpose_source = 'interpose_{0}.c'.format(self.real_header)
      self.api = api
      self.generated_code = ''
      self.wrote = False
   def generate(self):
      if not self.generated_code:
         includes=(
            '<stdio.h>',
            '<dlfcn.h>',
            '<sys/time.h>',
            '"{0}"'.format(self.real_header))
         result = '\n'.join('#include {0}'.format(i) for i in includes) + dedent('''

         struct timeval current_time()
         {
            // store a precise time-stamp
            struct timeval time;

            // capture the current time
            gettimeofday(&time, NULL);
            
            // return the time
            return time;
         }
         ''')
         for function in self.api:
            name, args, retn = function[:3]
            if retn == 'void':
               save_result = ''
               retn_result = ''
               dflt_result = 'return;'
            else:
               dflt = function[3]
               save_result = "{0} result = ".format(retn)
               retn_result = '''
               
               // return the actual result
               return result;'''
               dflt_result = "return {0};".format(dflt)
            result += dedent((
            '''
            {0} {1}({2})
            {{
               // points to the original function being interposed
               static {0} (*real_{1})({3}) = NULL;

               // record the timestamp before the call
               struct timeval call_timestamp = current_time();

               // print the time-stamp
               printf
               (
                  "[%011llu.%06llu][call] {1}()\\n",
                  (long long unsigned)call_timestamp.tv_sec,
                  (long long unsigned)call_timestamp.tv_usec
               );

               // find the original function
               if(!real_{1})
               {{
            #ifdef __APPLE__
                  /** 
                   ** On OS X, the original library is loaded explicitly and the function is
                   ** queried from within that library. This technique does not work on linux; it
                   ** results in an infinite recursion.
                   **/

                  // grab handle to the original library
                  void *handle = dlopen("{8}", RTLD_NOW);

                  // find the original function within that library
                  real_{1} = ({0} (*)({3}))dlsym(handle, "{1}");
            #else
                  /** 
                   ** Retrieving a pointer to the original function is even easier in linux.
                   ** Calling dlsym() with the flag "RTLD_NEXT" returns the *next* occurrence of
                   ** the specified name, which is the original library call This does not work
                   ** on OS X; it fails to find the function.
                   **/

                  // find the original function
                  real_{1} = dlsym(RTLD_NEXT, "{1}");
            #endif

                  // if the original function is not found...
                  if(!real_{1})
                  {{
                     // ...print an error...
                     printf("   >>> ERROR: {1}() not found\\n");

                     // ...and return immediately
                     {7}
                  }}
               }}

               // run the original function
               {5}real_{1}({4});

               // record the timestamp after the call
               struct timeval done_timestamp = current_time();

               // print the time-stamp
               printf
               (
                  "   >>> duration: %llu.%06llu seconds\\n"
                  "[%011llu.%06llu][done] {1}()\\n",
                  (long long unsigned)(done_timestamp.tv_sec  - call_timestamp.tv_sec),
                  (long long unsigned)(done_timestamp.tv_usec - call_timestamp.tv_usec),
                  (long long unsigned)done_timestamp.tv_sec,
                  (long long unsigned)done_timestamp.tv_usec
               );{6}
            }}
            ''').format(
               retn,
               name,
               ', '.join('{0} {1}'.format(arg[1], arg[0]) for arg in args),
               ', '.join(arg[1] for arg in args),
               ', '.join(arg[0] for arg in args),
               save_result,
               retn_result,
               dflt_result,
               self.real_lib))
         self.generated_code = result
      return self.generated_code
   def write(self):
      if not self.wrote:
         with open(self.interpose_source, 'w') as f:
            f.write(self.generate())
         self.wrote = True
   def build(self):
      self.write()
      cmd = [CC] + CC_FLAGS + ['-o', self.interpose_lib, self.interpose_source] + CC_LIBS
      audit(">>> {0}".format(' '.join(c for c in cmd)))
      subprocess.call(cmd)

def main():
   API=('test_api.h', 'libtest_api.dylib', ('api_call', (('argc','int'),('argv', 'char **')), 'int', '-1'), ('api_simple', (), 'void'))
   i = Interpose(header = API[0], lib = API[1], api = API[2:])
   i.build()

if __name__ == "__main__":
   main()
