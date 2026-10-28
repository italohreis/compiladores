from ..ast.nodes import (
    Programa, Declaracao, Funcao, Bloco, Atribuicao, If, While, For,
    Scan, Print, Return, Numero, Booleano, String, Identificador,
    OperacaoBinaria, OperacaoUnaria, ChamadaFuncao,
)


class SemanticError(Exception):
    """Erro encontrado durante a análise semântica."""


class TabelaSimbolos:
    """Mantém uma tabela de símbolos organizada por escopo e categoria."""

    def __init__(self):
        self.entradas = []

    def registrar(self, nome, tipo, categoria, escopo, linha, **metadata):
        entrada = {
            "nome": nome,
            "tipo": tipo,
            "categoria": categoria,
            "escopo": escopo,
            "linha": linha,
        }
        entrada.update(metadata)
        self.entradas.append(entrada)
        return entrada

    def buscar(self, nome, escopo=None):
        for entrada in reversed(self.entradas):
            if entrada["nome"] == nome and (escopo is None or entrada["escopo"] == escopo):
                return entrada
        return None

    def listar(self):
        return list(self.entradas)

    def gerar(self):
        return self.listar()

    def __str__(self):
        if not self.entradas:
            return "Tabela de símbolos vazia."

        colunas = ["nome", "tipo", "categoria", "escopo", "linha"]
        linhas = [
            [str(entrada.get(coluna, "")) for coluna in colunas]
            for entrada in self.entradas
        ]
        tamanhos = [max(len(str(linha[i])) for linha in [colunas] + linhas) for i in range(len(colunas))]
        separador = " | ".join("-" * tamanho for tamanho in tamanhos)

        cabecalho = " | ".join(coluna.ljust(tamanhos[i]) for i, coluna in enumerate(colunas))
        conteudo = [
            " | ".join(str(valor).ljust(tamanhos[i]) for i, valor in enumerate(linha))
            for linha in linhas
        ]
        return "\n".join([cabecalho, separador, *conteudo])


