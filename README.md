# Compilador C Mini

## Compilar um arquivo

Na raiz do projeto, execute:

```powershell
python main.py examples\fatorial.cm
```

O compilador executa o lexer, o parser, a análise semântica, gera o código C
em `saida\fatorial.c` e cria o executável em `saida\fatorial.exe`.

Para executar o programa gerado:

```powershell
python main.py examples\fatorial.cm --run
```

O programa `fatorial.cm` solicita um número pelo teclado. Os demais exemplos
demonstram estruturas de controle, tipos, funções, recursão e escopos:

- `examples\controle.cm`
- `examples\tipos_e_funcoes.cm`
- `examples\escopos.cm`

Para gerar também a visualização HTML da AST:

```powershell
python main.py examples\controle.cm --ast
```

O GCC precisa estar instalado e disponível no `PATH`.
