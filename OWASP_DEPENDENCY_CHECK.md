# OWASP Dependency Check - Documentação

## O que é OWASP Dependency Check?

OWASP Dependency Check é uma ferramenta de software composition analysis (SCA) que:
- 🔍 Identifica vulnerabilidades conhecidas em dependências
- 📊 Gera relatórios detalhados em múltiplos formatos (HTML, JSON, SARIF)
- 🔐 Integra-se nativamente com GitHub Security
- 📈 Executa verificações automáticas em CI/CD

## Configuração

### Arquivo de Workflow
- Localização: `.github/workflows/owasp-dependency-check.yml`
- Acionadores:
  - ✅ Push em `requirements.txt`
  - ✅ Pull Requests
  - ✅ Agendamento semanal (segundas 08:00 UTC)
  - ✅ Manual via `workflow_dispatch`

### Como Funciona

1. **Checkout**: Clona o repositório
2. **Scan**: Analisa `requirements.txt` com OWASP Dependency Check
3. **Relatório SARIF**: Gera relatório em formato SARIF
4. **Upload GitHub Security**: Integra com GitHub Security tab
5. **Artefatos**: Salva relatório HTML por 30 dias

## Interpretando Resultados

### Na GitHub Security Tab
1. Acesse: **Settings → Code security and analysis → Dependency alerts**
2. Ou: **Security → Dependency scanning**

### Relatório HTML
- Baixe do Actions → Artefatos
- Abre no navegador com detalhes completos
- Mostra: CVE, CVSS score, recomendações

### Exemplo de Vulnerabilidade
```
Vulnerability: CVE-2024-XXXXX
Severity: HIGH (CVSS 7.5)
Library: Django 5.2.13
Recommendation: Upgrade to Django 6.0.5 or later
Impact: Potential SQL injection in ORM
```

## Comparação com GitHub Dependabot

| Critério | Dependabot | OWASP Check |
|----------|-----------|------------|
| Atualiza automático | ✅ Cria PRs | ❌ Apenas alerta |
| Vulnerabilidades | ⚠️ Parcial | ✅ Completo (NVD) |
| Atualizações gerais | ✅ Sim | ❌ Não |
| Formato de saída | PR automático | HTML, JSON, SARIF |
| Base de dados | Release notes | CVE (NVD) |

## Próximas Verificações

Task 1 (Dependabot): ✅ Concluído
- Configurado monitoramento automático
- Atualizadas dependências
- PR #16 aberto

Task 2 (OWASP Check): ⏳ Em andamento
- Workflow configurado
- Executará automaticamente em cada push de requirements.txt
- Alertas aparecerão em GitHub Security tab

## Recursos

- [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/)
- [GitHub Security Overview](https://docs.github.com/en/code-security)
- [CVE Database](https://nvd.nist.gov/)
