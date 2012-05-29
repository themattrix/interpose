
/** Allocate an integer array equal in size to argc and fill it with integer
 ** representations of of the supplied command-line arguments.
 **/
int extract_int_args(int argc, char *argv[], int **args);

/** Return the sum of all integers in 'args'. 
 **/
int add_int_args(int argc, int *args);

/** Joins all of the integers in 'args' with 'delim'. For example, if delim is
 ** " + " and args is (9, 3, 6), the result would be "9 + 3 + 6". The result is
 ** appended to 'out'.
 **/
void join_int_args(char *out, int len, int argc, int *args, const char *delim);

/** Frees 'args' and sets it to NULL.
 **/
void release_int_args(int **args);
