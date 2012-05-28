int api_call(int argc, char **argv);

void api_simple();

int api_simple_int();

typedef char ** (*return_t)(char **, const unsigned short);

return_t api_register_callback
(
   int (*callback)(char[], const void *, unsigned),
   char *argv[]
);
