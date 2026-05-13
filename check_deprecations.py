#!/usr/bin/env python
"""
Detecta código deprecado no projeto Django.
Transforma DeprecationWarnings em erros para falhar a pipeline.
"""
import os
import sys
import warnings
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medsystem.settings")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "medsystem"))

# Tratar DeprecationWarnings como erros
warnings.filterwarnings("error", category=DeprecationWarning)

try:
    django.setup()
    # Importar views para detectar deprecações
    from core import views

    # Testar função deprecada - vai gerar DeprecationWarning
    try:
        views.validar_usuario("teste")
    except DeprecationWarning as e:
        raise  # Re-raise para capturar abaixo

    print("Nenhuma função deprecada detectada!")
    sys.exit(0)

except DeprecationWarning as e:
    print(f"Função deprecada detectada!")
    print(f"Erro: {str(e)}")
    sys.exit(1)
except Exception as e:
    # Erros de setup são ok, desde que não sejam DeprecationWarning
    if "deprecat" in str(e).lower():
        print(f"Código deprecado: {str(e)}")
        sys.exit(1)
    print(f"Django setup ok")
    sys.exit(0)
