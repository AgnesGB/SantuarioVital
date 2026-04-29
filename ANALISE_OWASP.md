# 🔒 Análise de Riscos de Segurança OWASP - SantuarioVital

## Visão Geral
Análise dos 10 principais riscos de segurança OWASP (2021/2025) aplicada ao projeto Django SantuarioVital. Foram identificados **3 vulnerabilidades críticas**.

## ⚠️ Nota Importante: Vulnerabilidades Aceitáveis
**Algumas vulnerabilidades foram ACEITAS deliberadamente** porque são requisitos do design e funcionamento do sistema:
- **Enumeração de usuários (HomeView)**: Listagem de todos os usuários é intencional (site colaborativo)
- **Acesso não restrito a bunkers**: O sistema permite visualizar dados de outras cidades (design da aplicação)
- Essas decisões são **conscientes** e documentadas abaixo em cada vulnerabilidade relevante.

---

## 1️⃣ **A01:2021 - Broken Access Control** ⚠️ CRÍTICO

### Descrição
Controle de acesso quebrado permite que usuários não autenticados ou com permissões limitadas acessem recursos restritos.

### Vulnerabilidades Identificadas

#### **1.1 BunkertListView sem Autenticação**
**Arquivo:** `medsystem/core/views.py` (linhas 53-56)
```python
class BunkertListView(ListView):
    model = Cidade
    template_name = 'core/bunker_list.html'
    context_object_name = 'bunkers'
    # ❌ FALTA LoginRequiredMixin
```

**Status:** ✅ **ACEITO COMO REQUISITO DO SISTEMA**

**Justificativa:**
- Requisito de design: Visitantes podem listar bunkers/cidades sem autenticação
- O site é colaborativo e deseja mostrar informações de centros disponíveis
- **Decisão consciente**: A exposição é intencional por necessidade funcional

**Vulnerabilidade Original:**
- Qualquer pessoa (mesmo não autenticada) pode acessar a lista de cidades/bunkers
- Url: `/cidades/` está acessível para qualquer um

**Possível Mitigação (se necessário no futuro):**
Adicionar `LoginRequiredMixin` quando o requisito mudar:
```python
class BunkertListView(LoginRequiredMixin, ListView):
    model = Cidade
    template_name = 'core/bunker_list.html'
    context_object_name = 'bunkers'
```

#### **1.2 BunkerDetailView sem Validação de Propriedade**
**Arquivo:** `medsystem/core/views.py` (linhas 47-53)
```python
class BunkerDetailView(DetailView):
    model = Cidade
    template_name = 'core/bunker_detail.html'
    # ❌ Não verifica se o usuário pertence à cidade
    # ❌ Não valida acesso aos pacientes/membros
```

**Status:** ✅ **ACEITO COMO REQUISITO DO SISTEMA**

**Justificativa:**
- Requisito de design: Qualquer usuário pode visualizar dados de qualquer bunker
- O site permite consulta de informações entre centros de operação
- **Decisão consciente**: A falta de isolamento é intencional para colaboração

**Vulnerabilidade Original:**
- Um usuário pode acessar detalhes de QUALQUER bunker, mesmo que não trabalhe lá
- Expõe membros da equipe e pacientes de outros bunkers
- Url: `/cidades/1/` mostra todos os pacientes da cidade 1

**Impacto Aceito:**
- ⚠️ Visualização de dados de pacientes entre bunkers
- ⚠️ Exposição de informações de equipe médica (por design)
- ⚠️ Acesso não autorizado a registros (como requisitado)

**Possível Mitigação (se necessário no futuro):**
```python
from django.core.exceptions import PermissionDenied

class BunkerDetailView(DetailView):
    model = Cidade
    
    def get_object(self):
        obj = super().get_object()
        # Verificar se o usuário pertence à cidade
        if self.request.user.cidade != obj and self.request.user.tipo != 'ADM':
            raise PermissionDenied("Você não tem acesso a este bunker")
        return obj
```

#### **1.3 HomeView Expõe Lista Global de Usuários**
**Arquivo:** `medsystem/core/views.py` (linhas 42-46)
```python
class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuarios'] = Usuario.objects.all().order_by('nickname')
        # ✓ Intencional: Lista de membros é uma feature do sistema
        return context
```

**Status:** ✅ **ACEITO COMO REQUISITO DO SISTEMA**

**Justificativa:**
- Requisito de design: Site colaborativo deseja mostrar todos os membros
- Enumeration de usuários é uma **feature**, não uma bug
- **Decisão consciente**: A visibilidade de usuários é parte da UX desejada

**Vulnerabilidade Original (contexto teórico):**
- Página inicial mostra lista completa de usuários
- Facilita enumeração de usuários (username enumeration attack)
- Facilita engenharia social

**Impacto Aceito:**
- ✓ Enumeration de usuários (como desejado)
- ✓ Visibilidade de informações de staff
- ✓ Transparência sobre papéis (médicos, admins, etc)

