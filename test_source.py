from pathlib import Path
import ast


def test_source_parses():
    source = Path(__file__).parents[1] / "json_translator_windows.py"
    ast.parse(source.read_text(encoding="utf-8"))
