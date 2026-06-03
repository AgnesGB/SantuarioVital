#!/usr/bin/env python3
"""
Gerador de Diagrama de Classes UML em Mermaid para projetos Django.
Lê os models do projeto e gera um HTML com o diagrama renderizado.
"""

import ast
import os
import sys
import re
from pathlib import Path
from datetime import datetime

# Mapeamento de campos Django para tipos legíveis
FIELD_TYPE_MAP = {
    "CharField": "String",
    "TextField": "Text",
    "IntegerField": "Integer",
    "PositiveIntegerField": "Integer+",
    "FloatField": "Float",
    "BooleanField": "Boolean",
    "DateField": "Date",
    "DateTimeField": "DateTime",
    "EmailField": "Email",
    "URLField": "URL",
    "ForeignKey": "FK",
    "ManyToManyField": "M2M",
    "OneToOneField": "O2O",
    "ImageField": "Image",
    "FileField": "File",
    "SlugField": "Slug",
    "UUIDField": "UUID",
    "JSONField": "JSON",
    "DecimalField": "Decimal",
}

SKIP_CLASSES = {"Meta", "Migration", "Admin"}
SKIP_FIELDS = {"id"}


def extract_classes_from_file(filepath: Path) -> list[dict]:
    """Extrai classes e seus campos de um arquivo Python usando AST."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as e:
        print(f"  Aviso: não foi possível parsear {filepath}: {e}", file=sys.stderr)
        return []

    classes = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if node.name in SKIP_CLASSES or node.name.startswith("_"):
            continue

        # Pega herança
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Attribute):
                bases.append(base.attr)
            elif isinstance(base, ast.Name):
                bases.append(base.id)

        # Ignora classes que não são models Django
        is_model = any(
            b in ("Model", "AbstractModel", "AbstractBaseUser", "AbstractUser")
            for b in bases
        ) or any("Model" in b for b in bases)

        fields = []
        relations = []

        for item in node.body:
            # Campos: nome = TipoField(...)
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    field_name = target.id
                    if field_name in SKIP_FIELDS or field_name.startswith("_"):
                        continue
                    if field_name.isupper():  # constantes como STATUS_CHOICES
                        continue

                    field_type = ""
                    related_to = None

                    if isinstance(item.value, ast.Call):
                        func = item.value.func
                        if isinstance(func, ast.Attribute):
                            field_type = func.attr
                        elif isinstance(func, ast.Name):
                            field_type = func.id

                        # Detecta relacionamentos (primeiro argumento posicional)
                        if field_type in ("ForeignKey", "ManyToManyField", "OneToOneField"):
                            args = item.value.args
                            if args:
                                arg = args[0]
                                if isinstance(arg, ast.Constant):
                                    related_to = str(arg.value).split(".")[-1]
                                elif isinstance(arg, ast.Attribute):
                                    related_to = arg.attr
                                elif isinstance(arg, ast.Name):
                                    related_to = arg.id

                    if field_type:
                        short_type = FIELD_TYPE_MAP.get(field_type, field_type)
                        fields.append({
                            "name": field_name,
                            "type": short_type,
                            "raw_type": field_type,
                        })
                        if related_to and related_to not in ("self", "AUTH_USER_MODEL"):
                            relations.append({
                                "from": node.name,
                                "to": related_to,
                                "type": field_type,
                                "field": field_name,
                            })

        classes.append({
            "name": node.name,
            "bases": bases,
            "fields": fields,
            "relations": relations,
            "is_model": is_model,
            "file": str(filepath),
        })

    return classes


def find_models_files(project_root: Path) -> list[Path]:
    """Encontra todos os arquivos models.py no projeto."""
    model_files = []

    # Procura models.py direto
    for path in project_root.rglob("models.py"):
        if any(part.startswith(".") for part in path.parts):
            continue
        if "migrations" in path.parts:
            continue
        if "venv" in path.parts or "env" in path.parts or "node_modules" in path.parts:
            continue
        model_files.append(path)

    # Procura pastas models/ com __init__.py ou arquivos .py
    for path in project_root.rglob("models"):
        if path.is_dir():
            if any(part.startswith(".") for part in path.parts):
                continue
            for py_file in path.glob("*.py"):
                if py_file.name != "__init__.py":
                    model_files.append(py_file)

    return model_files


def generate_mermaid(classes: list[dict]) -> str:
    """Gera o código Mermaid a partir das classes extraídas."""
    lines = ["classDiagram"]
    lines.append("    direction TB")
    lines.append("")

    # Filtra só os models (ou todas as classes se não houver models identificados)
    models = [c for c in classes if c["is_model"]]
    if not models:
        models = [c for c in classes if c["name"] not in SKIP_CLASSES]

    known_names = {c["name"] for c in models}
    all_relations = []

    for cls in models:
        lines.append(f'    class {cls["name"]} {{')
        for field in cls["fields"]:
            lines.append(f'        +{field["type"]} {field["name"]}')
        lines.append("    }")
        lines.append("")

        for rel in cls["relations"]:
            if rel["to"] in known_names:
                all_relations.append(rel)

    # Adiciona herança
    for cls in models:
        for base in cls["bases"]:
            if base in known_names:
                lines.append(f'    {base} <|-- {cls["name"]} : herda')

    # Adiciona relacionamentos
    seen_relations = set()
    for rel in all_relations:
        key = (rel["from"], rel["to"], rel["type"])
        if key in seen_relations:
            continue
        seen_relations.add(key)

        if rel["type"] == "ForeignKey":
            lines.append(f'    {rel["from"]} --> {rel["to"]} : {rel["field"]}')
        elif rel["type"] == "ManyToManyField":
            lines.append(f'    {rel["from"]} "N" -- "N" {rel["to"]} : {rel["field"]}')
        elif rel["type"] == "OneToOneField":
            lines.append(f'    {rel["from"]} "1" -- "1" {rel["to"]} : {rel["field"]}')

    return "\n".join(lines)


def generate_html(mermaid_code: str, project_name: str = "Projeto") -> str:
    """Gera HTML com o diagrama Mermaid estilizado."""
    now = datetime.now().strftime("%d/%m/%Y às %H:%M")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{project_name} — Diagrama UML</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
  <style>
    :root {{
      --bg: #0d0f14;
      --surface: #13161e;
      --border: #1e2330;
      --accent: #7c6af7;
      --accent2: #3ecfcf;
      --text: #e8eaf0;
      --muted: #6b7280;
      --glow: rgba(124, 106, 247, 0.15);
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Syne', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem;
    }}

    body::before {{
      content: '';
      position: fixed;
      top: -40%;
      left: -10%;
      width: 60vw;
      height: 60vw;
      background: radial-gradient(circle, rgba(124,106,247,0.07) 0%, transparent 70%);
      pointer-events: none;
      z-index: 0;
    }}

    .wrapper {{
      position: relative;
      z-index: 1;
      max-width: 1400px;
      margin: 0 auto;
    }}

    header {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 2.5rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
    }}

    .title-block h1 {{
      font-size: clamp(1.8rem, 4vw, 3rem);
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1;
      background: linear-gradient(135deg, var(--text) 40%, var(--accent));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}

    .title-block p {{
      margin-top: 0.4rem;
      font-size: 0.85rem;
      color: var(--muted);
      font-family: 'JetBrains Mono', monospace;
    }}

    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.35rem 0.75rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 999px;
      font-size: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--accent2);
      white-space: nowrap;
    }}

    .badge::before {{
      content: '';
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--accent2);
      animation: pulse 2s infinite;
    }}

    @keyframes pulse {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.4; }}
    }}

    .diagram-container {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 2rem;
      overflow: auto;
      box-shadow: 0 0 60px var(--glow), 0 4px 24px rgba(0,0,0,0.4);
      position: relative;
    }}

    .diagram-container::before {{
      content: 'DIAGRAMA DE CLASSES';
      position: absolute;
      top: 1rem;
      right: 1.5rem;
      font-size: 0.65rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--muted);
      letter-spacing: 0.15em;
    }}

    .mermaid {{
      display: flex;
      justify-content: center;
    }}

    .mermaid svg {{
      max-width: 100%;
      height: auto;
    }}

    footer {{
      margin-top: 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.5rem;
    }}

    footer span {{
      font-size: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--muted);
    }}

    footer a {{
      color: var(--accent);
      text-decoration: none;
    }}

    .controls {{
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
      flex-wrap: wrap;
    }}

    button {{
      font-family: 'Syne', sans-serif;
      font-size: 0.8rem;
      font-weight: 600;
      padding: 0.45rem 1rem;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: transparent;
      color: var(--text);
      cursor: pointer;
      transition: all 0.2s;
    }}

    button:hover {{
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }}

    pre.code-block {{
      background: #080a0f;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      color: #a8b5c8;
      overflow: auto;
      max-height: 300px;
      display: none;
      margin-top: 1rem;
    }}

    pre.code-block.visible {{
      display: block;
    }}
  </style>
</head>
<body>
<div class="wrapper">
  <header>
    <div class="title-block">
      <h1>{project_name}</h1>
      <p>Diagrama de Classes UML · gerado em {now}</p>
    </div>
    <span class="badge">auto-gerado · Mermaid v11</span>
  </header>

  <div class="controls">
    <button onclick="toggleCode()">&#60;/&#62; Ver código Mermaid</button>
    <button onclick="window.print()">⬇ Exportar</button>
  </div>

  <pre class="code-block" id="mermaid-source">{mermaid_code}</pre>

  <div class="diagram-container">
    <div class="mermaid">
{mermaid_code}
    </div>
  </div>

  <footer>
    <span>gerado por <strong>generate_uml.py</strong></span>
    <span>Mermaid.js · {project_name}</span>
  </footer>
</div>

<script>
  mermaid.initialize({{
    startOnLoad: true,
    theme: 'dark',
    themeVariables: {{
      primaryColor: '#1e2330',
      primaryTextColor: '#e8eaf0',
      primaryBorderColor: '#7c6af7',
      lineColor: '#3ecfcf',
      secondaryColor: '#13161e',
      tertiaryColor: '#0d0f14',
      background: '#0d0f14',
      mainBkg: '#13161e',
      nodeBorder: '#7c6af7',
      clusterBkg: '#1e2330',
      titleColor: '#e8eaf0',
      edgeLabelBackground: '#1e2330',
      attributeBackgroundColorEven: '#13161e',
      attributeBackgroundColorOdd: '#1a1f2e',
    }},
    classDiagram: {{
      diagramPadding: 20,
    }},
  }});

  function toggleCode() {{
    const el = document.getElementById('mermaid-source');
    el.classList.toggle('visible');
  }}
</script>
</body>
</html>"""


def main():
    # Descobre o root do projeto
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1]).resolve()
    else:
        project_root = Path(".").resolve()

    output_file = Path("docs/uml/classes.html")
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])

    project_name = project_root.name.replace("-", " ").replace("_", " ").title()

    print(f"🔍 Analisando projeto: {project_root}")

    model_files = find_models_files(project_root)
    if not model_files:
        print("⚠️  Nenhum arquivo models.py encontrado.", file=sys.stderr)
        sys.exit(1)

    print(f"📂 Arquivos encontrados: {len(model_files)}")
    for f in model_files:
        print(f"   - {f.relative_to(project_root)}")

    all_classes = []
    for filepath in model_files:
        classes = extract_classes_from_file(filepath)
        all_classes.extend(classes)
        print(f"   ✓ {len(classes)} classe(s) em {filepath.name}")

    if not all_classes:
        print("⚠️  Nenhuma classe encontrada.", file=sys.stderr)
        sys.exit(1)

    print(f"\n📊 Total de classes: {len(all_classes)}")

    mermaid_code = generate_mermaid(all_classes)
    html = generate_html(mermaid_code, project_name)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding="utf-8")

    print(f"\n✅ Diagrama gerado: {output_file}")


if __name__ == "__main__":
    main()
