import json

from ..ast.nodes import (
    Atribuicao,
    Bloco,
    Booleano,
    ChamadaFuncao,
    Declaracao,
    Funcao,
    Identificador,
    If,
    Numero,
    OperacaoBinaria,
    OperacaoUnaria,
    Print,
    Programa,
    Return,
    Scan,
    String,
    While,
    For,
)


class CCodeGenerator:
    """Gera código C a partir de uma AST validada semanticamente."""

    INDENTACAO = "    "

    def __init__(self):
        self.nivel = 0
        self.escopos = []
        self.funcoes = {}
        self.contador_scan = 0
        self.globais = {}

    def generate(self, programa):
        if not isinstance(programa, Programa):
            raise TypeError("a raiz da AST deve ser um Programa.")

        self.nivel = 0
        self.escopos = []
        self.funcoes = {}
        self.contador_scan = 0
        self.globais = {
            elemento.nome: elemento.tipo
            for elemento in programa.elementos
            if isinstance(elemento, Declaracao)
        }

        funcoes = [elemento for elemento in programa.elementos if isinstance(elemento, Funcao)]
        declaracoes_globais = [
            elemento for elemento in programa.elementos if isinstance(elemento, Declaracao)
        ]
        comandos_globais = [
            elemento for elemento in programa.elementos if not isinstance(elemento, Funcao)
        ]
        self.funcoes = {
            funcao.nome: {
                "retorno": funcao.tipo_retorno,
                "parametros": [parametro.tipo for parametro in funcao.parametros],
            }
            for funcao in funcoes
        }

        partes = ["#include <stdio.h>", "#include <stdbool.h>", ""]
        if declaracoes_globais:
            partes.append(self._gerar_declaracoes_globais(declaracoes_globais))
            partes.append("")
        if funcoes:
            partes.append(self._gerar_prototipos(funcoes))
            partes.append("")
            partes.extend(self._gerar_funcao(funcao) for funcao in funcoes)
            partes.append("")

        partes.append(self._gerar_main(comandos_globais))
        return "\n".join(partes).rstrip() + "\n"

    def _gerar_prototipos(self, funcoes):
        return "\n".join(
            f"{self._tipo_c(funcao.tipo_retorno)} {funcao.nome}("
            f"{self._parametros(funcao.parametros)});"
            for funcao in funcoes
        )

    def _gerar_funcao(self, funcao):
        self.escopos.append(self.globais)
        self.escopos.append({parametro.nome: parametro.tipo for parametro in funcao.parametros})
        self.nivel += 1
        try:
            cabecalho = (
                f"{self._tipo_c(funcao.tipo_retorno)} {funcao.nome}"
                f"({self._parametros(funcao.parametros)}) {{"
            )
            corpo = self._gerar_comandos(funcao.corpo.comandos)
            return "\n".join([cabecalho, corpo, "}"])
        finally:
            self.nivel -= 1
            self.escopos.pop()
            self.escopos.pop()

    def _gerar_main(self, comandos):
        self.escopos.append(self.globais)
        self.escopos.append({})
        self.nivel += 1
        try:
            corpo = self._gerar_comandos(
                comandos,
                inicializacao_global=True,
            )
            linhas = ["int main(void) {", corpo]
            linhas.append(f"{self._indent()}return 0;")
            linhas.append("}")
            return "\n".join(linhas)
        finally:
            self.nivel -= 1
            self.escopos.pop()
            self.escopos.pop()

    def _gerar_comandos(self, comandos, inicializacao_global=False):
        if not comandos:
            return f"{self._indent()}/* programa sem comandos executáveis */"

        linhas = []
        for comando in comandos:
            if inicializacao_global and isinstance(comando, Declaracao):
                if comando.inicializacao is not None:
                    linhas.append(
                        f"{self._indent()}{comando.nome} = "
                        f"{self._gerar_expressao(comando.inicializacao)};"
                    )
            else:
                linhas.append(self._gerar_comando(comando))
        return "\n".join(linhas)

    def _gerar_declaracoes_globais(self, declaracoes):
        return "\n".join(
            f"{self._tipo_c(declaracao.tipo)} {declaracao.nome};"
            for declaracao in declaracoes
        )

    def _gerar_comando(self, no):
        if isinstance(no, Declaracao):
            inicializacao = ""
            if no.inicializacao is not None:
                inicializacao = f" = {self._gerar_expressao(no.inicializacao)}"
            self._escopo_atual()[no.nome] = no.tipo
            return f"{self._indent()}{self._tipo_c(no.tipo)} {no.nome}{inicializacao};"

        if isinstance(no, Atribuicao):
            return f"{self._indent()}{no.nome} = {self._gerar_expressao(no.expressao)};"

        if isinstance(no, Bloco):
            return self._gerar_bloco(no)

        if isinstance(no, If):
            linhas = [
                f"{self._indent()}if ({self._gerar_expressao(no.condicao)}) {{",
                self._gerar_bloco_conteudo(no.bloco_if),
                f"{self._indent()}}}",
            ]
            if no.bloco_else is not None:
                linhas.extend(
                    [
                        f"{self._indent()}else {{",
                        self._gerar_bloco_conteudo(no.bloco_else),
                        f"{self._indent()}}}",
                    ]
                )
            return "\n".join(linhas)

        if isinstance(no, While):
            return "\n".join(
                [
                    f"{self._indent()}while ({self._gerar_expressao(no.condicao)}) {{",
                    self._gerar_bloco_conteudo(no.corpo),
                    f"{self._indent()}}}",
                ]
            )

        if isinstance(no, For):
            return "\n".join(
                [
                    f"{self._indent()}for ({self._gerar_atribuicao_for(no.inicializacao)}; "
                    f"{self._gerar_expressao(no.condicao)}; "
                    f"{self._gerar_atribuicao_for(no.incremento)}) {{",
                    self._gerar_bloco_conteudo(no.corpo),
                    f"{self._indent()}}}",
                ]
            )

        if isinstance(no, Scan):
            return self._gerar_scan(no)

        if isinstance(no, Print):
            return self._gerar_print(no)

        if isinstance(no, Return):
            return f"{self._indent()}return {self._gerar_expressao(no.expressao)};"

        if isinstance(no, ChamadaFuncao):
            return f"{self._indent()}{self._gerar_expressao(no)};"

        raise TypeError(f"nó de comando não suportado: {type(no).__name__}.")

    def _gerar_bloco(self, bloco):
        linhas = [f"{self._indent()}{{"]
        linhas.append(self._gerar_bloco_conteudo(bloco))
        linhas.append(f"{self._indent()}}}")
        return "\n".join(linhas)

    def _gerar_bloco_conteudo(self, bloco):
        self.escopos.append({})
        self.nivel += 1
        try:
            return self._gerar_comandos(bloco.comandos)
        finally:
            self.nivel -= 1
            self.escopos.pop()

    def _gerar_atribuicao_for(self, atribuicao):
        return f"{atribuicao.nome} = {self._gerar_expressao(atribuicao.expressao)}"

    def _gerar_scan(self, no):
        tipo = self._buscar_tipo(no.nome)
        if tipo == "bool":
            temporario = f"__cmini_scan_{self.contador_scan}"
            self.contador_scan += 1
            return "\n".join(
                [
                    f"{self._indent()}int {temporario};",
                    f'{self._indent()}scanf("%d", &{temporario});',
                    f"{self._indent()}{no.nome} = ({temporario} != 0);",
                ]
            )
        return f'{self._indent()}scanf("%d", &{no.nome});'

    def _gerar_print(self, no):
        tipo = self._inferir_tipo(no.valor)
        expressao = self._gerar_expressao(no.valor)
        if tipo == "string":
            return f'{self._indent()}printf("%s", {expressao});'
        if tipo == "bool":
            return f'{self._indent()}printf("%s", {expressao} ? "true" : "false");'
        return f'{self._indent()}printf("%d", {expressao});'

    def _gerar_expressao(self, no):
        if isinstance(no, Numero):
            return str(no.valor)
        if isinstance(no, Booleano):
            return "true" if no.valor else "false"
        if isinstance(no, String):
            return json.dumps(no.valor, ensure_ascii=False)
        if isinstance(no, Identificador):
            return no.nome
        if isinstance(no, ChamadaFuncao):
            argumentos = ", ".join(self._gerar_expressao(argumento) for argumento in no.argumentos)
            return f"{no.nome}({argumentos})"
        if isinstance(no, OperacaoUnaria):
            return f"({no.operador}{self._gerar_expressao(no.operando)})"
        if isinstance(no, OperacaoBinaria):
            esquerda = self._gerar_expressao(no.esquerda)
            direita = self._gerar_expressao(no.direita)
            return f"({esquerda} {no.operador} {direita})"
        raise TypeError(f"nó de expressão não suportado: {type(no).__name__}.")

    def _inferir_tipo(self, no):
        if isinstance(no, Numero):
            return "int"
        if isinstance(no, Booleano):
            return "bool"
        if isinstance(no, String):
            return "string"
        if isinstance(no, Identificador):
            return self._buscar_tipo(no.nome)
        if isinstance(no, ChamadaFuncao):
            return self.funcoes[no.nome]["retorno"]
        if isinstance(no, OperacaoUnaria):
            return "bool" if no.operador == "!" else "int"
        if isinstance(no, OperacaoBinaria):
            return "bool" if no.operador in {"<", "<=", ">", ">=", "==", "!=", "&&", "||"} else "int"
        raise TypeError(f"não foi possível inferir o tipo de {type(no).__name__}.")

    def _buscar_tipo(self, nome):
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        raise KeyError(f"variável '{nome}' não encontrada durante a geração.")

    def _escopo_atual(self):
        return self.escopos[-1]

    def _parametros(self, parametros):
        return ", ".join(
            f"{self._tipo_c(parametro.tipo)} {parametro.nome}" for parametro in parametros
        ) or "void"

    @staticmethod
    def _tipo_c(tipo):
        if tipo == "int":
            return "int"
        if tipo == "bool":
            return "bool"
        raise ValueError(f"tipo C Mini não suportado na geração: {tipo}.")

    def _indent(self):
        return self.INDENTACAO * self.nivel
