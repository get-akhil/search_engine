#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "query_processor.h"
#include "tokenizer_utils.h" 
#include "bst_index.h"

#define MAX_DOCS 500 
#define MAX_QUERY_TOKENS 20

static DocNode* copyDocList(DocNode *source) {
    DocNode *head = NULL;
    DocNode *tail = NULL;
    DocNode *current = source;

    while (current != NULL) {
        DocNode *newNode = (DocNode*)malloc(sizeof(DocNode));
        if (newNode == NULL) {

            return NULL;
        }
        strncpy(newNode->filename, current->filename, MAX_PATH_LEN - 1);
        newNode->filename[MAX_PATH_LEN - 1] = '\0';
        newNode->frequency = current->frequency; 
        newNode->next = NULL;

        if (head == NULL) {
            head = newNode;
            tail = newNode;
        } else {
            tail->next = newNode;
            tail = newNode;
        }
        current = current->next;
    }
    return head;
}

static void freeDocList(DocNode *head) {
    DocNode *current = head;
    DocNode *next;
    while (current != NULL) {
        next = current->next;
        free(current);
        current = next;
    }
}

static DocNode* intersectDocLists(DocNode *listA, DocNode *listB) {
    DocNode *resultHead = NULL;
    DocNode *resultTail = NULL;
    DocNode *currentA = listA;
    while (currentA != NULL) {
        DocNode *currentB = listB;
        while (currentB != NULL) {
        
            if (strcmp(currentA->filename, currentB->filename) == 0) {
               
                DocNode *newNode = (DocNode*)malloc(sizeof(DocNode));
                if (newNode == NULL) return resultHead;

                strncpy(newNode->filename, currentA->filename, MAX_PATH_LEN - 1);
                newNode->filename[MAX_PATH_LEN - 1] = '\0';
                newNode->frequency = currentA->frequency + currentB->frequency;
                newNode->next = NULL;

                if (resultHead == NULL) {
                    resultHead = newNode;
                    resultTail = newNode;
                } else {
                    resultTail->next = newNode;
                    resultTail = newNode;
                }
                break; 
            }
            currentB = currentB->next;
        }
        currentA = currentA->next;
    }
    return resultHead;
}

static int compareResults(const void *a, const void *b) {
    SearchResult *resA = (SearchResult *)a;
    SearchResult *resB = (SearchResult *)b;
    
    return resB->score - resA->score;
}
static void printJsonResults(DocNode *docList) {
    SearchResult resultsArray[MAX_DOCS];
    int count = 0;
    DocNode *current = docList;

    while (current != NULL && count < MAX_DOCS) {
        strncpy(resultsArray[count].filename, current->filename, MAX_PATH_LEN - 1);
        resultsArray[count].filename[MAX_PATH_LEN - 1] = '\0';
        resultsArray[count].score = current->frequency;
        count++;
        current = current->next;
    }
    
    if (count > 0) {
        qsort(resultsArray, count, sizeof(SearchResult), compareResults);
    }
    printf("[");
    for (int i = 0; i < count; i++) {
        
        printf("{\"filename\": \"%s\", \"score\": %d}", 
               resultsArray[i].filename, resultsArray[i].score);
        if (i < count - 1) {
            printf(", ");
        }
    }
    printf("]");
}

void handleSearch(TreeNode *root, char *query) {
    char *token;
    char tempQuery[MAX_WORD_LEN * MAX_QUERY_TOKENS];
    DocNode *combinedList = NULL;
    int tokenCount = 0;

    if (root == NULL) {
        printf("[{\"error\": \"Index is empty. Cannot search.\"}]");
        return;
    }

    strncpy(tempQuery, query, sizeof(tempQuery) - 1);
    tempQuery[sizeof(tempQuery) - 1] = '\0';

   
    token = strtok(tempQuery, " \t\n");
    while (token != NULL && tokenCount < MAX_QUERY_TOKENS) {
        
        cleanWord(token);
        simpleStem(token);

        if (strlen(token) > 0 && !isStopWord(token)) {
            DocNode *currentDocList = searchWord(root, token);

            if (currentDocList != NULL) {
                if (combinedList == NULL) {
            
                    combinedList = copyDocList(currentDocList);
                } else {
                   
                    DocNode *newCombinedList = intersectDocLists(combinedList, currentDocList);
                    freeDocList(combinedList); 
                    combinedList = newCombinedList;
                    
                    if (combinedList == NULL) {
                        break; 
                    }
                }
                tokenCount++;
            } else if (tokenCount > 0) {
               
                 freeDocList(combinedList);
                 combinedList = NULL;
                 break;
            }
        }
        token = strtok(NULL, " \t\n");
    }

    if (combinedList != NULL) {
        printJsonResults(combinedList);
    } else {
       
        printf("[]"); 
    }

  
    if (combinedList != NULL) {
        freeDocList(combinedList);
    }
}