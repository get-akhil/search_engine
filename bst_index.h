
#ifndef BST_INDEX_H
#define BST_INDEX_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_WORD_LEN 100
#define MAX_PATH_LEN 100

typedef struct DocNode {
    char filename[MAX_PATH_LEN];
    int frequency;            
    struct DocNode *next;
} DocNode;

typedef struct TreeNode {
    char word[MAX_WORD_LEN];
    int frequency;
    DocNode* docList;
    struct TreeNode *left;
    struct TreeNode *right;
} TreeNode;

TreeNode* newNode(char *word, const char *filename);

TreeNode* insertWord(TreeNode *node, char *word, const char *filename);

DocNode* searchWord(TreeNode *root, char *targetWord);

void inorderTraversal(TreeNode *root);

void freeTree(TreeNode *node);

#endif