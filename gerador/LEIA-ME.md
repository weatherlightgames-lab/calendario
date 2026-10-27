# Gerador do Calendário Weatherlight

1. `semana.json` — a semana: texto (introdução, destaques), dias e eventos (hora, jogo, preço, esgotado, modelo, arte, story, recorte) e, opcionais, `inscricao` (link do torneio na Melee, Bandai TCG+, Riftbound, Neuron…; mostra o botão "Inscreve-te") e `companion` (código do Magic Companion; mostra o botão "Código Companion"). Eventos esgotados não mostram estes botões. Links e códigos que chegam antes da semana ser publicada vão para `pendentes.json` (por data e nome do evento) e entram sozinhos quando essa semana for gerada.
2. `details.json` — textos de detalhes, com o mesmo título dos modelos (###) da Base de Dados Eventos Weatherlight.
3. `python3 recortar.py <pasta-das-stories>` — miniaturas em ../img/.
4. `python3 build.py` — gera ../index.html.
5. Commit e push para `main`: o GitHub Pages publica em https://eventos.weatherlightgames.pt.

Regras: fuso +01:00 até ao último sábado de outubro, +00:00 a partir do último domingo de outubro (e o inverso no fim de março).
One Piece: Pirate Lounge e Pirate Party são Standard; Extra Regulation só quando o calendário avisa.

- **Adicionar ao calendário:** o `build.py` gera um link Google Calendar e um ficheiro `.ics` (Apple/Outlook) por evento em `ics/` (a pasta é refeita em cada build; duração prevista 3 h). Aparece dentro de "Ver detalhes".
- **"Como me posso inscrever?"** nas páginas fixas: textos por jogo em `APPS` (`series.py`), confirmados pela equipa (contas obrigatórias; pagamento no check-in ao balcão; gratuito quando o preço é 0).
- **Formatos de Magic:** explicação curta + link para as regras no site da Wizards (`FMT_MTG` em `series.py`), na pergunta "Que formato se joga?" e nos cartões de "Outros eventos de Magic".
- **Eventos que não podes perder:** `futuros.json` (lista de eventos com `iso`, `hora`, `jogo`, `nome_jogo`, `evento`, `preco`, `modelo`, `arte`, `story`, `recorte` e, opcionais, `inscricao`/`companion`). Aparecem numa secção própria enquanto a data é posterior à semana publicada; o fuso é calculado sozinho (Europe/Lisbon). `recortar.py` também recorta as stories destes eventos. Quando a semana do evento é publicada, entra em `semana.json` como os outros (e pode sair de `futuros.json`).
- **Páginas de cada jogo** (`/magic/`, `/pokemon/`, …): geradas por `gerar_jogos` em `series.py` com os eventos regulares, os desta semana, os especiais (`futuros.json`), os outros modelos da base de dados e o link para a marca na loja. São o destino dos links nas páginas de marca da Shopkit.
- **extras.py** (corre no fim do build): páginas dos eventos especiais em `/<jogo>/<evento>/` (uma por entrada de `futuros.json`; não apagar entradas antigas, a página passa a dizer "Este evento já aconteceu"), página `/primeira-vez/`, calendários para subscrever (`/calendario.ics` e `/<jogo>/calendario.ics`), dados da loja (JSON-LD GameStore; horário em `loja.json` quando existir), `/llms.txt`, imagens de partilha em `/og/` (fonte Jost em `gerador/fonts/`, OFL) com as meta tags Open Graph, e o `sitemap.xml` completo.
- Gundam Assemble tem chave própria `assemble` (cor, filtro e página `/gundam-assemble/`).
- **Imagem de partilha do calendário** (`og/calendario.jpg`): mostra primeiro as artes dos eventos especiais da semana (os que não são regulares); o link leva `?v=` com o conteúdo da imagem, para o WhatsApp/Discord mostrarem sempre a nova.
- **Arquivo** (`/arquivo/`): eventos especiais passados, por semana, a partir de `gerador/historico/` (cópia automática da semana em cada build, com o texto congelado) e de `futuros.json` (onde ficam também os eventos anteriores ao calendário, desde o aniversário a 25/09; campo `texto` para o texto da altura, `tipo` para ligar ao próximo do mesmo tipo). Fotos da semana: `gerador/recaps.json` (`{"AAAA-MM-DD da segunda-feira ou do 1.º dia da semana": link do Instagram}`). As páginas de jogo ganham "Já fizemos".
- **Cartões com imagem** (arquivo e páginas de jogo): todos com a mesma altura (140 px); títulos até 2 linhas, datas e jogo numa linha (abreviados). Manter assim em cartões novos.
