#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <ctype.h>
#include <unistd.h>
#include "bst_index.h"
#include "query_processor.h"
#include "tokenizer_utils.h"

int main() {
    struct dirent *de;
    FILE *fp;

    char buffer[1000];
    char *token;
    TreeNode *root = NULL; 
    char cwd[1024];
    getcwd(cwd, sizeof(cwd));
    //printf(" Current working directory: %s\n",cwd);

  
    DIR *dr = opendir("C:\\PROJECTS\\search engine\\doc_sets");
    if (dr == NULL) {
        printf(" Could not open 'doc_sets' folder.\n");
        return 1;
    }

    //printf(" Tokenizing all text files inside 'doc_sets/'...\n");

    while ((de = readdir(dr)) != NULL) {
        if (strcmp(de->d_name, ".") == 0 || strcmp(de->d_name, "..") == 0)
            continue;

        char path[500];
        sprintf(path, "C:\\PROJECTS\\search engine\\doc_sets\\%s", de->d_name);

        fp = fopen(path, "r");
        if (fp == NULL) {
            printf(" Error opening %s\n", path);
            continue;
        }

        //printf("\n---  Tokens in %s ---\n", de->d_name);

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
    //printf("\n\n Indexing complete! Total unique words indexed.\n");

    handleSearch(root);

    freeTree(root); 
    //printf("\nMemory cleanup done. Exiting.\n");
    return 0;
}
