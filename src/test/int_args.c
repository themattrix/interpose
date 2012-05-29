
#include <stdlib.h>
#include <stdio.h>
#include "int_args.h"

int extract_int_args(int argc, char *argv[], int **args)
{
   *args = (int *)malloc(argc * sizeof(int));

   for(int i = 0; i < argc; ++i)
   {
      (*args)[i] = atoi(argv[i]);
   }

   return argc;
}

int add_int_args(int argc, int *args)
{
   int sum = 0;

   for(int i = 0; i < argc; ++i)
   {
      sum += args[i];
   }

   return sum;
}

void join_int_args(char *out, int argc, int *args, const char *delim)
{
   int offset = 0;

   for(int i = 0; i < argc; ++i)
   {
      if(i)
      {
         offset += sprintf(out + offset, "%s", delim);
      }

      offset += sprintf(out + offset, "%d", args[i]);
   }
}

void release_int_args(int **args)
{
   free(*args);
   *args = NULL;
}
