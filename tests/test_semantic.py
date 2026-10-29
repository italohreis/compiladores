import unittest

from src.cmini.lexer.lexer import LexicalAnalyzer
from src.cmini.parser.parser import Parser
from src.cmini.semantic.analyzer import SemanticAnalyzer, SemanticError
from src.cmini.codegen import CCodeGenerator


def analisar_codigo(codigo):
    tokens = LexicalAnalyzer().analyze(codigo)
    ast = Parser(tokens).parse()
    return SemanticAnalyzer().analisar(ast)


class TestAnalisadorSemantico(unittest.TestCase):
    def test_programa_valido(self):
        codigo = """
        int soma(int a, int b) { return a + b; }
        int x = 10;
        bool ativo = true;
        if (ativo && x >= 10) { x = soma(x, 1); }
        print(x);
        """
        self.assertTrue(analisar_codigo(codigo))

    def test_inicializacao_com_tipo_incompativel(self):
        with self.assertRaisesRegex(SemanticError, "inicialização de 'x'"):
            analisar_codigo("int x = true;")

    def test_variavel_nao_declarada(self):
        with self.assertRaisesRegex(SemanticError, "'x'.*declarada"):
            analisar_codigo("x = 10;")

    def test_condicao_precisa_ser_bool(self):
        with self.assertRaisesRegex(SemanticError, "condição de if deve ser 'bool'"):
            analisar_codigo("if (10) { print(1); }")

    def test_argumento_com_tipo_incorreto(self):
        codigo = "int dobro(int n) { return n * 2; } int x = dobro(true);"
        with self.assertRaisesRegex(SemanticError, "argumento 1 de 'dobro'"):
            analisar_codigo(codigo)

    def test_quantidade_incorreta_de_argumentos(self):
        codigo = "int soma(int a, int b) { return a + b; } int x = soma(1);"
        with self.assertRaisesRegex(SemanticError, r"espera 2 argumento\(s\)"):
            analisar_codigo(codigo)

    def test_retorno_com_tipo_incorreto(self):
        with self.assertRaisesRegex(SemanticError, "deveria retornar 'int'"):
            analisar_codigo("int valor() { return false; }")

    def test_funcao_sem_return_garantido(self):
        codigo = "int valor(bool ok) { if (ok) { return 1; } else { print(0); } }"
        with self.assertRaisesRegex(SemanticError, "pode terminar sem executar um return"):
            analisar_codigo(codigo)

    def test_variavel_local_fora_do_escopo(self):
        codigo = "if (true) { int temporaria = 1; } print(temporaria);"
        with self.assertRaisesRegex(SemanticError, "temporaria.*declarada"):
            analisar_codigo(codigo)

    def test_funcao_duplicada(self):
        codigo = "int f() { return 1; } int f() { return 2; }"
        with self.assertRaisesRegex(SemanticError, "função 'f'.*mais de uma vez"):
            analisar_codigo(codigo)

    def test_escopo_local_sombrea_variavel_global(self):
        codigo = """
        int x = 1;
        int f() {
            int x = 2;
            return x;
        }
        """
        self.assertTrue(analisar_codigo(codigo))

    def test_chamada_recursiva_valida(self):
        codigo = """
        int fat(int n) {
            if (n <= 1) { return 1; }
            return n * fat(n - 1);
        }
        """
        self.assertTrue(analisar_codigo(codigo))

    def test_expressao_com_tipo_invalido(self):
        with self.assertRaisesRegex(SemanticError, r"operador '\+' exige operandos 'int'"):
            analisar_codigo("int x = 1 + true;")

    def test_retorno_em_else_gera_sucesso(self):
        codigo = """
        int sinal(int x) {
            if (x > 0) { return 1; }
            else { return 0; }
        }
        """
        self.assertTrue(analisar_codigo(codigo))

    def test_erro_mostra_linha_exata(self):
        with self.assertRaisesRegex(SemanticError, r"linha 1:.*inicialização de 'x'"):
            analisar_codigo("int x = true;")

    def test_tabela_de_simbolos_gera_escopos(self):
        codigo = """
        int soma(int a, int b) {
            int total = a + b;
            return total;
        }
        """
        ast = Parser(LexicalAnalyzer().analyze(codigo)).parse()
        analise = SemanticAnalyzer()
        analise.analisar(ast)
        tabela = analise.gerar_tabela_simbolos()

        self.assertTrue(any(item["nome"] == "soma" and item["categoria"] == "funcao" for item in tabela))
        self.assertTrue(any(item["nome"] == "a" and item["categoria"] == "variavel" and item["escopo"] == "soma" for item in tabela))
        self.assertTrue(any(item["nome"] == "total" and item["categoria"] == "variavel" and item["escopo"] == "soma" for item in tabela))

    def test_geracao_de_codigo_c(self):
        codigo = """
        int x = 3;
        int dobro(int n) { return n * 2 + x; }
        bool ok = true;
        if (ok) { print(dobro(x)); } else { print(0); }
        """
        ast = Parser(LexicalAnalyzer().analyze(codigo)).parse()
        SemanticAnalyzer().analisar(ast)
        gerado = CCodeGenerator().generate(ast)

        self.assertIn("#include <stdbool.h>", gerado)
        self.assertIn("int x;", gerado)
        self.assertIn("int dobro(int n);", gerado)
        self.assertIn("return ((n * 2) + x);", gerado)
        self.assertIn("x = 3;", gerado)
        self.assertIn("printf(\"%d\", dobro(x));", gerado)
        self.assertIn("int main(void)", gerado)


if __name__ == "__main__":
    unittest.main()
