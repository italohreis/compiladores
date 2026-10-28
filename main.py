from src.cmini.lexer.lexer import LexicalAnalyzer
from src.cmini.parser.parser import Parser, ParserError
from src.cmini.semantic.analyzer import SemanticAnalyzer, SemanticError
from src.cmini.ast.printer import gerar_ast


def read_code_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


file_path = "examples/teste_sintatico.cm"

try:
    code = read_code_from_file(file_path)

    lexer = LexicalAnalyzer()
    tokens = lexer.analyze(code)

    parser = Parser(tokens)
    ast = parser.parse()
    print("Análise sintática concluída com sucesso!")

    analisador_semantico = SemanticAnalyzer()
    analisador_semantico.analisar(ast)
    print("Análise semântica concluída com sucesso!")

    gerar_ast(ast)

    print("\nTabela de símbolos:")
    tabela = analisador_semantico.gerar_tabela_simbolos()
    for item in tabela:
        print(f"Nome: {item['nome']}, Tipo: {item['tipo']}, Categoria: {item['categoria']}, Escopo: {item['escopo']}")

except SyntaxError as erro:
    print(f"Erro léxico: {erro}")
except ParserError as erro:
    print(erro)
except SemanticError as erro:
    print(erro)
