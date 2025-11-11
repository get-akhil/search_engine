#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "query_processor.h"
#include "tokenizer_utils.h" 
#include "bst_index.h"

#define MAX_DOCS 500 

static int compareResults(const void *a, const void *b) {
    SearchResult *resA = (SearchResult *)a;
    SearchResult *resB = (SearchResult *)b;
    return resB->score - resA->score;
}

static void sortAndDisplayResults(DocNode *docList, const char *queryWord) {
    SearchResult resultsArray[MAX_DOCS];
    int count = 0;
    DocNode *current = docList;
    int totalCount = 0;

    while (current != NULL && count < MAX_DOCS) {
        strncpy(resultsArray[count].filename, current->filename, MAX_PATH_LEN);
        resultsArray[count].score = current->frequency;
        totalCount += current->frequency;
        count++;
        current = current->next;
    }
    
    if (count == 0) {
        printf("\nWord '%s' not found in any document.\n", queryWord);
        return;
    }

    qsort(resultsArray, count, sizeof(SearchResult), compareResults);
    
    printf("\nFound word '%s' in %d document(s) (Total Occurrences: %d):\n", 
           queryWord, count, totalCount);

    for (int i = 0; i < count; i++) {
        printf(" %2d. File: %s (Relevance Score: %d)\n", 
               i + 1, resultsArray[i].filename, resultsArray[i].score);
    }
}

void handleSearch(TreeNode *root) {
    char searchInput[MAX_WORD_LEN];
    char cleanedQuery[MAX_WORD_LEN];
    DocNode *docList;
    
    if (root == NULL) {
        printf("\nError: Index is empty. Cannot search.\n");
        return;
    }

    printf("\n--- Search Engine Query (Single Word) ---\n");
    printf("Enter search term (or 'exit' to quit): ");

    while (fgets(searchInput, MAX_WORD_LEN, stdin)) {
        
        size_t len = strlen(searchInput);
        if (len > 0 && searchInput[len-1] == '\n') {
            searchInput[len-1] = '\0';
        }

        if (strcmp(searchInput, "exit") == 0) {
            break;
        }

        strncpy(cleanedQuery, searchInput, MAX_WORD_LEN - 1);
        cleanedQuery[MAX_WORD_LEN - 1] = '\0';
        
        cleanWord(cleanedQuery);
        simpleStem(cleanedQuery);

        if (strlen(cleanedQuery) == 0 || isStopWord(cleanedQuery)) {
            printf("\nQuery word is too short or a stop word. Try a different term.\n");
        } else {
           
            docList = searchWord(root, cleanedQuery);
            sortAndDisplayResults(docList, cleanedQuery);
        }
        
        printf("\n--- Search Engine Query (Single Word) ---\n");
        printf("Enter search term (or 'exit' to quit): ");
    }
}