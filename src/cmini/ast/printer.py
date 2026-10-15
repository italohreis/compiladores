from pathlib import Path
import html
import textwrap
import webbrowser
from .nodes import ASTNode


CORES = {
    "Programa": "#D6EAF8",
    "Funcao": "#D6EAF8",
    "Bloco": "#D6EAF8",
    "Declaracao": "#D5F5E3",
    "Atribuicao": "#D5F5E3",
    "If": "#FDEBD0",
    "While": "#FDEBD0",
    "For": "#FDEBD0",
    "Print": "#D5F5E3",
    "Scan": "#D5F5E3",
    "Return": "#D5F5E3",
    "ChamadaFuncao": "#E8DAEF",
    "OperacaoBinaria": "#FCF3CF",
    "OperacaoUnaria": "#FCF3CF",
}

LARGURA_MINIMA = 145
LARGURA_MAXIMA = 260
ESPACO_HORIZONTAL = 32
ESPACO_VERTICAL = 65


class NoVisual:
    def __init__(self, linhas, cor="#F4F6F7"):
        self.linhas = linhas
        self.cor = cor
        self.filhos = []
        self.largura = min(
            LARGURA_MAXIMA,
            max(LARGURA_MINIMA, int(max(map(len, linhas)) * 7.2 + 24))
        )
        self.altura = 20 + len(linhas) * 18
        self.largura_subarvore = self.largura
        self.x = 0
        self.y = 0


def quebrar_texto(texto, limite=30):
    return textwrap.wrap(
        str(texto),
        width=limite,
        break_long_words=True,
        break_on_hyphens=False
    ) or [""]


def construir_arvore(no):
    if not isinstance(no, ASTNode):
        return NoVisual(quebrar_texto(repr(no)))

    nome_classe = type(no).__name__
    linhas = [nome_classe]
    atributos_filhos = []

    for nome, valor in vars(no).items():
        if valor is None:
            continue

        if isinstance(valor, ASTNode) or isinstance(valor, list):
            atributos_filhos.append((nome, valor))
        else:
            representacao = repr(valor)
            linhas.extend(quebrar_texto(f"{nome}: {representacao}", 30))

    visual = NoVisual(linhas, CORES.get(nome_classe, "#F4F6F7"))

    for nome, valor in atributos_filhos:
        if isinstance(valor, ASTNode):
            visual.filhos.append((construir_arvore(valor), nome))
        else:
            lista_visual = NoVisual([nome], "#F8F9F9")

            if valor:
                for item in valor:
                    if isinstance(item, ASTNode):
                        lista_visual.filhos.append((construir_arvore(item), ""))
                    else:
                        lista_visual.filhos.append(
                            (NoVisual(quebrar_texto(repr(item))), "")
                        )
            else:
                lista_visual.filhos.append((NoVisual(["(vazio)"]), ""))

            visual.filhos.append((lista_visual, ""))

    return visual


def calcular_larguras(no):
    for filho, _ in no.filhos:
        calcular_larguras(filho)

    if no.filhos:
        largura_filhos = (
            sum(filho.largura_subarvore for filho, _ in no.filhos)
            + ESPACO_HORIZONTAL * (len(no.filhos) - 1)
        )
        no.largura_subarvore = max(no.largura, largura_filhos)


def posicionar_horizontalmente(no, esquerda):
    no.x = esquerda + no.largura_subarvore / 2

    if not no.filhos:
        return

    largura_filhos = (
        sum(filho.largura_subarvore for filho, _ in no.filhos)
        + ESPACO_HORIZONTAL * (len(no.filhos) - 1)
    )

    cursor = esquerda + (no.largura_subarvore - largura_filhos) / 2

    for filho, _ in no.filhos:
        posicionar_horizontalmente(filho, cursor)
        cursor += filho.largura_subarvore + ESPACO_HORIZONTAL


def coletar_niveis(raiz):
    niveis = []

    def percorrer(no, nivel):
        if nivel == len(niveis):
            niveis.append([])

        niveis[nivel].append(no)

        for filho, _ in no.filhos:
            percorrer(filho, nivel + 1)

    percorrer(raiz, 0)
    return niveis


