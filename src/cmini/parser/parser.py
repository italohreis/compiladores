from ..ast.nodes import (
    Programa, Declaracao, Funcao, Parametro, Bloco, Atribuicao,
    If, While, For, Scan, Print, Return, Numero, Booleano,
    String, Identificador, OperacaoBinaria, OperacaoUnaria,
    ChamadaFuncao
)


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
                f"Erro sintático: esperado {tipo}, mas o código terminou."
            )

        if token.tipo != tipo:
            raise ParserError(
                f"Erro sintático na linha {token.linha}: "
                f"esperado {tipo}, encontrado "
                f"{token.tipo} ('{token.valor}')."
            )

        return self.advance()

    def _com_linha(self, no, token):
        if no is not None and token is not None:
            no.linha = token.linha
        return no

    # Programa e elementos globais

    def parse(self):
        elementos = []

        while self.current() is not None:
            elementos.append(self.elemento())

        return Programa(elementos)

    def elemento(self):
        if self.check("INT") or self.check("BOOL"):
            tipo = self.tipo()
            nome = self.expect("IDENTIFICADOR")

            if self.check("ABRE_PARENTESES"):
                return self.funcao_restante(tipo, nome)

            return self.declaracao_restante(tipo, nome)

        return self.comando()

    def tipo(self):
        if self.match("INT"):
            return "int"

        if self.match("BOOL"):
            return "bool"

        token = self.current()
        linha = token.linha if token else "desconhecida"

        raise ParserError(
            f"Erro sintático na linha {linha}: tipo esperado."
        )

    def declaracao_restante(self, tipo, identificador):
        inicializacao = None

        if self.match("ATRIBUICAO"):
            inicializacao = self.expressao()

        self.expect("PONTO_VIRGULA")

        declaracao = Declaracao(tipo, identificador.valor, inicializacao)
        return self._com_linha(declaracao, identificador)

    # Funções e parâmetros

    def funcao_restante(self, tipo, identificador):
        self.expect("ABRE_PARENTESES")
        parametros = self.parametros()
        self.expect("FECHA_PARENTESES")
        corpo = self.bloco()

        funcao = Funcao(
            tipo,
            identificador.valor,
            parametros,
            corpo
        )
        return self._com_linha(funcao, identificador)

    def parametros(self):
        parametros = []

        if self.check("FECHA_PARENTESES"):
            return parametros

        tipo = self.tipo()
        nome = self.expect("IDENTIFICADOR")
        parametro = Parametro(tipo, nome.valor)
        parametro.linha = nome.linha
        parametros.append(parametro)

        while self.match("VIRGULA"):
            tipo = self.tipo()
            nome = self.expect("IDENTIFICADOR")
            parametro = Parametro(tipo, nome.valor)
            parametro.linha = nome.linha
            parametros.append(parametro)

        return parametros

    # Comandos

    def comando(self):
        if self.check("INT") or self.check("BOOL"):
            tipo = self.tipo()
            nome = self.expect("IDENTIFICADOR")
            return self.declaracao_restante(tipo, nome)

        if self.check("IDENTIFICADOR"):
            nome = self.advance()

            if self.match("ATRIBUICAO"):
                expressao = self.expressao()
                self.expect("PONTO_VIRGULA")
                atribuicao = Atribuicao(nome.valor, expressao)
                return self._com_linha(atribuicao, nome)

            if self.match("ABRE_PARENTESES"):
                argumentos = self.argumentos()
                self.expect("FECHA_PARENTESES")
                self.expect("PONTO_VIRGULA")
                chamada = ChamadaFuncao(nome.valor, argumentos)
                return self._com_linha(chamada, nome)

            raise ParserError(
                f"Erro sintático na linha {nome.linha}: "
                f"esperado '=' ou '(' após '{nome.valor}'."
            )

        if self.check("IF"):
            return self.selecao()

        if self.check("WHILE") or self.check("FOR"):
            return self.repeticao()

        if self.check("SCAN"):
            return self.entrada()

        if self.check("PRINT"):
            return self.saida()

        if self.check("RETURN"):
            return self.retorno()

        token = self.current()

        if token:
            raise ParserError(
                f"Erro sintático na linha {token.linha}: "
                f"comando inesperado '{token.valor}'."
            )

        raise ParserError("Fim inesperado do código.")

    def selecao(self):
        token_if = self.expect("IF")
        self.expect("ABRE_PARENTESES")
        condicao = self.expressao()
        self.expect("FECHA_PARENTESES")

        bloco_if = self.bloco()
        bloco_else = None

        if self.match("ELSE"):
            bloco_else = self.bloco()

        no = If(condicao, bloco_if, bloco_else)
        return self._com_linha(no, token_if)

    def repeticao(self):
        if self.check("WHILE"):
            token_while = self.expect("WHILE")
            self.expect("ABRE_PARENTESES")
            condicao = self.expressao()
            self.expect("FECHA_PARENTESES")
            corpo = self.bloco()

            no = While(condicao, corpo)
            return self._com_linha(no, token_while)

        token_for = self.expect("FOR")
        self.expect("ABRE_PARENTESES")

        # Inicialização: identificador = expressão
        inicializacao = self.atribuicao_for()
        self.expect("PONTO_VIRGULA")

        # Condição do laço
        condicao = self.expressao()
        self.expect("PONTO_VIRGULA")

        # Incremento: identificador = expressão
        incremento = self.atribuicao_for()
        self.expect("FECHA_PARENTESES")

        corpo = self.bloco()

        no = For(inicializacao, condicao, incremento, corpo)
        return self._com_linha(no, token_for)

    def atribuicao_for(self):
        nome = self.expect("IDENTIFICADOR")
        self.expect("ATRIBUICAO")
        expressao = self.expressao()

        atribuicao = Atribuicao(nome.valor, expressao)
        return self._com_linha(atribuicao, nome)

    def entrada(self):
        token_scan = self.expect("SCAN")
        self.expect("ABRE_PARENTESES")
        nome = self.expect("IDENTIFICADOR")
        self.expect("FECHA_PARENTESES")
        self.expect("PONTO_VIRGULA")

        scan = Scan(nome.valor)
        return self._com_linha(scan, token_scan)

    def saida(self):
        token_print = self.expect("PRINT")
        self.expect("ABRE_PARENTESES")

        if self.check("STRING"):
            token = self.advance()
            valor = String(token.valor[1:-1])
            valor.linha = token.linha
        else:
            valor = self.expressao()

        self.expect("FECHA_PARENTESES")
        self.expect("PONTO_VIRGULA")

        print_no = Print(valor)
        return self._com_linha(print_no, token_print)

    def retorno(self):
        token_return = self.expect("RETURN")
        expressao = self.expressao()
        self.expect("PONTO_VIRGULA")

        retorno = Return(expressao)
        return self._com_linha(retorno, token_return)

    def bloco(self):
        self.expect("ABRE_CHAVES")
        comandos = []

        if self.check("FECHA_CHAVES"):
            token = self.current()
            raise ParserError(
                f"Erro sintático na linha {token.linha}: "
                "bloco vazio não é permitido."
            )

        while not self.check("FECHA_CHAVES"):
            if self.current() is None:
                raise ParserError(
                    "Erro sintático: bloco não foi fechado com '}'."
                )

            comandos.append(self.comando())

        self.expect("FECHA_CHAVES")

        return Bloco(comandos)

    # Expressões: precedência do menor para o maior nível

    def expressao(self):
        return self.or_expr()

    def or_expr(self):
        esquerda = self.and_expr()

        while self.match("OR"):
            operador = self.tokens[self.pos - 1]
            direita = self.and_expr()
            esquerda = OperacaoBinaria(
                esquerda, "||", direita
            )
            esquerda.linha = operador.linha

        return esquerda

    def and_expr(self):
        esquerda = self.relacional()

        while self.match("AND"):
            operador = self.tokens[self.pos - 1]
            direita = self.relacional()
            esquerda = OperacaoBinaria(
                esquerda, "&&", direita
            )
            esquerda.linha = operador.linha

        return esquerda

    def relacional(self):
        esquerda = self.aditiva()

        operadores = {
            "IGUAL_IGUAL", "DIFERENTE", "MENOR",
            "MENOR_IGUAL", "MAIOR", "MAIOR_IGUAL"
        }

        if self.current() and self.current().tipo in operadores:
            operador = self.advance()
            direita = self.aditiva()

            esquerda = OperacaoBinaria(
                esquerda, operador.valor, direita
            )
            esquerda.linha = operador.linha

        return esquerda

    def aditiva(self):
        esquerda = self.multiplicativa()

        while self.check("MAIS") or self.check("MENOS"):
            operador = self.advance()
            direita = self.multiplicativa()

            esquerda = OperacaoBinaria(
                esquerda, operador.valor, direita
            )
            esquerda.linha = operador.linha

        return esquerda

    def multiplicativa(self):
        esquerda = self.fator()

        while (
            self.check("MULTIPLICACAO")
            or self.check("DIVISAO")
            or self.check("MODULO")
        ):
            operador = self.advance()
            direita = self.fator()

            esquerda = OperacaoBinaria(
                esquerda, operador.valor, direita
            )
            esquerda.linha = operador.linha

        return esquerda

    def fator(self):
        if self.match("NOT"):
            operador = self.tokens[self.pos - 1]
            operacao = OperacaoUnaria("!", self.fator())
            operacao.linha = operador.linha
            return operacao

        if self.check("MENOS"):
            operador = self.advance()
            operacao = OperacaoUnaria("-", self.fator())
            operacao.linha = operador.linha
            return operacao

        if self.check("NUMERO"):
            token = self.advance()
            numero = Numero(int(token.valor))
            numero.linha = token.linha
            return numero

        if self.check("TRUE"):
            token = self.advance()
            literal = Booleano(True)
            literal.linha = token.linha
            return literal

        if self.check("FALSE"):
            token = self.advance()
            literal = Booleano(False)
            literal.linha = token.linha
            return literal

        if self.check("IDENTIFICADOR"):
            nome = self.advance()

            if self.match("ABRE_PARENTESES"):
                argumentos = self.argumentos()
                self.expect("FECHA_PARENTESES")
                chamada = ChamadaFuncao(nome.valor, argumentos)
                chamada.linha = nome.linha
                return chamada

            identificador = Identificador(nome.valor)
            identificador.linha = nome.linha
            return identificador

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

        raise ParserError(
            "Erro sintático: fim inesperado durante expressão."
        )

    def argumentos(self):
        argumentos = []

        if self.check("FECHA_PARENTESES"):
            return argumentos

        argumentos.append(self.expressao())

        while self.match("VIRGULA"):
            argumentos.append(self.expressao())

        return argumentos