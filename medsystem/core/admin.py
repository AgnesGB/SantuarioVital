from django.contrib import admin
from .models import (
    Usuario,
    Doenca,
    Paciente,
    Cidade,
    Besta,
    RelatorioExpedicao,
    Diagnostico,
    RegistroMedico,
    Raca,
    Ingrediente,
    Remedio,
    RemedioIngrediente,
    AnotacaoPessoal
)

class RemedioIngredienteInline(admin.TabularInline):
    model = RemedioIngrediente
    extra = 1
    fields = ['ingrediente', 'quantidade']

class RemedioAdmin(admin.ModelAdmin):
    inlines = [RemedioIngredienteInline]
    list_display = ['nome', 'descricao']
    filter_horizontal = ['doencas']

admin.site.register(Usuario)
admin.site.register(Doenca)
admin.site.register(Paciente)
admin.site.register(Cidade)
admin.site.register(Besta)
admin.site.register(RelatorioExpedicao)
admin.site.register(Diagnostico)
admin.site.register(RegistroMedico)
admin.site.register(Raca)
admin.site.register(Ingrediente)
admin.site.register(Remedio, RemedioAdmin)
admin.site.register(AnotacaoPessoal)