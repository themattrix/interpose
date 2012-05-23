#ifdef __cplusplus
extern "C" {
#endif

#include <stdio.h>
#include <dlfcn.h>
#include <sys/time.h>
#include "{{ORIGINAL_HEADER}}"

#ifdef __cplusplus
}
#endif

// insert the user-defined functions
#include "{{USER_DEFINED_FUNCTIONS}}"

namespace util
{
#ifdef __APPLE__
   // retrieving the original function call on OS X requires the library name
   static const char LIB_NAME[] = "{{APPLE_LIB_NAME}}";
#endif

   static auto current_time() -> timeval
   {
      // store a precise time-stamp
      timeval time;

      // capture the current time
      gettimeofday(&time, NULL);

      // return the time
      return time;
   }

   static void print_call(timeval const &call, char const *function)
   {
      printf
      (
         "[%011llu.%06llu][call] %s()\n",
         (long long unsigned)call.tv_sec,
         (long long unsigned)call.tv_usec,
         function
      );
   }

   static void print_done(timeval const &call, timeval const &done, char const *function)
   {
      printf
      (
         "[%011llu.%06llu][done][%llu.%06llu] %s()\n",
         (long long unsigned)done.tv_sec,
         (long long unsigned)done.tv_usec,
         (long long unsigned)(done.tv_sec  - call.tv_sec),
         (long long unsigned)(done.tv_usec - call.tv_usec),
         function
      );
   }

   template<typename Signature>
   static auto get_function(char const *function) -> Signature
   {
#ifdef __APPLE__
      /** 
       ** On OS X, the original library is loaded explicitly and the function is
       ** queried from within that library. This technique does not work on linux; it
       ** results in an infinite recursion.
       **/

      // grab handle to the original library
      void *handle = dlopen(LIB_NAME, RTLD_NOW);

      // find the original function within that library
      return (Signature)dlsym(handle, function);
#else
      /** 
       ** Retrieving a pointer to the original function is even easier in linux. It
       ** doesn't even require the original library name. Calling dlsym() with the
       ** flag "RTLD_NEXT" returns the *next* occurrence of the specified name, which
       ** is the original library call. This does not work on OS X; it fails to find
       ** the function.
       **/

      // find the original function
      return (Signature)dlsym(RTLD_NEXT, function);
#endif
   }

   template<typename ReturnType, typename...Parameters>
   static auto interpose
   (
      ReturnType (*wrap)(ReturnType (*)(Parameters...), Parameters...),
      char const *function_name,
      ReturnType (*&original)(Parameters...),
      ReturnType const &default_return,
      Parameters...parameters
   )
   -> ReturnType
   {
      // record the timestamp before the call
      timeval call_timestamp(current_time());

      // print the time-stamp
      print_call(call_timestamp, function_name);

      // find the original function
      if(!original)
      {
         original = get_function<ReturnType (*)(Parameters...)>(function_name);

         // if the original function is not found...
         if(!original)
         {
            // ...print an error...
            printf("   >>> ERROR: %s() not found\n", function_name);

            // ...and return immediately
            return default_return;
         }
      }

      // run the original function
      ReturnType result(wrap(original, parameters...));

      // record the timestamp after the call
      timeval done_timestamp(current_time());

      // print the time-stamp and duration
      print_done(call_timestamp, done_timestamp, function_name);

      // return the actual result
      return result;
   }

   template<typename...Parameters>
   static void interpose
   (
      void (*wrap)(void (*)(Parameters...), Parameters...),
      char const *function_name,
      void (*&original)(Parameters...),
      Parameters...parameters
   )
   {
      // record the timestamp before the call
      timeval call_timestamp(current_time());

      // print the time-stamp
      print_call(call_timestamp, function_name);

      // find the original function
      if(!original)
      {
         original = get_function<void (*)(Parameters...)>(function_name);

         // if the original function is not found...
         if(!original)
         {
            // ...print an error...
            printf("   >>> ERROR: %s() not found\n", function_name);

            // ...and return immediately
            return;
         }
      }

      // run the original function
      wrap(original, parameters...);

      // record the timestamp after the call
      timeval done_timestamp(current_time());

      // print the time-stamp and duration
      print_done(call_timestamp, done_timestamp, function_name);
   }
}

{{FOR_EACH_FUNCTION:
static auto proxy_{{NAME}}({{ARGUMENT_LIST}}) -> {{RETURN_TYPE}}
{
   // points to the original function being interposed
   static {{RETURN_TYPE}} (*original)({{ARGUMENT_TYPES}}) = NULL;

   {{IF_NONVOID:return }}util::interpose(&{{NAME}}, "{{NAME}}", original{{IF_NONVOID:, {{RETURN_TYPE}}()}}{{,ARGUMENT_NAMES}});
}
}}

#ifdef __cplusplus
extern "C" {
#endif

{{FOR_EACH_FUNCTION:
{{RETURN_TYPE}} {{NAME}}({{ARGUMENT_LIST}})
{
   {{IF_NONVOID:return }}proxy_{{NAME}}({{ARGUMENT_NAMES}});
}
}}

#ifdef __cplusplus
}
#endif