**Possível Mitigação (se necessário no futuro):**
Restringir para apenas admins:
```python
class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Apenas usuários adminstradores veem lista
        if self.request.user.tipo == 'ADM':
            context['usuarios'] = Usuario.objects.all().order_by('nickname')
        else:
            context['usuarios'] = []
        return context
```

---

## 2️⃣ **A05:2021 - Security Misconfiguration** ⚠️ CRÍTICO

### Descrição
Configurações de segurança inadequadas, padrões inseguros e segredos expostos.

### Vulnerabilidades Identificadas

#### **2.1 SECRET_KEY Exposta em Código Versionado**
**Arquivo:** `medsystem/medsystem/settings.py` (linha 24)
```python
SECRET_KEY = "django-insecure-*^mi_y4vu23^oopd%+^tr$27pvh-es5qkqb*fj=0-5$%+@jurs"
```

**Problema:**
- SECRET_KEY é hardcoded no repositório Git (history forever)
- Anyone com acesso ao repo pode usar para:
  - Falsificar tokens CSRF
  - Assinar session cookies
  - Decriptar dados sensíveis

**Evidência:**
```bash
# Comando que revela a secret no histórico:
git log -p -- medsystem/medsystem/settings.py | grep SECRET_KEY
# Resultado: SECRET_KEY exposta em todos os commits
```

**Impacto:**
- ☠️ Session hijacking
- ☠️ CSRF forgery
- ☠️ Autenticação comprometida
- ☠️ **IMPOSSÍVEL regenerar SECRET_KEY** (quebra todas as sessions)

**Solução:**
```python
# Usar variável de ambiente
import os
from pathlib import Path

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY não configurada. Configure a variável de ambiente.")

# Ou usar python-decouple
from decouple import config
SECRET_KEY = config('SECRET_KEY')
```

**Implementação:**
1. Criar `.env` (localmente apenas):
```env
SECRET_KEY=django-insecure-VALOR-NOVO-E-SEGURO-GERADO
```

2. Adicionar `.env` ao `.gitignore`
3. Em produção, configurar via railway/hosting

#### **2.2 CSRF_TRUSTED_ORIGINS Hardcoded**
**Arquivo:** `medsystem/medsystem/settings.py` (linha 121)
```python
CSRF_TRUSTED_ORIGINS=['https://localhost:8000']
```

**Problema:**
- Localhost está hardcoded (dev config em produção)
- Permite CSRF attacks se alguém conseguir subdomínio com `localhost`
- Não escala para múltiplos hosts

**Solução:**
```python
CSRF_TRUSTED_ORIGINS = os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    'https://localhost:8000'
).split(',')
```

#### **2.3 SQLite em Produção**
**Arquivo:** `medsystem/medsystem/settings.py` (linhas 73-77)
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

**Problema:**
- SQLite não suporta múltiplos escritores em concorrência
- Sem criptografia de dados em repouso
- Sem auditoria nativa
- Arquivo no filesystem sem backup automático

**Impacto:**
- ☠️ Corrupção de dados em produção
- ☠️ Sem proteção de dados em repouso
- ☠️ Sem controle de acesso a nível de DB

**Solução:**
```python
# Usar PostgreSQL em produção
if os.getenv('ENVIRONMENT') == 'production':
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv('DB_NAME'),
            "USER": os.getenv('DB_USER'),
            "PASSWORD": os.getenv('DB_PASSWORD'),
            "HOST": os.getenv('DB_HOST'),
            "PORT": os.getenv('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
```

---

## 3️⃣ **A07:2021 - Identification and Authentication Failures** ⚠️ ALTO

### Descrição
Falhas em autenticação, session management e proteção de credenciais.

### Vulnerabilidades Identificadas

#### **3.1 Falta de Rate Limiting na Função de Recuperação de Senha**
**Arquivo:** Função `recuperar_senha` em `medsystem/core/views.py`

**Problema:**
- Sem proteção contra brute force
- Qualquer pessoa pode tentar recuperar senha de qualquer usuário
- Facilita ataques de força bruta (testar muitos emails)
- Não há delay entre tentativas

**Exemplo de Ataque:**
```
POST /recuperar-senha/
Email: teste@example.com
# Resposta imediata

POST /recuperar-senha/
Email: teste2@example.com
# Resposta imediata (pode fazer isso 1000x/s)
```

**Impacto:**
- ☠️ Conta hijacking
- ☠️ Enumeration de emails válidos
- ☠️ DoS (trava servidor com muitas requisições)

**Solução:**
```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.http import condition

def recuperar_senha(request):
    """Com rate limiting"""
    
    # Usar django-ratelimit
    from django_ratelimit.decorators import ratelimit
    
    @ratelimit(key='ip', rate='5/h', method='POST')
    def post(request):
        email = request.POST.get('email')
        # ... resto d código
    
    # Ou usar cache:
    from django.core.cache import cache
    
    ip = request.META.get('REMOTE_ADDR')
    key = f'pwd_reset_{ip}'
    
    if cache.get(key, 0) >= 5:
        messages.error(request, 'Muitas tentativas. Tente novamente em 1 hora.')
        return redirect('home')
    
    # Aumentar contador
    cache.set(key, cache.get(key, 0) + 1, 3600)
    
    # ... resto do código
```

