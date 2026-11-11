import argparse
import subprocess
import sys
from pathlib import Path

from src.cmini.ast.printer import gerar_ast
from src.cmini.codegen import CCodeGenerator
from src.cmini.lexer.lexer import LexicalAnalyzer
from src.cmini.parser.parser import Parser, ParserError
from src.cmini.semantic.analyzer import SemanticAnalyzer, SemanticError


ROOT = Path(__file__).resolve().parent


def read_code_from_file(file_path):
    return file_path.read_text(encoding="utf-8")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Compilador C Mini: analisa um arquivo .cm e gera um executável C."
    )
    parser.add_argument("arquivo", type=Path, help="caminho do arquivo-fonte C Mini (.cm)")
    parser.add_argument(
        "--run",
        action="store_true",
        help="executa o programa gerado depois da compilação",
    )
    parser.add_argument(
        "--ast",
        action="store_true",
        help="gera também a visualização HTML da AST",
    )
    return parser.parse_args()


def compiler_command(source_c, executable):
    return [
        "gcc",
        "-Wall",
        "-Wextra",
        "-std=c11",
        str(source_c),
        "-o",
        str(executable),
    ]


def compile_file(file_path, run=False, generate_ast=False):
    file_path = file_path.resolve()
    if not file_path.is_file():
        raise FileNotFoundError(f"arquivo não encontrado: {file_path}")
    if file_path.suffix.lower() != ".cm":
        raise ValueError("o arquivo de entrada deve ter a extensão .cm")

    code = read_code_from_file(file_path)
    tokens = LexicalAnalyzer().analyze(code)
    ast = Parser(tokens).parse()
    print("Análise sintática concluída com sucesso!")

    semantic_analyzer = SemanticAnalyzer()
    semantic_analyzer.analisar(ast)
    print("Análise semântica concluída com sucesso!")

    output_dir = ROOT / "saida"
    output_dir.mkdir(exist_ok=True)
    base_name = file_path.stem
    source_c = output_dir / f"{base_name}.c"
    executable = output_dir / (
        f"{base_name}.exe" if sys.platform == "win32" else base_name
    )

    if generate_ast:
        gerar_ast(ast, arquivo=str(output_dir / f"{base_name}_ast.html"), abrir=False)
        print(f"AST gerada em: {output_dir / f'{base_name}_ast.html'}")

    print("\nTabela de símbolos:")
    print(
        f"{'Nome':<18} {'Tipo':<10} {'Categoria':<12} "
        f"{'Escopo':<18} {'Linha':<8} Parâmetros"
    )
    print("-" * 90)
    for item in semantic_analyzer.gerar_tabela_simbolos():
        parametros = ", ".join(item.get("parametros", []))
        print(
            f"{item['nome']:<18} {item['tipo']:<10} "
            f"{item['categoria']:<12} {item['escopo']:<18} "
            f"{str(item['linha'] or '-'): <8} {parametros}"
        )

    source_c.write_text(CCodeGenerator().generate(ast), encoding="utf-8")
    print(f"\nCódigo C gerado em: {source_c}")

    command = compiler_command(source_c, executable)
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "GCC não foi encontrado. Instale o GCC e deixe-o disponível no PATH."
        ) from error

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"falha ao compilar o código C:\n{details}")

    print(f"Compilação concluída: {executable}")
    if run:
        print("\nExecução do programa:")
        completed = subprocess.run([str(executable)], cwd=ROOT, check=False)
        if completed.returncode != 0:
            raise RuntimeError(
                f"o programa terminou com código {completed.returncode}."
            )

    return source_c, executable


def main():
    arguments = parse_arguments()
    try:
        compile_file(arguments.arquivo, arguments.run, arguments.ast)
    except (OSError, SyntaxError, ParserError, SemanticError, ValueError, RuntimeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
