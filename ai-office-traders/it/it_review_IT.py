import os
import sys
import ast
import re
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for d in ["core", "data", "llm"]:
    sys.path.insert(0, os.path.join(BASE_DIR, d))


def code_review_IT() -> list[str]:
    findings = []

    findings.extend(_check_code_style())
    findings.extend(_check_imports())
    findings.extend(_check_code_complexity())
    findings.extend(_check_security())
    findings.extend(_check_line_length())
    findings.extend(_check_documentation())
    findings.extend(_check_typing())
    findings.extend(_check_naming_conventions())
    findings.extend(_check_comments())
    findings.extend(_check_code_duplication())

    return findings


def _check_code_style() -> list[str]:
    findings = []
    py_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".py")]

    long_functions = []
    for fname in py_files:
        fpath = os.path.join(os.path.dirname(__file__), fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            func_count = sum(1 for l in lines if l.strip().startswith("def "))
            if func_count > 20:
                long_functions.append((fname, func_count))
        except Exception:
            pass

    if long_functions:
        for name, count in sorted(long_functions, key=lambda x: x[1], reverse=True)[:3]:
            findings.append(f"💡 {name}: {count} функций — стоит разделить")
    else:
        findings.append("✅ Все файлы имеют разумное количество функций")
    return findings


def _check_imports() -> list[str]:
    findings = []
    py_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".py")]

    unused_imports = []
    for fname in py_files:
        fpath = os.path.join(os.path.dirname(__file__), fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            imports = [l.strip().split("import")[1].strip() for l in content.split("\n")
                      if l.strip().startswith("import ") and "import" in l]
            for imp in imports:
                if imp not in content.replace(f"import {imp}", ""):
                    unused_imports.append((fname, imp))
        except Exception:
            pass

    if unused_imports:
        findings.append(f"💡 {len(unused_imports)} неиспользуемых импортов")
    else:
        findings.append("✅ Все импорты используются")
    return findings


def _check_code_complexity() -> list[str]:
    findings = []
    py_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".py")]

    for fname in py_files:
        fpath = os.path.join(os.path.dirname(__file__), fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = _calc_complexity(node)
                    if complexity > 10:
                        findings.append(f"💡 {fname}:{node.name} сложность {complexity}")
        except Exception:
            pass

    return findings if findings else ["✅ Сложность кода в норме"]


def _calc_complexity(node: ast.FunctionDef) -> int:
    c = 1
    for item in ast.walk(node):
        if isinstance(item, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
            c += 1
        elif isinstance(item, ast.BoolOp):
            c += 1
        elif isinstance(item, ast.Compare):
            c += len(item.ops)
    return c


def _check_security() -> list[str]:
    findings = []
    py_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".py")]

    for fname in py_files:
        fpath = os.path.join(os.path.dirname(__file__), fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            if "eval(" in content:
                findings.append(f"🔒 {fname}: используется eval()")
            if "pickle.load" in content:
                findings.append(f"🔒 {fname}: pickle.load без проверки")
        except Exception:
            pass

    return findings if findings else ["✅ Проблем безопасности нет"]


def _check_line_length() -> list[str]:
    findings = []
    py_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".py")]
    max_len = 120

    for fname in py_files:
        fpath = os.path.join(os.path.dirname(__file__), fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            long = [(i+1, len(l.rstrip())) for i, l in enumerate(lines) if len(l.rstrip()) > max_len]
            if long:
                findings.append(f"📏 {fname}: {len(long)} длинных строк")
        except Exception:
            pass

    return findings if findings else [f"✅ Все строки < {max_len} символов"]


def _check_documentation() -> list[str]:
    findings = []
    py_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".py") and f != "__init__.py"]
    for fname in py_files:
        fpath = os.path.join(os.path.dirname(__file__), fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            if not ast.get_docstring(tree):
                findings.append(f"📝 {fname}: нет docstring модуля")
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and not ast.get_docstring(node):
                    findings.append(f"📝 {fname}: класс {node.name} без docstring")
                elif isinstance(node, ast.FunctionDef) and not ast.get_docstring(node):
                    findings.append(f"📝 {fname}: {node.name}() без docstring")
        except Exception:
            pass
    return findings if findings else ["✅ Документация в порядке"]


def _check_typing() -> list[str]:
    findings = []
    py_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".py")]
    for fname in py_files:
        fpath = os.path.join(os.path.dirname(__file__), fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            total = 0
            typed = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    total += 1
                    if node.returns is not None:
                        typed += 1
            if total > 0:
                pct = typed / total * 100
                if pct < 50:
                    findings.append(f"🔤 {fname}: типизация {pct:.0f}%")
        except Exception:
            pass
    return findings if findings else ["✅ Типизация в порядке"]


def _check_naming_conventions() -> list[str]:
    findings = []
    py_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".py")]
    for fname in py_files:
        fpath = os.path.join(os.path.dirname(__file__), fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not re.match(r'^[a-z][a-z0-9_]*$', node.name) and node.name != "__init__":
                        findings.append(f"📛 {fname}: {node.name} ≠ snake_case")
                elif isinstance(node, ast.ClassDef):
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                        findings.append(f"📛 {fname}: {node.name} ≠ PascalCase")
        except Exception:
            pass
    return findings if findings else ["✅ Именование OK"]


def _check_comments() -> list[str]:
    findings = []
    py_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".py")]
    for fname in py_files:
        fpath = os.path.join(os.path.dirname(__file__), fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            code = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
            comments = sum(1 for l in lines if l.strip().startswith("#"))
            if code > 0 and comments / code * 100 < 5:
                findings.append(f"💬 {fname}: мало комментариев")
        except Exception:
            pass
    return findings if findings else ["✅ Комментарии OK"]


def _check_code_duplication() -> list[str]:
    findings = []
    py_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".py")]
    snippets = {}
    for fname in py_files:
        fpath = os.path.join(os.path.dirname(__file__), fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    src = ast.get_source_segment(content, node)
                    if src:
                        fp = "\n".join(src.split("\n")[:3])
                        snippets.setdefault(fp, []).append(fname)
        except Exception:
            pass
    for fp, files in snippets.items():
        if len(files) > 1:
            findings.append(f"🔄 Дублирование: {', '.join(set(files))}")
    return findings if findings else ["✅ Дублирования нет"]
