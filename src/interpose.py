#!/usr/bin/python

from textwrap import dedent

TYPE_CONVERSION={
   'size_t' : 'unsigned long',
   'int8_t' : 'char',
   'uint8_t' : 'unsigned char',
   'int16_t' : 'short',
   'uint16_t' : 'unsigned short',
   'int32_t' : 'long',
   'uint32_t' : 'unsigned long',
   'int64_t' : 'long long',
   'uint64_t' : 'unsigned long long',
   'signed char' : 'char',
   'unsigned int' : 'unsigned',
   'unsigned long int' : 'unsigned long',
   'unsigned long long int' : 'unsigned long long',
   'long int' : 'long',
   'long long int' : 'long long'}

class interpose(object):
   def __init__(self, api):
      self.api = api
   def generate(self):
      INCLUDES=(
         'stdio.h',
         'dlfcn.h',
         'sys/time.h')
      PRINTF_TYPES={
         'char' : "'%c'",
         'unsigned char' : '%u',
         'short' : '',
         'unsigned short' : '%u',
         'int' : '%d',
         'unsigned' : '%u',
         'long' : '%ld',
         'unsigned long' : '%lu',
         'long long' : '%lld',
         'unsigned long long' : '%llu'}
      result = '\n'.join('#include <' + i + '>' for i in INCLUDES)
      for function in self.api:
         name = function[0]
         args = function[1]
         retn = function[2]
         if retn == 'void':
            save_result = ''
            retn_result = ''
         else:
            save_result = "{0} result = "
            retn_result = '''
            
            // return the actual result
            return result;'''
         result += dedent((
         '''

         {0} {1}({2})
         {{
            // store the precise time-stamp for outputting later
            struct timeval time;

            // capture the current time
            gettimeofday(&time, NULL);

            // points to the original function being interposed
            static {0} (*real_{1})({3}) = NULL;

            // on the first call to this function, determine the pointer to the original function
            if(!real_{1}) real_{1} = dlsym(RTLD_NEXT, "{1}");

            // run the original function
            ''' + save_result + '''real_{1}({4});

            // output the precise time-stamp and the function name
            printf
            (
               "[%llu.%06llu] {1}()",
               (long long unsigned)time.tv_sec,
               (long long unsigned)time.tv_usec
            );{5}
         }}
         ''').format(
            retn,
            name,
            ', '.join('{0} {1}'.format(arg[1], arg[0]) for arg in args),
            ', '.join(arg[1] for arg in args),
            ', '.join(arg[0] for arg in args),
            retn_result))
      return result

def main():
   API=(('api_call', (('argc','int'),('argv', 'char *[]')), 'void'),)
   print(interpose(API).generate())

if __name__ == "__main__":
   main()
