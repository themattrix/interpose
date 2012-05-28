
/* for printf() */
#include <stdio.h>

/* for api_call() */
#include "test_api.h"

int main(int argc, char **argv)
{
   printf("result[1] = %d\n", api_call(argc, argv));

   api_simple();

   printf("result[2] = %d\n", api_call(argc, argv));

   return 0;
}
