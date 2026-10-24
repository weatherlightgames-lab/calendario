# Gerador do Calendário Weatherlight

1. `semana.json` — a semana: texto (introdução, destaques), dias e eventos (hora, jogo, preço, esgotado, modelo, arte, story, recorte) e, opcionais, `inscricao` (link do torneio na Melee, Bandai TCG+, Riftbound, Neuron…; mostra o botão "Inscreve-te") e `companion` (código do Magic Companion; mostra o botão "Código Companion"). Eventos esgotados não mostram estes botões. Links e códigos que chegam antes da semana ser publicada vão para `pendentes.json` (por data e nome do evento) e entram sozinhos quando essa semana for gerada.
2. `details.json` — textos de detalhes, com o mesmo título dos modelos (###) da Base de Dados Eventos Weatherlight.
3. `python3 recortar.py <pasta-das-stories>` — miniaturas em ../img/.
4. `python3 build.py` — gera ../index.html.
5. Commit e push para `main`: o GitHub Pages publica em https://eventos.weatherlightgames.pt.

Regras: fuso +01:00 até ao último sábado de outubro, +00:00 a partir do último domingo de outubro (e o inverso no fim de março).
One Piece: Pirate Lounge e Pirate Party são Standard; Extra Regulation só quando o calendário avisa.
