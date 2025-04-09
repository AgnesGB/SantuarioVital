from django.contrib import admin
from .models import (
    Usuario,
    Doenca,
    Paciente,
    Bunker,
    Besta,
    Postagem,
    Comentario,
    RelatorioExpedicao,
    Diagnostico,
    RegistroMedico
)

admin.site.register(Usuario)
admin.site.register(Doenca)
admin.site.register(Paciente)
admin.site.register(Bunker)
admin.site.register(Besta)
admin.site.register(Postagem)
admin.site.register(Comentario)
admin.site.register(RelatorioExpedicao)
admin.site.register(Diagnostico)
admin.site.register(RegistroMedico)