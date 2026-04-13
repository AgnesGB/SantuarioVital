# SantuarioVital

## Versionamento e LTS

Análise de dois componentes usados no projeto, evitando os exemplos vistos em sala de aula.

| Componente | Usado no projeto | Versionamento semântico | LTS | Evidências |
| --- | --- | --- | --- | --- |
| Django | Sim | Sim, a documentação oficial trabalha com versões no formato `A.B.C` e política de releases bem definida | Sim, há releases LTS | [requirements.txt](requirements.txt#L1), [release process](https://docs.djangoproject.com/en/stable/internals/release-process/) |
| Pillow | Sim | Sim, as publicações seguem o padrão de versões numeradas `major.minor.patch` | Não encontrei um programa oficial de LTS na documentação pública consultada | [requirements.txt](requirements.txt#L2), [PyPI](https://pypi.org/project/Pillow/), [release notes](https://pillow.readthedocs.io/en/stable/releasenotes/index.html) |

Conclusão rápida: no projeto, Django oferece versionamento compatível com semver e possui LTS; Pillow também usa versões numeradas no estilo semver, mas não traz uma oferta oficial de LTS na documentação consultada.