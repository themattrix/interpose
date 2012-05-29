
int extract_int_args(int argc, char *argv[], int **args);

int add_int_args(int argc, int *args);

void join_int_args(char *out, int argc, int *args, const char *delim);

void release_int_args(int **args);
