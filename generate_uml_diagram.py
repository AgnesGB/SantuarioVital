#!/usr/bin/env python
"""
Script para gerar diagrama UML das classes de domínio.
Usa django-extensions para gerar um diagrama graphviz e converte para PNG.
"""

import os
import sys
import django
from pathlib import Path

# Add medsystem directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "medsystem"))

from django.core.management import call_command

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medsystem.settings")
django.setup()


def generate_html_visualization(dot_file: Path):
    """Generates HTML visualization of the DOT diagram using graphviz.js"""
    html_file = dot_file.with_suffix(".html")

    with open(dot_file, "r") as f:
        dot_content = f.read()

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SantuarioVital - Diagrama de Classes UML</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://unpkg.com/@hpcc-js/wasm@1.14.8/dist/graphviz.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-top: 0;
        }}
        .info {{
            background-color: #e8f4f8;
            padding: 12px;
            border-left: 4px solid #0066cc;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        #graphviz {{
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 20px;
            background-color: #fafafa;
            overflow: auto;
            min-height: 600px;
        }}
        svg {{
            max-width: 100%;
            height: auto;
        }}
        .loading {{
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 SantuarioVital - Diagrama de Classes UML</h1>
        <div class="info">
            <strong>📊 Diagrama de Classes do Domínio:</strong> Visualização das classes de modelo da aplicação Django
        </div>
        <div id="graphviz">
            <div class="loading">Carregando diagrama...</div>
        </div>
    </div>

    <script>
        async function renderDiagram() {{
            const graphviz = await Graphviz.load();
            const dotSource = `{dot_content}`;
            
            try {{
                const svg = graphviz.renderSVGElement(dotSource);
                const container = document.getElementById('graphviz');
                container.innerHTML = '';
                container.appendChild(svg);
            }} catch (error) {{
                document.getElementById('graphviz').innerHTML = 
                    '<div class="loading" style="color: red;">Erro ao renderizar diagrama: ' + error.message + '</div>';
            }}
        }}
        
        renderDiagram();
    </script>
</body>
</html>
"""

    with open(html_file, "w") as f:
        f.write(html_content)

    return html_file


def generate_uml_diagram():
    """Generates UML diagram of the core app models using pyreverse."""
    output_dir = Path("docs")
    output_dir.mkdir(exist_ok=True)

    print("🔄 Gerando diagrama UML das classes de domínio...")

    # Use pyreverse to generate UML diagram
    try:
        import subprocess

        # Generate dot file using pyreverse
        result = subprocess.run(
            [
                "pyreverse",
                "-o",
                "dot",
                "-p",
                "core",
                "medsystem/core/models.py",
            ],
            cwd="/workspaces/SantuarioVital",
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"⚠️  Aviso ao executar pyreverse: {result.stderr}")

        # Move files to docs directory
        classes_dot = Path("classes_core.dot")

        if classes_dot.exists():
            classes_dot.rename(output_dir / "classes.dot")
            print(f"✅ Diagrama de classes gerado: {output_dir / 'classes.dot'}")

            # Generate HTML visualization
            html_file = generate_html_visualization(output_dir / "classes.dot")
            print(f"✅ Visualização HTML gerada: {html_file}")
            return True
        else:
            print("⚠️  Nenhum diagrama gerado. Verifique se pyreverse está instalado corretamente.")
            return False

    except Exception as e:
        print(f"❌ Erro ao gerar diagrama: {e}")
        return False


if __name__ == "__main__":
    success = generate_uml_diagram()
    sys.exit(0 if success else 1)
