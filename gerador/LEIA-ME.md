# Calendário Weatherlight — back-up (23/10/2026, 23:05)

Ficheiros:
- eventos-weatherlight.html — a página gerada (semana de 21 a 25 de outubro).
- nuvens.jpg — imagem do cabeçalho (tem de ficar na mesma pasta da página).
- tpl.html — modelo da página (visual, cores, fonte Futura/Jost, filtro por jogo).
- details.json — textos de detalhes de cada evento, copiados da Base de Dados Eventos Weatherlight.
- img/ — miniaturas ao alto (<evento>-v.jpg, recortadas das stories) e imagens largas para o Google (<evento>.jpg).
- crop_story.py / crop.py — scripts de recorte das stories e dos cartazes.
- build.py — script que junta o calendário da semana (lista `days`), os detalhes e o modelo, e gera a página com os dados estruturados de evento (schema.org Event) para o Google.

Para gerar a página: `python3 build.py` (Python 3, sem bibliotecas extra).

Notas:
- A página publicada como artifact recebe o <html>/<head> automaticamente. Para alojar no vosso subdomínio, basta envolver o conteúdo em <!doctype html><html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"> … </head><body> … </body></html> (o Claude faz isto na primeira publicação).
- Fusos: horário de verão (+01:00) até 24/10; a partir de 25/10, +00:00.
- Regra One Piece: Pirate Lounge e Pirate Party são Standard; Extra Regulation só quando o calendário avisa.

- Fluxo semanal: stories (eventos + miniaturas) + texto da semana (introdução, destaques). Sábado/domingo após a mudança de hora usam +00:00.
- Links fixos: Discord https://discord.gg/HTCZeJZuVk · Google Maps https://maps.app.goo.gl/GnKdFUwrm1J6o46P9 · Central de Ajuda e Glossário.