class SemanticAnalyzer:
    """Verifica nomes, escopos e compatibilidade de tipos da C Mini."""

    TIPOS = {"int", "bool"}
    OPERADORES_ARITMETICOS = {"+", "-", "*", "/", "%"}
    OPERADORES_RELACIONAIS = {"<", "<=", ">", ">="}
    OPERADORES_IGUALDADE = {"==", "!="}
    OPERADORES_LOGICOS = {"&&", "||"}

    def __init__(self):
        self.funcoes = {}
        self.escopos = []
        self.tipo_retorno_atual = None
        self.funcao_atual = None
        self.tabela_simbolos = TabelaSimbolos()

    def _escopo_nome_atual(self):
        if len(self.escopos) == 1:
            return "global"
        if self.funcao_atual is not None:
            return self.funcao_atual
        return f"escopo_{len(self.escopos)}"

    def analisar(self, programa):
        if not isinstance(programa, Programa):
            raise SemanticError("a raiz da AST não é um Programa válido.")

        self.funcoes = {}
        self.escopos = [{}]
        self.tipo_retorno_atual = None
        self.funcao_atual = None
        self.tabela_simbolos = TabelaSimbolos()

        # Registrar assinaturas primeiro permite chamadas recursivas e chamadas
        # para funções que aparecem depois no arquivo.
        for elemento in programa.elementos:
            if isinstance(elemento, Funcao):
                self._registrar_funcao(elemento)

        # Variáveis globais continuam sujeitas à ordem de declaração.
        for elemento in programa.elementos:
            if isinstance(elemento, Declaracao):
                self._analisar_declaracao(elemento)
            elif isinstance(elemento, Funcao):
                self._analisar_funcao(elemento)
            else:
                self._analisar_comando(elemento)

        return True

    def _erro(self, mensagem, no=None):
        linha = getattr(no, "linha", None)
        if linha is not None:
            raise SemanticError(f"Erro semântico na linha {linha}: {mensagem}")
        raise SemanticError(f"Erro semântico: {mensagem}")

    def _registrar_funcao(self, funcao):
        if funcao.nome in self.funcoes:
            self._erro(f"a função '{funcao.nome}' foi declarada mais de uma vez.", funcao)
        self.funcoes[funcao.nome] = {
            "retorno": funcao.tipo_retorno,
            "parametros": [parametro.tipo for parametro in funcao.parametros],
            "no": funcao,
        }
        self.tabela_simbolos.registrar(
            funcao.nome,
            funcao.tipo_retorno,
            "funcao",
            "global",
            getattr(funcao, "linha", None),
            parametros=[parametro.tipo for parametro in funcao.parametros],
        )

    def _escopo_atual(self):
        return self.escopos[-1]

    def _declarar_variavel(self, nome, tipo, no=None):
        if tipo not in self.TIPOS:
            self._erro(f"tipo '{tipo}' inválido para a variável '{nome}'.", no)
        if nome in self._escopo_atual():
            self._erro(f"a variável '{nome}' foi declarada mais de uma vez no mesmo escopo.", no)
        if len(self.escopos) == 1 and nome in self.funcoes:
            self._erro(f"'{nome}' já foi declarado como função e não pode ser variável global.", no)
        self._escopo_atual()[nome] = tipo
        self.tabela_simbolos.registrar(
            nome,
            tipo,
            "variavel",
            self._escopo_nome_atual(),
            getattr(no, "linha", None),
        )

    def _buscar_variavel(self, nome):
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        return None

    def _analisar_declaracao(self, no):
        # A variável ainda não existe durante a avaliação do próprio inicializador.
        if no.inicializacao is not None:
            tipo_inicial = self._inferir_tipo(no.inicializacao)
            if tipo_inicial != no.tipo:
                self._erro(
                    f"inicialização de '{no.nome}' espera '{no.tipo}', "
                    f"mas recebeu '{tipo_inicial}'.",
                    no,
                )
        self._declarar_variavel(no.nome, no.tipo, no)

    def _analisar_funcao(self, funcao):
        self.funcao_atual = funcao.nome
        self.tipo_retorno_atual = funcao.tipo_retorno
        self.escopos.append({})  # Parâmetros e variáveis do corpo compartilham escopo.
        try:
            for parametro in funcao.parametros:
                self._declarar_variavel(parametro.nome, parametro.tipo, parametro)
            self._analisar_bloco(funcao.corpo, criar_escopo=False)
            if not self._retorna_em_todos_os_caminhos(funcao.corpo):
                self._erro(
                    f"a função '{funcao.nome}', que retorna '{funcao.tipo_retorno}', "
                    "pode terminar sem executar um return.",
                    funcao,
                )
        finally:
            self.escopos.pop()
            self.funcao_atual = None
            self.tipo_retorno_atual = None

    def _analisar_bloco(self, bloco, criar_escopo=True):
        if criar_escopo:
            self.escopos.append({})
        try:
            for comando in bloco.comandos:
                self._analisar_comando(comando)
        finally:
            if criar_escopo:
                self.escopos.pop()

    def _analisar_atribuicao(self, no):
        tipo_variavel = self._buscar_variavel(no.nome)
        if tipo_variavel is None:
            if no.nome in self.funcoes:
                self._erro(f"'{no.nome}' é uma função, não uma variável atribuível.", no)
            self._erro(f"a variável '{no.nome}' foi usada antes de ser declarada.", no)
        tipo_expressao = self._inferir_tipo(no.expressao)
        if tipo_expressao != tipo_variavel:
            self._erro(
                f"não é possível atribuir '{tipo_expressao}' à variável '{no.nome}', "
                f"que é do tipo '{tipo_variavel}'.",
                no,
            )

    def _analisar_comando(self, no):
        if isinstance(no, Declaracao):
            self._analisar_declaracao(no)
        elif isinstance(no, Atribuicao):
            self._analisar_atribuicao(no)
        elif isinstance(no, Bloco):
            self._analisar_bloco(no)
        elif isinstance(no, If):
            tipo = self._inferir_tipo(no.condicao)
            if tipo != "bool":
                self._erro(f"a condição de if deve ser 'bool', não '{tipo}'.", no)
            self._analisar_bloco(no.bloco_if)
            if no.bloco_else is not None:
                self._analisar_bloco(no.bloco_else)
        elif isinstance(no, While):
            tipo = self._inferir_tipo(no.condicao)
            if tipo != "bool":
                self._erro(f"a condição de while deve ser 'bool', não '{tipo}'.", no)
            self._analisar_bloco(no.corpo)
        elif isinstance(no, For):
            self._analisar_atribuicao(no.inicializacao)
            tipo = self._inferir_tipo(no.condicao)
            if tipo != "bool":
                self._erro(f"a condição de for deve ser 'bool', não '{tipo}'.", no)
            self._analisar_atribuicao(no.incremento)
            self._analisar_bloco(no.corpo)
        elif isinstance(no, Scan):
            if self._buscar_variavel(no.nome) is None:
                self._erro(f"scan usa a variável '{no.nome}', que não foi declarada.", no)
        elif isinstance(no, Print):
            tipo = self._inferir_tipo(no.valor)
            if tipo not in {"int", "bool", "string"}:
                self._erro(f"print não pode receber um valor do tipo '{tipo}'.", no)
        elif isinstance(no, Return):
            if self.tipo_retorno_atual is None:
                self._erro("return só pode aparecer dentro de uma função.", no)
            tipo = self._inferir_tipo(no.expressao)
            if tipo != self.tipo_retorno_atual:
                self._erro(
                    f"return da função '{self.funcao_atual}' deveria retornar "
                    f"'{self.tipo_retorno_atual}', mas recebeu '{tipo}'.",
                    no,
                )
        elif isinstance(no, ChamadaFuncao):
            self._inferir_tipo(no)
        else:
            self._erro(f"nó de comando não reconhecido: {type(no).__name__}.", no)

    def _inferir_tipo(self, no):
        if isinstance(no, Numero):
            return "int"
        if isinstance(no, Booleano):
            return "bool"
        if isinstance(no, String):
            return "string"
        if isinstance(no, Identificador):
            tipo = self._buscar_variavel(no.nome)
            if tipo is None:
                if no.nome in self.funcoes:
                    self._erro(f"'{no.nome}' é uma função e não pode ser usada como variável.", no)
                self._erro(f"a variável '{no.nome}' foi usada antes de ser declarada.", no)
            return tipo
        if isinstance(no, ChamadaFuncao):
            if self._buscar_variavel(no.nome) is not None:
                self._erro(f"'{no.nome}' é uma variável, não uma função.", no)
            funcao = self.funcoes.get(no.nome)
            if funcao is None:
                self._erro(f"a função '{no.nome}' não foi declarada.", no)
            esperados = funcao["parametros"]
            if len(no.argumentos) != len(esperados):
                self._erro(
                    f"a função '{no.nome}' espera {len(esperados)} argumento(s), "
                    f"mas recebeu {len(no.argumentos)}.",
                    no,
                )
            for indice, (argumento, tipo_esperado) in enumerate(zip(no.argumentos, esperados), start=1):
                tipo_real = self._inferir_tipo(argumento)
                if tipo_real != tipo_esperado:
                    self._erro(
                        f"o argumento {indice} de '{no.nome}' deveria ser '{tipo_esperado}', "
                        f"mas recebeu '{tipo_real}'.",
                        no,
                    )
            return funcao["retorno"]
        if isinstance(no, OperacaoUnaria):
            tipo = self._inferir_tipo(no.operando)
            if no.operador in {"-", "+"}:
                if tipo != "int":
                    self._erro(f"o operador unário '{no.operador}' exige 'int', mas recebeu '{tipo}'.", no)
                return "int"
            if no.operador == "!":
                if tipo != "bool":
                    self._erro(f"o operador '!' exige 'bool', mas recebeu '{tipo}'.", no)
                return "bool"
            self._erro(f"operador unário '{no.operador}' não reconhecido.", no)
        if isinstance(no, OperacaoBinaria):
            tipo_esquerda = self._inferir_tipo(no.esquerda)
            tipo_direita = self._inferir_tipo(no.direita)
            op = no.operador
            if op in self.OPERADORES_ARITMETICOS:
                if tipo_esquerda != "int" or tipo_direita != "int":
                    self._erro(
                        f"o operador '{op}' exige operandos 'int', mas recebeu "
                        f"'{tipo_esquerda}' e '{tipo_direita}'.",
                        no,
                    )
                return "int"
            if op in self.OPERADORES_RELACIONAIS:
                if tipo_esquerda != "int" or tipo_direita != "int":
                    self._erro(
                        f"o operador '{op}' exige operandos 'int', mas recebeu "
                        f"'{tipo_esquerda}' e '{tipo_direita}'.",
                        no,
                    )
                return "bool"
            if op in self.OPERADORES_IGUALDADE:
                if tipo_esquerda != tipo_direita or tipo_esquerda not in self.TIPOS:
                    self._erro(
                        f"o operador '{op}' exige operandos do mesmo tipo ('int' ou 'bool'), "
                        f"mas recebeu '{tipo_esquerda}' e '{tipo_direita}'.",
                        no,
                    )
                return "bool"
            if op in self.OPERADORES_LOGICOS:
                if tipo_esquerda != "bool" or tipo_direita != "bool":
                    self._erro(
                        f"o operador '{op}' exige operandos 'bool', mas recebeu "
                        f"'{tipo_esquerda}' e '{tipo_direita}'.",
                        no,
                    )
                return "bool"
            self._erro(f"operador binário '{op}' não reconhecido.", no)
        self._erro(f"expressão não reconhecida: {type(no).__name__}.", no)

    def _retorna_em_todos_os_caminhos(self, no):
        """Verificação simples de retorno garantido; laços não contam como garantia."""
        if isinstance(no, Return):
            return True
        if isinstance(no, Bloco):
            return any(self._retorna_em_todos_os_caminhos(cmd) for cmd in no.comandos)
        if isinstance(no, If):
            if no.bloco_else is None:
                return False
            return (
                self._retorna_em_todos_os_caminhos(no.bloco_if)
                and self._retorna_em_todos_os_caminhos(no.bloco_else)
            )
        return False

    def gerar_tabela_simbolos(self):
        return self.tabela_simbolos.gerar()
