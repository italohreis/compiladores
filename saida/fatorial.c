#include <stdio.h>
#include <stdbool.h>

int numero;
int resultado;

int fatorial(int n);

int fatorial(int n) {
    if ((n <= 1)) {
        return 1;
    }
    else {
        return (n * fatorial((n - 1)));
    }
}

int main(void) {
    printf("%s\n", "Digite um numero:");
    scanf("%d", &numero);
    resultado = fatorial(numero);
    printf("%s\n", "Resultado:");
    printf("%d\n", resultado);
    return 0;
}
