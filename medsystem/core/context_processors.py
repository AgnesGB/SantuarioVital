def medico_context(request):
    return {
        'is_medico': request.user.is_authenticated and request.user.tipo == 'MED'
    }