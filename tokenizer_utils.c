#include <string.h>
#include <ctype.h>
#include "tokenizer_utils.h"
#include "bst_index.h"
#define MAX_WORD_SIZE 1000

void cleanWord(char *word) {
    int i, j = 0;
    char temp[MAX_WORD_SIZE];
    for (i = 0; word[i] != '\0'; i++) {
        if (isalpha(word[i]) || isdigit(word[i])) {         
            temp[j++] = tolower(word[i]);
        }
    }
    temp[j] = '\0';
    strcpy(word, temp);
}

const char *stopWords[] = {"the", "is", "and", "of", "to", "in", "on", "for", "with", "a", "an"};

int isStopWord(char *word) {
    for (int i = 0; i < sizeof(stopWords) / sizeof(stopWords[0]); i++) {
        if (strcmp(word, stopWords[i]) == 0)
            return 1;
    }
    return 0;
}

void simpleStem(char *word) {
    int len = strlen(word);
    if (len > 3) {
        if (strcmp(&word[len - 3], "ing") == 0)
            word[len - 3] = '\0';
        else if (strcmp(&word[len - 2], "ed") == 0)
            word[len - 2] = '\0';
        else if (word[len - 1] == 's')
            word[len - 1] = '\0';
    }
}