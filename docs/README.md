# 📊 Diagrama de Classes UML - SantuarioVital

## Visão Geral

O diagrama de classes UML do projeto **SantuarioVital** é gerado automaticamente a partir das classes de modelo Django.

## Arquivos Gerados

- **`docs/classes.dot`** - Arquivo Graphviz em formato DOT com a definição do diagrama
- **`docs/classes.html`** - Visualização interativa do diagrama em HTML/JavaScript

## Como Gerar o Diagrama

### Localmente

Execute o script de geração:

```bash
python generate_uml_diagram.py
```

O script irá:
1. Analisar as classes em `medsystem/core/models.py`
2. Gerar o arquivo `classes.dot` usando `pyreverse`
3. Criar uma visualização HTML interativa em `classes.html`

### No Pipeline

O diagrama é gerado automaticamente quando há mudanças em:
- `medsystem/core/models.py` - Classes de modelo
- `requirements.txt` - Dependências
- `generate_uml_diagram.py` - Script de geração

O workflow é executado via GitHub Actions e os diagramas são salvos como artifacts.

## Visualizar o Diagrama

### Opção 1: Arquivo HTML (Recomendado)
Abra `docs/classes.html` em um navegador web para uma visualização interativa do diagrama.

### Opção 2: Arquivo DOT
Use ferramentas online como:
- [Graphviz Online](https://dreampuf.github.io/GraphvizOnline/)
- [Edotor](https://edotor.net/)

Cole o conteúdo de `docs/classes.dot` para visualizar.

## Classes do Domínio

O diagrama inclui as seguintes classes principais:

- **Usuario** - Usuários do sistema (Médicos, Administradores, etc)
- **Paciente** - Pacientes em tratamento
- **Doenca** - Doenças catalogadas
- **Diagnostico** - Diagnósticos realizados
- **Besta** - Bestas perigosas registradas
- **Ingrediente** - Ingredientes para remédios
- **Remedio** - Remédios e tratamentos
- **Raca** - Raças e características
- **Cidade** - Localidades
- **RegistroMedico** - Histórico médico
- **RelatorioExpedicao** - Relatórios de expedições
- **AnotacaoPessoal** - Anotações pessoais dos usuários

## Dependências

O gerador utiliza:
- `pylint` (3.0.0+) - Para análise com `pyreverse`
- `django-extensions` (3.2.0+) - Utilitários Django
- `pydot` (1.4.2+) - Para manipulação de diagramas

## Fluxo de Atualização

```
Mudança em models.py
        ↓
GitHub Actions dispara workflow
        ↓
Script gera classes.dot
        ↓
Script gera classes.html
        ↓
Artifacts salvos
```

## Referências

- [Django Models Documentation](https://docs.djangoproject.com/en/5.2/topics/db/models/)
- [Graphviz Documentation](https://graphviz.org/documentation/)
- [Pyreverse Documentation](https://pylint.pycqa.org/en/latest/pyreverse.html)