def desenhar_nos_e_conexoes(raiz, altura):
    elementos = []

    def percorrer(no):
        x_esquerda = no.x - no.largura / 2
        y_topo = no.y
        y_base = y_topo + no.altura

        for filho, rotulo in no.filhos:
            inicio_y = y_base
            fim_y = filho.y
            meio_y = (inicio_y + fim_y) / 2

            elementos.append(
                f'<path d="M {no.x:.1f} {inicio_y:.1f} '
                f'C {no.x:.1f} {meio_y:.1f}, '
                f'{filho.x:.1f} {meio_y:.1f}, '
                f'{filho.x:.1f} {fim_y:.1f}" '
                'fill="none" stroke="#8293A5" stroke-width="1.5"/>'
            )

            if rotulo:
                rotulo_html = html.escape(rotulo)
                elementos.append(
                    f'<text x="{(no.x + filho.x) / 2:.1f}" '
                    f'y="{meio_y - 4:.1f}" text-anchor="middle" '
                    'font-family="Arial" font-size="11" '
                    'fill="#526579" '
                    'style="paint-order:stroke;stroke:#F5F7FA;'
                    'stroke-width:5px">'
                    f'{rotulo_html}</text>'
                )

            percorrer(filho)

        elementos.append(
            f'<rect x="{x_esquerda:.1f}" y="{y_topo:.1f}" '
            f'width="{no.largura}" height="{no.altura}" rx="8" '
            f'fill="{no.cor}" stroke="#60758A" stroke-width="1.2"/>'
        )

        for indice, linha in enumerate(no.linhas):
            tamanho = 12 if indice == 0 else 11
            peso = "700" if indice == 0 else "400"
            y_texto = y_topo + 20 + indice * 18
            elementos.append(
                f'<text x="{x_esquerda + 12:.1f}" y="{y_texto:.1f}" '
                f'font-family="Consolas, monospace" '
                f'font-size="{tamanho}" font-weight="{peso}" '
                f'fill="#243447">{html.escape(linha)}</text>'
            )

    percorrer(raiz)
    return "\n".join(elementos)


def gerar_ast(raiz, arquivo="saida/ast_cmini.html", abrir=True):
    if not isinstance(raiz, ASTNode):
        raise TypeError("A raiz recebida não é um nó válido da AST.")

    arvore = construir_arvore(raiz)
    calcular_larguras(arvore)
    posicionar_horizontalmente(arvore, 30)

    niveis = coletar_niveis(arvore)
    topo = 25

    for nivel in niveis:
        altura_nivel = max(no.altura for no in nivel)

        for no in nivel:
            no.y = topo + (altura_nivel - no.altura) / 2

        topo += altura_nivel + ESPACO_VERTICAL

    largura_svg = int(arvore.largura_subarvore + 60)
    altura_svg = int(topo + 10)
    conteudo_svg = desenhar_nos_e_conexoes(arvore, altura_svg)

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg"
         width="{largura_svg}" height="{altura_svg}"
         viewBox="0 0 {largura_svg} {altura_svg}">
        <rect width="100%" height="100%" fill="#F5F7FA"/>
        {conteudo_svg}
    </svg>
    """

    documento = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AST - C Mini</title>
<style>
body {{
    margin: 0;
    background: #F5F7FA;
    color: #243447;
    font-family: Arial, sans-serif;
}}
header {{
    padding: 16px 22px;
    background: white;
    border-bottom: 1px solid #DCE3EA;
}}
h1 {{ font-size: 20px; margin: 0 0 6px; }}
p {{ font-size: 13px; margin: 0; color: #627386; }}
main {{ height: calc(100vh - 76px); overflow: auto; }}
svg {{ display: block; }}
</style>
</head>
<body>
<header>
    <h1>Árvore Sintática Abstrata — C Mini</h1>
</header>
<main>
{svg}
</main>
</body>
</html>
"""

    destino = Path(arquivo)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(documento, encoding="utf-8")

    caminho = destino.resolve()

    if abrir:
        webbrowser.open(caminho.as_uri())

    return str(caminho)