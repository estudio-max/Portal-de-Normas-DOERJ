# docs/ — material de apoio

Duas tabelas de titulares moram aqui, e **a diferença entre elas é o ponto**.

| Arquivo | O que é | Confiança |
|---|---|---|
| `secretarios-cti-levantamento-web.csv` | levantamento feito na internet, trazido pelo João em 2026-09-22 | **hipótese** |
| `titulares-conferidos-no-diario.csv` | lido da capa do próprio Diário | **fonte primária** |

O primeiro não é ruim: foi ele que deu os períodos onde procurar, e economizou
uma busca cega em dezesseis anos de edições. Mas ele tem sobreposição — Gustavo
Tutuca aparece em 2013-2014, 2015 e 2017, e Pedro Fernandes em 2017-2018 — e
usa apelido no lugar de nome ("Dr. Serginho"). Um portal lido por órgão de
controle não publica linha do tempo com contradição dentro.

O segundo é gerado por `tools/doerj_titulares.py`, que lê a lista de titulares
impressa na capa de cada edição. Ele diz apenas "nesta data, esta pasta tinha
este titular". Não deduz período, e é de propósito: onde acaba um mandato e
começa o outro é coisa que se descobre baixando mais edições, não supondo.

## O que a conferência mostrou

Cinco datas conferidas, cinco batem com o levantamento. E o Diário completa o
que a internet abreviava:

| Levantamento | Diário |
|---|---|
| Gustavo Tutuca | Gustavo Reis Ferreira |
| Dr. Serginho | Sérgio Luiz Costa Azevedo Filho |
| Gabriell Neves | Gabriell Carvalho Neves Franco dos Santos |

E o nome da pasta muda com o tempo, que era a pergunta original:

- 2010 e 2013 — Secretaria de Estado de **Ciência e Tecnologia**
- 2018 — Secretaria de Estado de **Ciência, Tecnologia, Inovação e Desenvolvimento Social**
- 2021 em diante — Secretaria de Estado de **Ciência, Tecnologia e Inovação**

## Como ampliar

```
python tools/doerj_download.py --inicio 2016-06-15
python tools/doerj_titulares.py dados/2016/06/*.pdf --pasta CI
```

Para achar a data exata de uma troca, busca binária: quando duas datas mostram
titulares diferentes, baixe o meio. Cada troca custa cerca de cinco downloads.
