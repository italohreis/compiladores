from ..ast import (
    Programa, Funcao, Declaracao, Parametro, Atribuicao,
    OperacaoBinaria, OperacaoUnaria, Numero, Booleano, String, Identificador, ChamadaFuncao)

class ParserError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self):
        token = self.current()

        if token is not None:
            self.pos += 1

        return token

    def check(self, tipo):
        token = self.current()
        return token is not None and token.tipo == tipo

    def match(self, tipo):
        if self.check(tipo):
            self.advance()
            return True

        return False

    def expect(self, tipo):
        token = self.current()

        if token is None:
            raise ParserError(
                f"Esperado {tipo}, mas o código terminou."
            )

        if token.tipo != tipo:
            raise ParserError(
                f"Erro sintático na linha {token.linha}: "
                f"esperado {tipo}, encontrado {token.tipo} ('{token.valor}')."
            )

        return self.advance()

    def parse(self):
        elementos = []

        while self.current() is not None:
            elementos.append(self.elemento())

        return Programa(elementos)

    # <elemento> ::= <funcao> | <comando>
    def elemento(self):
        if self.check("INT") or self.check("BOOL"):
            tipo = self.tipo()
            identificador = self.expect("IDENTIFICADOR")

            if self.check("ABRE_PARENTESES"):
                return self.funcao_restante(tipo, identificador)

            return self.declaracao_restante(tipo, identificador)

        return self.comando()

    # Parte final de:
    # <funcao> ::= <tipo> <identificador> "(" <parametros_opt> ")" <bloco>
    def funcao_restante(self, tipo, identificador):
        self.expect("ABRE_PARENTESES")
        parametros = self.parametros()
        self.expect("FECHA_PARENTESES")

        corpo = self.bloco()

        return Funcao(
            tipo,
            identificador.valor,
            parametros,
            corpo
        )

    # Parte final de:
    # <declaracao> ::= <tipo> <identificador> <inicializacao_opt> ";"
    def declaracao_restante(self, tipo, identificador):
        inicializacao = None

        if self.match("ATRIBUICAO"):
            inicializacao = self.expressao()

        self.expect("PONTO_VIRGULA")

        return Declaracao(tipo, identificador.valor, inicializacao)

    # <tipo> ::= int | bool
    def tipo(self):
        if self.check("INT"):
            self.advance()
            return "int"

        if self.check("BOOL"):
            self.advance()
            return "bool"

        token = self.current()
        raise ParserError(
            f"Erro sintático na linha {token.linha}: tipo esperado."
    )
    # <parametros_opt> ::= <parametros> | ε
    def parametros(self):
        parametros = []

        if self.check("FECHA_PARENTESES"):
            return parametros

        tipo = self.tipo()
        nome = self.expect("IDENTIFICADOR")
        parametros.append(Parametro(tipo, nome.valor))

        while self.match("VIRGULA"):
            tipo = self.tipo()
            nome = self.expect("IDENTIFICADOR")
            parametros.append(Parametro(tipo, nome.valor))

        return parametros

    # <comando> ::= declaração | atribuição | seleção |
    #               repetição | entrada | saída | retorno
    def comando(self):
        if self.check("INT") or self.check("BOOL"):
            self.tipo()
            self.expect("IDENTIFICADOR")

            if self.match("ATRIBUICAO"):
                self.expressao()

            self.expect("PONTO_VIRGULA")
            return

        if self.check("IDENTIFICADOR"):
            nome = self.advance()

            if self.match("ATRIBUICAO"):
                expressao = self.expressao()
                self.expect("PONTO_VIRGULA")
                return Atribuicao(nome.valor, expressao)

            if self.match("ABRE_PARENTESES"):
                argumentos = self.argumentos()
                self.expect("FECHA_PARENTESES")
                self.expect("PONTO_VIRGULA")
                return ChamadaFuncao(nome.valor, argumentos)

            raise ParserError(
                f"Erro sintático na linha {nome.linha}: "
                f"esperado '=' ou '(' após '{nome.valor}'."
            )

        if self.check("IF"):
            self.selecao()
            return

        if self.check("WHILE") or self.check("FOR"):
            self.repeticao()
            return

        if self.check("SCAN"):
            self.entrada()
            return

        if self.check("PRINT"):
            self.saida()
            return

        if self.check("RETURN"):
            self.retorno()
            return

        token = self.current()

        if token:
            raise ParserError(
                f"Erro sintático na linha {token.linha}: "
                f"comando inesperado '{token.valor}'."
            )

        raise ParserError("Fim inesperado do código.")

    # <selecao> ::= if "(" <expressao> ")" <bloco>
    #              | if "(" <expressao> ")" <bloco> else <bloco>
    def selecao(self):
        self.expect("IF")
        self.expect("ABRE_PARENTESES")
        self.expressao()
        self.expect("FECHA_PARENTESES")
        self.bloco()

        if self.match("ELSE"):
            self.bloco()

    # <repeticao> ::= <while> | <for>
    def repeticao(self):
        if self.match("WHILE"):
            self.expect("ABRE_PARENTESES")
            self.expressao()
            self.expect("FECHA_PARENTESES")
            self.bloco()
            return

        self.expect("FOR")
        self.expect("ABRE_PARENTESES")

        # inicialização do for
        self.expect("IDENTIFICADOR")
        self.expect("ATRIBUICAO")
        self.expressao()
        self.expect("PONTO_VIRGULA")

        # condição
        self.expressao()
        self.expect("PONTO_VIRGULA")

        # incremento
        self.expect("IDENTIFICADOR")
        self.expect("ATRIBUICAO")
        self.expressao()

        self.expect("FECHA_PARENTESES")
        self.bloco()

    # <entrada> ::= scan "(" <identificador> ")" ";"
    def entrada(self):
        self.expect("SCAN")
        self.expect("ABRE_PARENTESES")
        self.expect("IDENTIFICADOR")
        self.expect("FECHA_PARENTESES")
        self.expect("PONTO_VIRGULA")

    # <saida> ::= print "(" <expressao_ou_string> ")" ";"
    def saida(self):
        self.expect("PRINT")
        self.expect("ABRE_PARENTESES")

        if self.check("STRING"):
            self.advance()
        else:
            self.expressao()

        self.expect("FECHA_PARENTESES")
        self.expect("PONTO_VIRGULA")

    # <retorno> ::= return <expressao> ";"
    def retorno(self):
        self.expect("RETURN")
        self.expressao()
        self.expect("PONTO_VIRGULA")

    # <bloco> ::= "{" <comandos> "}"
    def bloco(self):
        self.expect("ABRE_CHAVES")

        if self.check("FECHA_CHAVES"):
            token = self.current()
            raise ParserError(
                f"Erro sintático na linha {token.linha}: "
                "bloco vazio não é permitido."
            )

        while not self.check("FECHA_CHAVES"):
            if self.current() is None:
                raise ParserError("Bloco não foi fechado com '}'.")

            self.comando()

        self.expect("FECHA_CHAVES")

    # <expressao> ::= <or>
    def expressao(self):
        self.or_expr()

    # <or> ::= <and> ("||" <and>)*
    def or_expr(self):
        esquerda = self.and_expr()

        while self.match("OR"):
            direita = self.and_expr()
            esquerda = OperacaoBinaria(esquerda, "||", direita)

        return esquerda

    # <and> ::= <relacional> ("&&" <relacional>)*
    def and_expr(self):
        esquerda = self.relacional()

        while self.match("AND"):
            direita = self.relacional()
            esquerda = OperacaoBinaria(esquerda, "&&", direita)

        return esquerda

    # <relacional> ::= <aditiva> [operador_relacional <aditiva>]
    def relacional(self):
        self.aditiva()

        if (
            self.check("IGUAL_IGUAL")
            or self.check("DIFERENTE")
            or self.check("MENOR")
            or self.check("MENOR_IGUAL")
            or self.check("MAIOR")
            or self.check("MAIOR_IGUAL")
        ):
            self.advance()
            self.aditiva()

    # <aditiva> ::= <multiplicativa> (("+" | "-") <multiplicativa>)*
    def aditiva(self):
        esquerda = self.multiplicativa()

        while self.check("MAIS") or self.check("MENOS"):
            operador = self.advance()
            direita = self.multiplicativa()
            esquerda = OperacaoBinaria(esquerda, operador.valor, direita)

        return esquerda

    # <multiplicativa> ::= <fator> (("*" | "/" | "%") <fator>)*
    def multiplicativa(self):
        esquerda = self.fator()

        while (
            self.check("MULTIPLICACAO")
            or self.check("DIVISAO")
            or self.check("MODULO")
        ):
            operador = self.advance()
            direita = self.fator()
            esquerda = OperacaoBinaria(esquerda, operador.valor, direita)


    # <fator> ::= identificador
    #           | chamada
    #           | número
    #           | true
    #           | false
    #           | "(" <expressao> ")"
    #           | "!" <fator>
    def fator(self):
        if self.match("NOT"):
            operando = self.fator()
            return OperacaoUnaria("!", operando)

        if self.check("NUMERO"):
            token = self.advance()
            return Numero(int(token.valor))

        if self.check("TRUE"):
            self.advance()
            return Booleano(True)

        if self.check("FALSE"):
            self.advance()
            return Booleano(False)

        if self.check("STRING"):
            token = self.advance()
            return String(token.valor[1:-1])

        if self.check("IDENTIFICADOR"):
            token = self.advance()

            if self.match("ABRE_PARENTESES"):
                argumentos = self.argumentos()
                self.expect("FECHA_PARENTESES")
                return ChamadaFuncao(token.valor, argumentos)

            return Identificador(token.valor)

        if self.match("ABRE_PARENTESES"):
            expressao = self.expressao()
            self.expect("FECHA_PARENTESES")
            return expressao

        token = self.current()

        if token:
            raise ParserError(
                f"Erro sintático na linha {token.linha}: "
                f"expressão inesperada '{token.valor}'."
            )

        raise ParserError("Fim inesperado durante expressão.")

    # <argumentos_opt> ::= <argumentos> | ε
    def argumentos(self):
        if self.check("FECHA_PARENTESES"):
            return

        self.expressao()

        while self.match("VIRGULA"):
            self.expressao()