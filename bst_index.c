#include "bst_index.h" 

static DocNode* newDocNode(const char *filename) {
    DocNode *docNode = (DocNode*)malloc(sizeof(DocNode));
    if (docNode == NULL) {
        printf("Error allocating memory for DocNode");
        exit(1);
    }
    strncpy(docNode->filename, filename, MAX_PATH_LEN - 1);
    docNode->filename[MAX_PATH_LEN - 1] = '\0';
    docNode->frequency = 1; 
    docNode->next = NULL;
    return docNode;
}

TreeNode* newNode(char *word, const char *filename) {
    TreeNode *node = (TreeNode*)malloc(sizeof(TreeNode));
    if (node == NULL) {
        printf("Error allocating memory for new node");
        exit(1);
    }
    
    strncpy(node->word, word, MAX_WORD_LEN - 1);
    node->word[MAX_WORD_LEN - 1] = '\0';
    node->docList = newDocNode(filename); 
    node->left = node->right = NULL;
    return node;
}

TreeNode* insertWord(TreeNode *node, char *word, const char *filename) {
    if (node == NULL) {
        return newNode(word, filename); 
    }
    int cmp = strcmp(word, node->word);
    if (cmp < 0) {
        node->left = insertWord(node->left, word, filename);
    } else if (cmp > 0) {
        node->right = insertWord(node->right, word, filename);
    } else {
        DocNode *current = node->docList;
        DocNode *prev = NULL;
        while (current != NULL) {
            if (strcmp(current->filename, filename) == 0) {
                current->frequency++;
                return node; 
            }
            prev = current;
            current = current->next;
        }

        DocNode *newDoc = newDocNode(filename);
        if (prev != NULL) {
            prev->next = newDoc;
        } else {
             node->docList = newDoc; 
        }
    }
    return node; 
}

DocNode* searchWord(TreeNode *root, char *targetWord) {
    if (root == NULL) {
        return NULL; 
    }

    int cmp = strcmp(targetWord, root->word);
    if (cmp == 0) {
        return root->docList; 
    } 
    else if (cmp < 0) {
        return searchWord(root->left, targetWord); 
    } 
    else {
        return searchWord(root->right, targetWord); 
    }
}

void inorderTraversal(TreeNode *root) {
    if (root != NULL) {
        inorderTraversal(root->left); 
        printf(" Word: %s\n", root->word);
        DocNode *current = root->docList;
        while (current != NULL) {
            printf("    -> Doc: %s (Count: %d)\n", current->filename, current->frequency);
            current = current->next;
        }
        inorderTraversal(root->right);
    }
}

void freeTree(TreeNode *node) {
    if (node != NULL) {
        DocNode *current = node->docList;
        DocNode *next;
        while (current != NULL) {
            next = current->next;
            free(current);
            current = next;
        }
        freeTree(node->left);
        freeTree(node->right);
        free(node);
    }
}