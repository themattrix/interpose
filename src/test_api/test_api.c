
#include <stdio.h>

int api_call(int argc, char **argv)
{
   printf("   libtest_api::api_call(int, char **)\n");
   return argc;
}

void api_simple()
{
   printf("   libtest_api::api_simple()\n");
}
