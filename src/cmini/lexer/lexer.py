import re
from token import Token

class LexicalAnalyzer:
    def __init__(self):
        self.token_patterns = [
            # Palavras reservadas
            (r'\bint\b', 'INT'),
            (r'\bbool\b', 'BOOL'),
            (r'\bif\b', 'IF'),
            (r'\belse\b', 'ELSE'),
            (r'\bwhile\b', 'WHILE'),
            (r'\bfor\b', 'FOR'),
            (r'\bscan\b', 'SCAN'),
            (r'\bprint\b', 'PRINT'),
            (r'\breturn\b', 'RETURN'),
            (r'\btrue\b', 'TRUE'),
            (r'\bfalse\b', 'FALSE'),

            # Comentários
            (r'//[^\n]*', None),
            (r'/\*[\s\S]*?\*/', None),

            # Operadores relacionais
            (r'==', 'IGUAL_IGUAL'),
            (r'!=', 'DIFERENTE'),
            (r'<=', 'MENOR_IGUAL'),
            (r'>=', 'MAIOR_IGUAL'),
            (r'<', 'MENOR'),
            (r'>', 'MAIOR'),

            # Operadores lógicos
            (r'&&', 'AND'),
            (r'\|\|', 'OR'),
            (r'!', 'NOT'),

            # Atribuição
            (r'=', 'ATRIBUICAO'),

            # Operadores aritméticos
            (r'\+', 'MAIS'),
            (r'-', 'MENOS'),
            (r'\*', 'MULTIPLICACAO'),
            (r'/', 'DIVISAO'),
            (r'%', 'MODULO'),

            # Delimitadores
            (r'\(', 'ABRE_PARENTESES'),
            (r'\)', 'FECHA_PARENTESES'),
            (r'\{', 'ABRE_CHAVES'),
            (r'\}', 'FECHA_CHAVES'),
            (r';', 'PONTO_VIRGULA'),
            (r',', 'VIRGULA'),

            # Literais
            (r'"[^"\n]*"', 'STRING'),
            (r'[0-9]+', 'NUMERO'),

            # Identificadores
            (r'[a-zA-Z_][a-zA-Z_0-9]*', 'IDENTIFICADOR'),

            # Espaços, tabulações e quebras de linha
            (r'\s+', None)
        ]

        self.compiled_patterns = [
            (re.compile(pattern), token_type)
            for pattern, token_type in self.token_patterns
        ]

    def analyze(self, code):
        tokens = []
        linha = 1

        while code:
            match = None

            for regex, token_type in self.compiled_patterns:
                match = regex.match(code)

                if match:
                    valor = match.group(0)

                    if token_type:
                        tokens.append(Token(token_type, valor, linha))

                    linha += valor.count('\n')
                    break

            if not match:
                raise SyntaxError(f"Token inválido na linha {linha}: {code[0]}")

            code = code[match.end():]

        return tokens


def read_code_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


file_path = 'examples/teste.cm' 

code = read_code_from_file(file_path)

analyzer = LexicalAnalyzer()
tokens = analyzer.analyze(code)

for token in tokens:
    print(token)