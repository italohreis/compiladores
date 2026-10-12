class ASTNode:
    pass


class Programa(ASTNode):
    def __init__(self, elementos):
        self.elementos = elementos


class Declaracao(ASTNode):
    def __init__(self, tipo, nome, inicializacao=None):
        self.tipo = tipo
        self.nome = nome
        self.inicializacao = inicializacao


class Funcao(ASTNode):
    def __init__(self, tipo_retorno, nome, parametros, corpo):
        self.tipo_retorno = tipo_retorno
        self.nome = nome
        self.parametros = parametros
        self.corpo = corpo


class Parametro(ASTNode):
    def __init__(self, tipo, nome):
        self.tipo = tipo
        self.nome = nome


class Bloco(ASTNode):
    def __init__(self, comandos):
        self.comandos = comandos


class Atribuicao(ASTNode):
    def __init__(self, nome, expressao):
        self.nome = nome
        self.expressao = expressao


class If(ASTNode):
    def __init__(self, condicao, bloco_if, bloco_else=None):
        self.condicao = condicao
        self.bloco_if = bloco_if
        self.bloco_else = bloco_else


class While(ASTNode):
    def __init__(self, condicao, corpo):
        self.condicao = condicao
        self.corpo = corpo


class For(ASTNode):
    def __init__(self, inicializacao, condicao, incremento, corpo):
        self.inicializacao = inicializacao
        self.condicao = condicao
        self.incremento = incremento
        self.corpo = corpo


class Scan(ASTNode):
    def __init__(self, nome):
        self.nome = nome


class Print(ASTNode):
    def __init__(self, valor):
        self.valor = valor


class Return(ASTNode):
    def __init__(self, expressao):
        self.expressao = expressao


class Numero(ASTNode):
    def __init__(self, valor):
        self.valor = valor


class Booleano(ASTNode):
    def __init__(self, valor):
        self.valor = valor


class String(ASTNode):
    def __init__(self, valor):
        self.valor = valor


class Identificador(ASTNode):
    def __init__(self, nome):
        self.nome = nome


class OperacaoBinaria(ASTNode):
    def __init__(self, esquerda, operador, direita):
        self.esquerda = esquerda
        self.operador = operador
        self.direita = direita


class OperacaoUnaria(ASTNode):
    def __init__(self, operador, operando):
        self.operador = operador
        self.operando = operando


class ChamadaFuncao(ASTNode):
    def __init__(self, nome, argumentos):
        self.nome = nome
        self.argumentos = argumentos