#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <ctype.h>
#include <unistd.h>
#include "bst_index.h"
#include "query_processor.h"
#include "tokenizer_utils.h"

int main(int argc, char *argv[]) {
    struct dirent *de;
    FILE *fp;

    char buffer[1000];
    char *token;
    TreeNode *root = NULL; 

    
    DIR *dr = opendir("doc_sets");
    if (dr == NULL) {
        
        printf("[{\"error\": \"Could not open 'doc_sets' folder. Ensure the folder is present.\"}]");
        return 1;
    }

    while ((de = readdir(dr)) != NULL) {
        if (strcmp(de->d_name, ".") == 0 || strcmp(de->d_name, "..") == 0)
            continue;

        char path[500];
        sprintf(path, "doc_sets/%s", de->d_name);

        fp = fopen(path, "r");
        if (fp == NULL) {
            continue;
        }

        while (fgets(buffer, sizeof(buffer), fp)) {
            token = strtok(buffer, " \t\n");
            while (token != NULL) {
                cleanWord(token);
                simpleStem(token);
                if (strlen(token) > 0 && !isStopWord(token)) {
                    root = insertWord(root, token,de->d_name); 
                }
                token = strtok(NULL, " \t\n");
            }
        }
        fclose(fp);
    }
    closedir(dr);
    
    if (argc > 1) {
      
        handleSearch(root, argv[1]);
    } else {
      
        printf("[{\"message\": \"Index built successfully. Run the C executable with a search argument (e.g., ./search_engine 'query').\"}]");
    }

    freeTree(root); 
    return 0;
}