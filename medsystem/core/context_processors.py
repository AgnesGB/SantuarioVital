def medico_context(request):
    is_medico = request.user.is_authenticated and request.user.tipo == 'MED'
    is_admin = request.user.is_authenticated and request.user.tipo == 'ADM'
    return {
        'is_medico': is_medico,
        'is_admin': is_admin,
        'is_medico_or_admin': is_medico or is_admin
    }