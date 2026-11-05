#include <stdio.h>
#include <stdbool.h>

int x;

int main(void) {
    x = 0;
    printf("%s\n", "Executando while: ");
    while ((x < 3)) {
        printf("%d\n", x);
        x = (x + 1);
    }
    printf("%s\n", "Executando for: ");
    for (x = 0; (x < 3); x = (x + 1)) {
        printf("%d\n", x);
    }
    return 0;
}
