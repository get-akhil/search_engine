#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <ctype.h>
#include <unistd.h>
#include <sys/stat.h> 
#include "bst_index.h"
#include "query_processor.h"
#include "tokenizer_utils.h"

#define MAX_FULL_PATH 4096

void index_file(TreeNode **root, const char *full_path, const char *unique_filename) {
    FILE *fp = fopen(full_path, "r");
    if (fp == NULL) {
        return;
    }

    char buffer[1000];
    char *token;

    while (fgets(buffer, sizeof(buffer), fp)) {
        token = strtok(buffer, " \t\n");
        while (token != NULL) {
            cleanWord(token);
            simpleStem(token);
            if (strlen(token) > 0 && !isStopWord(token)) {
               
                *root = insertWord(*root, token, (char*)unique_filename); 
            }
            token = strtok(NULL, " \t\n");
        }
    }
    fclose(fp);
}


void traverse_and_index(TreeNode **root, const char *base_path) {
    DIR *dr = opendir(base_path);
    if (dr == NULL) {
        return; 
    }

    struct dirent *de;
    while ((de = readdir(dr)) != NULL) {
        if (strcmp(de->d_name, ".") == 0 || strcmp(de->d_name, "..") == 0)
            continue;

        char current_path[MAX_FULL_PATH];
        snprintf(current_path, MAX_FULL_PATH, "%s/%s", base_path, de->d_name);

        struct stat path_stat;
        if (stat(current_path, &path_stat) != 0) {
            continue;
        }

        if (S_ISDIR(path_stat.st_mode)) {


            DIR *sub_dr = opendir(current_path);
            if (sub_dr == NULL) continue;

            struct dirent *sub_de;
            while ((sub_de = readdir(sub_dr)) != NULL) {
                if (strcmp(sub_de->d_name, ".") == 0 || strcmp(sub_de->d_name, "..") == 0) continue;

                // Create a unique filename string: "CategoryName/DocumentName.txt"
                char unique_filename[MAX_PATH_LEN];
                snprintf(unique_filename, MAX_PATH_LEN, "%s/%s", de->d_name, sub_de->d_name);

                char sub_file_path[MAX_FULL_PATH];
                snprintf(sub_file_path, MAX_FULL_PATH, "%s/%s", current_path, sub_de->d_name);

                index_file(root, sub_file_path, unique_filename);
            }
            closedir(sub_dr);

        } else if (S_ISREG(path_stat.st_mode)) {
            index_file(root, current_path, de->d_name);
        }
    }
    closedir(dr);
}


int main(int argc, char *argv[]) {
    TreeNode *root = NULL; 
    traverse_and_index(&root, "doc_sets");

    if (root == NULL) {
   
        printf("[{\"error\": \"Index is empty. Could not find any files in doc_sets/ or its subfolders.\"}]");
        return 1;
    }
    
    if (argc > 1) {
        handleSearch(root, argv[1]);
    } else {
        printf("[{\"message\": \"Index built successfully. Run the C executable with a search argument (e.g., ./search_engine 'query').\"}]");
    }

    freeTree(root); 
    return 0;
}