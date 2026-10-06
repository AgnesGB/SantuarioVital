import uuid

from django.conf import settings
from django.db import migrations, models


def gerar_tokens(apps, schema_editor):
    MapaTeorizacao = apps.get_model('core', 'MapaTeorizacao')
    for mapa in MapaTeorizacao.objects.all():
        mapa.token_link = uuid.uuid4()
        mapa.save(update_fields=['token_link'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_imagens'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='mapateorizacao',
            name='versao',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='mapateorizacao',
            name='colaboradores',
            field=models.ManyToManyField(blank=True, related_name='mapas_colaborando', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='mapateorizacao',
            name='link_ativo',
            field=models.BooleanField(default=False, verbose_name='Link de visualização ativo'),
        ),
        # Em três passos para que cada mapa já existente receba um token diferente
        migrations.AddField(
            model_name='mapateorizacao',
            name='token_link',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.RunPython(gerar_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='mapateorizacao',
            name='token_link',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]
