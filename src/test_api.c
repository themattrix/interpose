
#include <stdio.h>

int api_call(int argc, char **argv)
{
   printf("argv {\n");

   for(int i = 0; i < argc; ++i)
   {
      printf("   [%d] \"%s\"\n", i, argv[i]);
   }

   printf("}\n");

   return argc;
}

void api_simple()
{
   printf("simple!\n");
}
