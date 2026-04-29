#!/usr/bin/env python
"""
Verifica avisos de deprecação no projeto Django.
Uso: python check_warnings.py
"""
import os
import sys
import django
import warnings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medsystem.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'medsystem'))

django.setup()

def check_deprecations():
    """Detecta warnings e deprecações na aplicação Django."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Importa views para detectar deprecações
        from core import views
        
        # Conta avisos
        deprecations = [warning for warning in w if issubclass(warning.category, (DeprecationWarning, PendingDeprecationWarning))]
        
        if deprecations:
            print(f"❌ {len(deprecations)} avisos de deprecação encontrados:")
            for warning in deprecations:
                print(f"  - {warning.category.__name__}: {warning.message}")
            return 1
        else:
            print("✓ Nenhum aviso de deprecação detectado!")
            return 0

if __name__ == '__main__':
    sys.exit(check_deprecations())