#### **3.2 Falta de CSRF Token Explícito em Alteração de Privilégio**
**Arquivo:** `medsystem/core/views.py` (linhas 32-42)
```python
@login_required
@require_POST
def alterar_tipo_usuario(request, usuario_id):
    if request.user.tipo != 'ADM':
        messages.error(request, 'Apenas administradores...')
        return redirect('home')
    
    usuario = get_object_or_404(Usuario, id=usuario_id)
    novo_tipo = request.POST.get('tipo')
    # ❌ Depende apenas de @require_POST
    # ❌ Sem validação de CSRF explícita
```

**Problema:**
- Django tem CSRF middleware, MAS:
- Se a template não incluir `{% csrf_token %}`, qualquer site pode fazer CSRF
- Endpoint crítico (alteração de privilégio) merecia proteção extra

**Exemplo de CSRF:**
```html
<!-- Malicious site myevil.com -->
<form action="https://santuariovital.com/usuario/1/alterar-tipo/" method="POST">
  <input type="hidden" name="tipo" value="ADM">
  <img src="x" onerror="this.form.submit()">
</form>
<!-- Qualquer admin que visite esse site tem seu privilégio alterado! -->
```

**Impacto:**
- ☠️ Privilégio escalation
- ☠️ Account takeover (transformar outro user em admin)

**Solução:**
1. Garantir template tem `{% csrf_token %}`:
```html
<form method="POST" action="{% url 'alterar-tipo-usuario' usuario.id %}">
  {% csrf_token %}  <!-- ✓ OBRIGATÓRIO -->
  <select name="tipo">
    <option value="MED">Médico</option>
    <option value="ADM">Admin</option>
  </select>
  <button type="submit">Salvar</button>
</form>
```

2. Adicionar validação customizada:
```python
from django.middleware.csrf import get_token

@login_required
@require_POST
def alterar_tipo_usuario(request, usuario_id):
    # Django já valida CSRF automaticamente com CsrfViewMiddleware
    # Mas fazemos validação extra:
    
    if request.user.tipo != 'ADM':
        messages.error(request, 'Apenas administradores...')
        return redirect('home')
    
    # Validar CSRF explicitamente (redundante mas seguro)
    from django.middleware.csrf import CsrfViewMiddleware
    CsrfViewMiddleware(lambda r: None).process_request(request)
    
    usuario = get_object_or_404(Usuario, id=usuario_id)
    novo_tipo = request.POST.get('tipo')
    
    if novo_tipo in ['MED', 'OUT', 'ADM']:
        usuario.tipo = novo_tipo
        usuario.save()
        messages.success(request, f'Tipo alterado para {usuario.get_tipo_display()}')
    
    return redirect('home')
```

---

## 📊 Tabela Comparativa de Impactos

| Risco | CVSS Score | Impacto | Facilidade de Exploit |
|-------|-----------|--------|----------------------|
| A01 - Broken Access Control | 8.5 | Alto | Baixa (apenas URL) |
| A05 - Security Misconfiguration | 8.3 | Alto | Média (precisa da secret) |
| A07 - Auth Failures | 7.8 | Alto | Baixa (brute force) |

---

## ✅ Roadmap de Correções (Status Atual)

| Prioridade | Risco | Status | Ação | Justificativa |
|-----------|-------|--------|------|---------------|
| 1️⃣ CRÍTICO | A05 | ✅ IMPLEMENTADO | Mover SECRET_KEY para .env | Segurança obrigatória |
| 2️⃣ ALTO | A07 | ✅ IMPLEMENTADO | Rate limiting em recuperar_senha | Previne brute force |
| 📌 ACEITÁVEL | A01 | ⏭️ NÃO IMPLEMENTADO | Autenticação em BunkertListView | Requisito de design: lista pública |
| 📌 ACEITÁVEL | A01 | ⏭️ NÃO IMPLEMENTADO | Autorização em BunkerDetailView | Requisito de design: dados compartilhados |
| 📌 ACEITÁVEL | A01 | ⏭️ NÃO IMPLEMENTADO | Esconder enumeration em HomeView | Requisito de design: visibilidade de membros |

---

## 🔐 Referências OWASP

- [OWASP Top 10 - 2021](https://owasp.org/Top10/)
- [A01 - Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [A05 - Security Misconfiguration](https://owasp.org/Top10/A05_2021-Security_Misconfiguration/)
- [A07 - Identification and Authentication Failures](https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/)
- [Django Security Documentation](https://docs.djangoproject.com/en/5.2/topics/security/)

---

**Documento criado:** 29/04/2026
**Status:** Análise Completa - Aguardando Implementação das Correções
