#ifndef QUERY_PROCESSOR
#define QUERY_PROCESSOR

#include "bst_index.h" 

typedef struct SearchResult {
     char filename[MAX_PATH_LEN];
    int score; 
} SearchResult;

void handleSearch(TreeNode *root, char *query);

#endif