from django.contrib import admin
from .models import Doenca, Paciente, Sintoma

admin.site.register(Doenca)
admin.site.register(Paciente)
admin.site.register(Sintoma)
