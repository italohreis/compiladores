from src.cmini.lexer.lexer import LexicalAnalyzer
from src.cmini.parser.parser import Parser, ParserError
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
    gerar_ast(ast)

except ParserError as erro:
    print(erro)

except SyntaxError as erro:
    print(f"Erro léxico: {erro}")