
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
