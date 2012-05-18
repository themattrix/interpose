
/* for printf() */
#include <stdio.h>

/* for api_call() */
#include "test_api.h"

int main(int argc, char **argv)
{
   printf("result = %d\n", api_call(argc, argv));

   api_simple();

   return 0;
}
