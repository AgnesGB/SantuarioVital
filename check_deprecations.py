#!/usr/bin/env python
"""
Script para detectar código deprecado no projeto.
Verifica:
1. Uso de decoradores @deprecated
2. Funções/métodos do Django que foram descontinuados
3. Verificações customizadas
"""

import os
import re
import sys
from pathlib import Path


def find_deprecated_decorator_usage(directory):
    """
    Encontra uso de decorador @deprecated ou @deprecation.deprecated
    """
    issues = []
    deprecated_pattern = re.compile(r'@(?:deprecation\.)?deprecated')
    
    for root, dirs, files in os.walk(directory):
        # Ignorar diretórios não relevantes
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.env', 
                                                   'node_modules', '.venv', 'venv',
                                                   'migrations', '.github'}]
        
        for file in files:
            if not file.endswith('.py'):
                continue
                
            filepath = os.path.join(root, file)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for line_num, line in enumerate(lines, 1):
                    if deprecated_pattern.search(line):
                        # Pega o contexto (próxima linha tem a função/classe)
                        context = lines[line_num].strip() if line_num < len(lines) else ""
                        issues.append({
                            'file': filepath,
                            'line': line_num,
                            'type': 'deprecated_decorator',
                            'message': f'Código marcado como deprecated: {context}',
                            'code': line.strip()
                        })
            except Exception as e:
                print(f"Erro ao processar {filepath}: {e}", file=sys.stderr)
    
    return issues


def find_django_deprecated_apis(directory):
    """
    Encontra uso de APIs deprecadas do Django
    """
    issues = []
    
    # Padrões de APIs deprecadas do Django
    deprecated_patterns = {
        r'from django\.utils import force_text': 'force_text foi removido, use force_str',
        r'\.force_text\(': 'force_text foi removido, use force_str',
        r'from django\.conf\.urls import url': 'url() foi removido em Django 4.0, use path() ou re_path()',
        r'from django\.utils import unescape_entities': 'unescape_entities foi removido',
        r'smart_text': 'smart_text foi removido, use smart_str',
        r'django\.utils\.encoding\.smart_text': 'smart_text foi removido, use smart_str',
        r'JsonResponse.*safe=False': 'safe=False é o padrão em Django 3.1+, pode ser removido',
    }
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.env', 
                                                   'node_modules', '.venv', 'venv',
                                                   'migrations', '.github'}]
        
        for file in files:
            if not file.endswith('.py'):
                continue
                
            filepath = os.path.join(root, file)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                for pattern, message in deprecated_patterns.items():
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            issues.append({
                                'file': filepath,
                                'line': line_num,
                                'type': 'django_deprecated_api',
                                'message': f'API deprecada: {message}',
                                'code': line.strip()
                            })
            except Exception as e:
                print(f"Erro ao processar {filepath}: {e}", file=sys.stderr)
    
    return issues


def print_issues(issues):
    """
    Formata e imprime os problemas encontrados
    """
    if not issues:
        print("✓ Nenhum código deprecado encontrado!")
        return 0
    
    print(f"✗ {len(issues)} problema(s) de código deprecado encontrado(s):\n")
    
    for issue in issues:
        print(f"📍 {issue['file']}:{issue['line']}")
        print(f"   Tipo: {issue['type']}")
        print(f"   Mensagem: {issue['message']}")
        print(f"   Código: {issue['code']}")
        print()
    
    return len(issues)


def main():
    """
    Executa todas as verificações de código deprecado
    """
    print("🔍 Analisando código deprecado no projeto...\n")
    
    directories = ['medsystem']
    all_issues = []
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"Verificando {directory}...")
            all_issues.extend(find_deprecated_decorator_usage(directory))
            all_issues.extend(find_django_deprecated_apis(directory))
    
    print()
    exit_code = print_issues(all_issues)
    
    if exit_code > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
