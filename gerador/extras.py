"""Extras gerados depois do calendário e das páginas fixas (chamado no fim de build.py):
- páginas dos eventos especiais (futuros.json) em /<jogo>/<evento>/
- página /primeira-vez/
- calendários para subscrever: /calendario.ics e /<jogo>/calendario.ics
- dados da loja (JSON-LD GameStore) na página principal e /llms.txt para as IAs
- imagens de partilha (Open Graph) em /og/ e as respetivas meta tags em todas as páginas
- sitemap.xml com todas as páginas
"""
import json, os, re, html, datetime as dt
from PIL import Image, ImageDraw, ImageFont
import series
from series import (BASE, MAPS, CA, GL, DISCORD, PL, DIA_NOME, MESES, PASTA, MARCAS, CENTRAL, APPS, PAGA, GRATIS,
                    preco_txt, formato, fmt_mtg, esp_slug)

AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(AQUI)
FONTE = os.path.join(AQUI, 'fonts', 'Jost.ttf')
HORARIO = [("Segunda e Terça","Encerrados"),("Quarta e Sexta","15:00 – 23:00"),("Quinta, Sábado e Domingo","15:00 – 20:30")]
LOJA = {"@context": "https://schema.org", "@type": "GameStore", "name": "Weatherlight Games & Collectibles",
        "alternateName": "Weatherlight", "url": "https://www.weatherlightgames.pt/",
        "logo": "https://cdn-shopkit.com/usercontent/weatherlightgames/media/images/6caa56f-180700-logo-weatherlight_site_actualizado_nome_4.jpg",
        "image": BASE + "/og/calendario.jpg", "telephone": "+351266735119", "email": "weatherlightgames@gmail.com",
        "address": {"@type": "PostalAddress", "streetAddress": "Rua Frei José Maria Évora, Nº2", "postalCode": "7005-495",
                    "addressLocality": "Évora", "addressRegion": "Évora", "addressCountry": "PT"},
        "hasMap": MAPS, "currenciesAccepted": "EUR",
        "sameAs": ["https://www.instagram.com/weatherlightgames/", "https://www.facebook.com/weatherlightgames",
                   "https://www.tiktok.com/@weatherlightcollectibles", "https://www.youtube.com/@weatherlightgames", DISCORD]}
LOJA_P = os.path.join(AQUI, 'loja.json')   # horário (openingHoursSpecification) e outros dados, quando existirem
if os.path.exists(LOJA_P): LOJA.update(json.load(open(LOJA_P)))

# O que é preciso para participar, por jogo (resumo de APPS, confirmado pela equipa)
PRECISA = {"magic": "App Magic: The Gathering Companion e conta Wizards (entras com o código do evento)",
           "poke": "Player ID da Pokémon (se não tens, fazemos contigo na loja); recomendamos a app Pokémon Access",
           "op": "App e conta Bandai TCG+", "digi": "App e conta Bandai TCG+", "gundam": "App e conta Bandai TCG+",
           "ygo": "App Neuron e KONAMI ID (se não tens, criamos contigo na loja)",
           "rift": "Conta na Riftbound Gaming Network", "cyber": "Conta na Melee"}


def fz(iso, hora):
    from zoneinfo import ZoneInfo
    y, m, d = map(int, iso.split('-')); h, mi = map(int, hora.split(':'))
    z = dt.datetime(y, m, d, h, mi, tzinfo=ZoneInfo('Europe/Lisbon')).strftime('%z'); return z[:3] + ':' + z[3:]


def data_longa(iso):
    x = dt.date.fromisoformat(iso); return f"{DIA_NOME[x.weekday()]}, {x.day} de {MESES[x.month-1]}"


def cabeca(titulo, desc, url, lds, extra_css=''):
    sh = series.SHELL
    return f"""<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(titulo)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
{sh['fonts']}
{''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in lds)}
{sh['style']}
{sh['css2']}
<style>{extra_css}</style>
</head>"""


ALVO = lambda p: re.sub(r'<a (class="[^"]*" )?href="(https?://[^"]+)"(?![^>]*target=)', r'<a \1href="\2" target="_blank" rel="noopener"', p)
RODAPE = f'<footer><div class="wrap"><p class="close">Tens dúvidas? Vê a <a href="/primeira-vez/">página para quem vem pela primeira vez</a>, a <a href="{CA}">Central de Ajuda</a> ou junta-te à nossa comunidade no <a href="{DISCORD}">Discord</a>!</p></div></footer>'


# ---------------- páginas dos eventos especiais ----------------
def especiais(DET, FUT, inscricao):
    hoje = dt.date.today().isoformat(); urls = []
    css = (".acoes{display:flex;flex-wrap:wrap;align-items:center;gap:.6rem 1.2rem;margin:0}"
           ".passou{background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--brass);border-radius:6px;padding:.8rem 1rem;margin:0}"
           ".cal{font-size:.95rem;color:var(--muted)}.cal a{color:var(--sea-2)}.code{font:500 1.2rem var(--body);letter-spacing:.08em}")
    for f in FUT:
        g = f['jogo']; pasta = PASTA.get(g, g); slug = f.get('_slug') or (esp_slug(f) + '-' + f['iso'] if f.get('_slug_sufixo') else esp_slug(f)); url = f"{BASE}/{pasta}/{slug}/"
        txt = f.get('texto') or DET.get(f.get('modelo')) or DET.get(f['evento']); fmt = formato(txt); pr = preco_txt(float(f['preco']))
        quando = f"{data_longa(f['iso'])} · {f['hora']}"; passou = f['iso'] < hoje
        b2, _ = inscricao(f)
        cal = f.get('_cal', '') if not passou else ''
        fx = fmt_mtg(fmt) if g == 'magic' and fmt else None
        insc = APPS.get(g, '') + (GRATIS if float(f['preco']) == 0 else PAGA) if g in APPS else (GRATIS.strip() if float(f['preco']) == 0 else PAGA.strip())
        if f.get('inscricao'): insc += f' Inscreve-te já <a href="{html.escape(f["inscricao"])}">aqui</a>.'
        perg = [("Quando e onde é?", f"{quando}, aqui na <a href=\"{MAPS}\">Weatherlight</a>, em Évora (Rua Frei José Maria Évora, Nº2)."),
                ("Como me posso inscrever?", insc)]
        if fmt: perg.insert(1, ("Que formato se joga?", html.escape(fmt) + '. ' + (fx[1] + ' ' if fx else '') + f'Se algum termo for novo para ti, o <a href="{GL}">Glossário</a> explica tudo.'))
        perg.append(("É a minha primeira vez. Posso vir?", f'Claro! Vê a nossa <a href="/primeira-vez/">página para quem vem pela primeira vez</a>: explica como funciona o check-in, o que levar e que aplicações precisas.'))
        sem_tags = lambda x: re.sub(r'<[^>]+>', '', x)
        ev_ld = {"@context": "https://schema.org", "@type": "Event", "name": f"{f['evento']} - {f['nome_jogo']}",
                 "startDate": f"{f['iso']}T{f['hora']}:00{fz(f['iso'], f['hora'])}", "eventStatus": "https://schema.org/EventScheduled",
                 "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode", "url": url,
                 "location": {"@type": "Place", "name": "Weatherlight Games & Collectibles", "address": LOJA["address"]},
                 "organizer": {"@type": "Organization", "name": "Weatherlight Games & Collectibles", "url": "https://www.weatherlightgames.pt"},
                 **({"image": f"{BASE}/img/{f['arte']}-g.jpg"} if f.get('arte') else {}),
                 "description": re.sub(r"\s+", " ", txt).strip() if txt else f"{f['evento']} de {f['nome_jogo']} na Weatherlight, em Évora.",
                 "offers": {"@type": "Offer", "price": f"{float(f['preco']):.2f}", "priceCurrency": "EUR", "url": f.get('inscricao') or url,
                            "availability": "https://schema.org/" + ("SoldOut" if f.get('esgotado') else "InStock")}}
        faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": sem_tags(a)}} for q, a in perg]}
        bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Calendário Weatherlight", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": f"Eventos de {f['nome_jogo']}", "item": f"{BASE}/{pasta}/"},
            {"@type": "ListItem", "position": 3, "name": f['evento'], "item": url}]}
        desc = f"{f['evento']} de {f['nome_jogo']} na Weatherlight, em Évora: {quando}. {pr}." + (f" Formato: {fmt}." if fmt else "")
        img = f'<img src="/img/{f["arte"]}-g.jpg" alt="" width="180" height="240">' if f.get('arte') else ''
        loja = MARCAS.get(f['nome_jogo'])
        page = cabeca(f"{f['evento']} · {f['nome_jogo']} em Évora | Weatherlight", desc, url, [ev_ld, faq, bc], css) + f"""
<body>
<header>
  <div class="wrap">
    <span class="crumbs"><a href="/">Calendário Weatherlight</a> › <a href="/{pasta}/">{html.escape(f['nome_jogo'])}</a></span>
    <h1>{html.escape(f['evento'])}</h1>
    <p class="sub">{html.escape(f['nome_jogo'])} em Évora · {quando}</p>
  </div>
</header>
<main>
  <div class="wrap">
    {f'<p class="passou">Este evento já aconteceu.'+(f' O próximo {html.escape(f["_prox"]["tipo"])} é {("no " if data_longa(f["_prox"]["iso"]).startswith(("Sábado","Domingo")) else "na ")+data_longa(f["_prox"]["iso"]).lower()}: <a href="{f["_prox"]["url"]}">{html.escape(f["_prox"]["evento"])}</a>.' if f.get('_prox') else f' Vê os <a href="/{pasta}/">próximos eventos de {html.escape(f["nome_jogo"])}</a>.')+(f' <a href="{f["_recap"]}">Vê as fotos dessa semana no Instagram ↗</a>' if f.get('_recap') else '')+' · <a href="/arquivo/">Arquivo de eventos</a></p>' if passou else ''}
    <ul class="facts">
      <li><small>Quando</small><strong>{quando}</strong></li>
      <li><small>Preço</small><strong>{pr}</strong></li>
      {f'<li><small>Formato</small><strong>{html.escape(fmt)}</strong></li>' if fmt else ''}
      <li><small>Onde</small><strong><a href="{MAPS}">Weatherlight, Évora</a></strong></li>
    </ul>
    {f'<div class="acoes">{b2 if not passou else ""}{cal}</div>' if (b2 and not passou) or cal else ''}
    {f'<p class="m">Código Companion: <span class="code">{html.escape(f["companion"])}</span> (na app, toca em <em>Enter Event Code</em>)</p>' if f.get('companion') and not passou else ''}
    <section class="intro"><div class="box"><h2>Como funciona</h2><p class="pre">{html.escape(txt or "Detalhes em breve! Entretanto, acompanha o nosso Discord.")}</p></div>{img}</section>
    <section class="box faq"><h2>Perguntas frequentes</h2><dl>{''.join(f'<dt>{html.escape(q)}</dt><dd>{a}</dd>' for q, a in perg)}</dl></section>
    <section class="sec"><h2>Mais eventos</h2><div class="rel">
      <a class="card" href="/{pasta}/"><strong>Eventos de {html.escape(f['nome_jogo'])}</strong><span>Regulares e especiais</span><em>Ver página →</em></a>
      <a class="card" href="/"><strong>Calendário Weatherlight</strong><span>Todos os eventos desta semana</span><em>Ver calendário →</em></a>
      {f'<a class="card" href="{loja}"><strong>Produtos de {html.escape(f["nome_jogo"])}</strong><span>Na loja Weatherlight</span><em>Ver na loja ↗</em></a>' if loja else ''}
    </div></section>
  </div>
</main>
{RODAPE}
<script async src="https://tally.so/widgets/embed.js"></script>
</body>
</html>
"""
        os.makedirs(os.path.join(RAIZ, pasta, slug), exist_ok=True)
        fn = os.path.join(RAIZ, pasta, slug, 'index.html'); open(fn, 'w').write(ALVO(page))
        series.OG.append((fn, url, quando.upper(), f['evento'], f"{f['nome_jogo']} · {pr}", [f['arte']] if f.get('arte') else []))
        urls.append(url)
    return urls


# ---------------- página "Primeira vez na Weatherlight" ----------------
NOMES = {"magic": "Magic: The Gathering", "poke": "Pokémon TCG", "op": "One Piece Card Game", "digi": "Digimon Card Game",
         "gundam": "Gundam Card Game", "ygo": "Yu-Gi-Oh!", "rift": "Riftbound", "cyber": "Cyberpunk TCG"}


def primeira_vez(SER):
    url = f"{BASE}/primeira-vez/"
    jogos = []
    for s in SER:
        if s['jogo'] not in [j for j, _ in jogos]: jogos.append((s['jogo'], s['nome_jogo']))
    apps = ''.join(f'<li><span><a href="/{PASTA[g]}/">{html.escape(n)}</a></span><span>{html.escape(PRECISA[g])}</span></li>' for g, n in jogos if g in PRECISA)
    passos = [("Escolhe o evento", 'Vê o <a href="/">Calendário Weatherlight</a> ou a página do teu jogo. Os eventos semanais são os ideais para começar: são pensados para jogar, aprender e divertir-te.'),
              ("Prepara a aplicação do jogo", "A maioria dos jogos usa uma aplicação oficial para as inscrições, as rondas e os resultados. A conta é obrigatória: trata dela antes de vir (vê a lista em baixo)."),
              ("Inscreve-te", "Nos eventos com o botão <strong>Inscreve-te</strong>, a inscrição é feita na aplicação. Nos eventos de Magic, entras com o <strong>Código Companion</strong> que está no calendário."),
              ("Faz o check-in no balcão", "No dia, faz o check-in no nosso balcão com um de nós, dentro do horário indicado nos detalhes do evento. O pagamento da inscrição é feito nesse momento.")]
    faq_keys = ['primeira', 'sozinho', 'iniciante', 'competitivos', 'sleeves_ilustradas', 'sleeves_ygo']
    perg = [CENTRAL[k] for k in faq_keys if k in CENTRAL]
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in perg]}
    desc = "Vais ao teu primeiro evento na Weatherlight, em Évora? Como funciona o check-in, que aplicações precisas para cada jogo, o que levar e respostas às dúvidas mais comuns."
    css = (".passos{list-style:none;margin:0;padding:0;display:grid;gap:.6rem;counter-reset:p}"
           ".passos li{counter-increment:p;background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:.8rem 1rem;display:grid;grid-template-columns:1.6rem minmax(0,1fr);column-gap:.9rem;align-items:center}"
           ".passos li::before{content:counter(p);grid-row:1;grid-column:1;width:1.6rem;height:1.6rem;border-radius:50%;background:var(--sea-2);color:#fff;display:grid;place-items:center;font-size:.9rem;line-height:1}"
           ".passos li>strong{grid-row:1;grid-column:2;font-weight:500}.passos li>p{grid-row:2;grid-column:2;margin-top:.15rem}"
           ".horario li span:last-child{color:var(--muted)}"
           ".passos p strong{font-weight:500;color:var(--ink)}.passos p{margin:0;color:var(--muted)}.passos a{color:var(--sea-2)}"
           ".apps li{display:grid;grid-template-columns:minmax(9rem,15rem) 1fr;gap:.2rem 1rem}.apps li span:last-child{color:var(--muted)}"
           "@media (max-width:560px){.apps li{grid-template-columns:1fr}}")
    page = cabeca("Primeira vez num evento? | Weatherlight, Évora", desc, url, [faq], css) + f"""
<body>
<header>
  <div class="wrap">
    <span class="crumbs"><a href="/">Calendário Weatherlight</a> › Primeira vez</span>
    <h1>Primeira vez na Weatherlight</h1>
    <p class="sub">Tudo o que precisas de saber antes do teu primeiro evento</p>
  </div>
</header>
<main>
  <div class="wrap">
    <section class="sec"><h2>Como funciona</h2><ol class="passos">{''.join(f'<li><strong>{t}</strong><p>{p}</p></li>' for t, p in passos)}</ol></section>
    <section class="box"><h2>Que aplicação preciso?</h2><ul class="dates apps">{apps}</ul>
      <p class="m small">Em caso de dúvida, pergunta-nos no balcão ou no <a href="{DISCORD}">Discord</a>.</p></section>
    <section class="box"><h2>Horário da loja</h2><ul class="dates horario">{''.join(f'<li><span>{d}</span><span>{h}</span></li>' for d, h in HORARIO)}</ul>
      <p class="m small">Rua Frei José Maria Évora, Nº2, Évora · <a href="{MAPS}">Ver no mapa</a> · 266 735 119</p></section>
    <section class="box"><h2>O que levar</h2>
      <p class="m">Nos eventos <strong>Constructed</strong> trazes o teu baralho. Nos <strong>Sealed</strong>, <strong>Draft</strong> e <strong>Prereleases</strong> recebes as cartas no próprio evento e constróis o baralho na hora, por isso não precisas de trazer nada.</p>
      <p class="m" style="margin-top:.7rem">Ainda não tens baralho? Temos decks pré-construídos prontos para começares: pergunta-nos na loja.</p></section>
    <section class="box faq"><h2>Perguntas frequentes</h2><dl>{''.join(f'<dt>{html.escape(q)}</dt><dd>{html.escape(a)}</dd>' for q, a in perg)}</dl>
      <p class="m" style="margin-top:.9rem">Mais respostas na <a href="{CA}">Central de Ajuda</a>. Algum termo novo? Vê o <a href="{GL}">Glossário</a>.</p></section>
    <section class="sec"><h2>Escolhe o teu jogo</h2><div class="rel">{''.join(f'<a class="card" href="/{PASTA[g]}/"><strong>{html.escape(n)}</strong><em>Ver eventos →</em></a>' for g, n in jogos)}</div></section>
  </div>
</main>
<footer><div class="wrap"><p class="close">Tens dúvidas? Junta-te à nossa comunidade no <a href="{DISCORD}">Discord</a>! 👾</p></div></footer>
</body>
</html>
"""
    os.makedirs(os.path.join(RAIZ, 'primeira-vez'), exist_ok=True)
    fn = os.path.join(RAIZ, 'primeira-vez', 'index.html'); open(fn, 'w').write(ALVO(page))
    series.OG.append((fn, url, "Évora · Weatherlight", "Primeira vez num evento?", "Check-in, aplicações, o que levar", []))
    return [url]


# ---------------- calendários para subscrever ----------------
def feeds(FEED):
    vistos = {}
    for nome, (g, ev) in FEED.items():
        k = (re.search(r'DTSTART:(\S+)', ev).group(1), g)
        vistos.setdefault(k, (g, ev))
    def escreve(fn, titulo, evs):
        cab = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Weatherlight//Calendario//PT", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
               f"X-WR-CALNAME:{titulo}", "X-WR-TIMEZONE:Europe/Lisbon", "X-WR-CALDESC:Eventos da Weatherlight em Évora",
               "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H"]
        corpo = "".join("BEGIN:VEVENT" + ev + "END:VEVENT\r\n" for _, ev in evs)
        open(fn, 'w', newline='').write("\r\n".join(cab) + "\r\n" + corpo + "END:VCALENDAR\r\n")
    escreve(os.path.join(RAIZ, 'calendario.ics'), "Weatherlight · Eventos", list(vistos.values()))
    for g, pasta in PASTA.items():
        if os.path.isdir(os.path.join(RAIZ, pasta)):
            escreve(os.path.join(RAIZ, pasta, 'calendario.ics'), f"Weatherlight · {NOMES.get(g, pasta.replace('-', ' ').title())}",
                    [v for v in vistos.values() if v[0] == g])


# ---------------- llms.txt ----------------
def llms(SER, FUT, S):
    hoje = dt.date.today().isoformat()
    L = ["# Weatherlight Games & Collectibles — eventos em Évora", "",
         "> Weatherlight é uma loja de jogos (Local Game Store) em Évora, Portugal, com Trading Card Games, TTRPGs, Model Kits e colecionáveis. "
         "Organiza eventos semanais e especiais de Magic: The Gathering, Pokémon TCG, One Piece Card Game, Yu-Gi-Oh!, Riftbound, Digimon, Gundam Card Game, Gundam Assemble e Cyberpunk TCG.", "",
         "## Loja", "- Morada: Rua Frei José Maria Évora, Nº2, 7005-495 Évora, Portugal", "- Telefone: +351 266 735 119",
         "- Email: weatherlightgames@gmail.com", "- Horário: " + "; ".join(f"{d}: {h}" for d, h in HORARIO), "- Loja online: https://www.weatherlightgames.pt/", f"- Mapa: {MAPS}",
         "- Instagram: https://www.instagram.com/weatherlightgames/", f"- Discord (comunidade): {DISCORD}", "",
         "## Calendário", f"- [Calendário da semana]({BASE}/): {S['semana']}, atualizado todas as semanas.",
         f"- [Calendário para subscrever (.ics)]({BASE}/calendario.ics)", f"- [Primeira vez num evento]({BASE}/primeira-vez/): check-in, aplicações por jogo, o que levar.", "",
         "## Eventos regulares (todas as semanas; em feriados e férias confirmar no calendário)"]
    for s in sorted(SER, key=lambda s: (list(PL).index(s['dia']), s['hora'])):
        L.append(f"- [{s['titulo']} — {s['nome_jogo']}]({BASE}/{s['slug']}/): {PL[s['dia']].lower()} às {s['hora']}, {preco_txt(float(s['preco']))}")
    fut = [f for f in sorted(FUT, key=lambda x: (x['iso'], x['hora'])) if f['iso'] >= hoje]
    if fut:
        L += ["", "## Próximos eventos especiais"]
        L += [f"- [{f['evento']} — {f['nome_jogo']}]({BASE}/{PASTA.get(f['jogo'], f['jogo'])}/{esp_slug(f)}/): {data_longa(f['iso']).lower()} às {f['hora']}, {preco_txt(float(f['preco']))}" for f in fut]
    L += ["", "## Como participar",
          "- Inscrição na aplicação oficial de cada jogo (conta obrigatória): Bandai TCG+ (One Piece, Digimon, Gundam Card Game), Melee (Cyberpunk TCG), Riftbound Gaming Network (Riftbound), Neuron com KONAMI ID (Yu-Gi-Oh!), Magic: The Gathering Companion com conta Wizards (Magic), Player ID da Pokémon (Pokémon TCG).",
          "- O pagamento da inscrição é feito no check-in, no balcão da loja.", "", "## Páginas por jogo"]
    for g, pasta in PASTA.items():
        if os.path.isdir(os.path.join(RAIZ, pasta)): L.append(f"- [Eventos de {NOMES.get(g, pasta.replace('-', ' ').title())}]({BASE}/{pasta}/)")
    open(os.path.join(RAIZ, 'llms.txt'), 'w').write("\n".join(L) + "\n")


# ---------------- imagens de partilha (Open Graph) ----------------
def fonte(tam, peso=500):
    f = ImageFont.truetype(FONTE, tam)
    try: f.set_variation_by_axes([peso])
    except Exception: pass
    return f


def quebra(d, txt, f, larg, maxl):
    pal = txt.split(); linhas = []; cur = ''
    for p in pal:
        t = (cur + ' ' + p).strip()
        if d.textlength(t, font=f) <= larg: cur = t
        else: linhas.append(cur); cur = p
    linhas.append(cur)
    if len(linhas) > maxl: linhas = linhas[:maxl]; linhas[-1] = linhas[-1].rstrip('.,') + '…'
    return linhas


FUNDO = None
def og_img(fn, kicker, titulo, sub, artes):
    global FUNDO
    W, H = 1200, 630
    if FUNDO is None:
        b = Image.open(os.path.join(RAIZ, 'nuvens.jpg')).convert('RGB'); r = max(W / b.width, H / b.height)
        b = b.resize((int(b.width * r) + 1, int(b.height * r) + 1)); x = (b.width - W) // 2; y = int((b.height - H) * .35)
        b = b.crop((x, y, x + W, y + H)); FUNDO = Image.blend(b, Image.new('RGB', (W, H), (238, 243, 243)), .45)
    im = FUNDO.copy(); d = ImageDraw.Draw(im)
    artes = [a for a in artes if a and os.path.exists(os.path.join(RAIZ, 'img', a + '-g.jpg'))][:3]
    if artes:
        n = len(artes); h = 440 if n == 1 else 380; w = int(h * 3 / 4); passo = 120
        tot = w + passo * (n - 1); x0 = W - 70 - tot; y0 = (H - h) // 2
        for i, a in enumerate(artes):
            t = Image.open(os.path.join(RAIZ, 'img', a + '-g.jpg')).convert('RGB').resize((w, h), Image.LANCZOS)
            fr = Image.new('RGB', (w + 12, h + 12), (255, 255, 255)); fr.paste(t, (6, 6))
            m = Image.new('L', fr.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, fr.width, fr.height), 16, fill=255)
            dy = (n - 1 - i) * 14 if n > 1 else 0
            im.paste(fr, (x0 + i * passo - 6, y0 - 6 + dy), m)
        larg = x0 - 70 - 40
    else:
        larg = W - 140
    tit = fonte(68 if len(titulo) < 26 else 58); linhas = quebra(d, titulo.upper(), tit, larg, 3)
    y = 120
    d.text((70, y), kicker.upper(), font=fonte(26), fill=(138, 95, 31)); y += 52
    for l in linhas: d.text((70, y), l, font=tit, fill=(31, 61, 71)); y += int(tit.size * 1.12)
    y += 14
    for l in quebra(d, sub, fonte(32, 400), larg, 2): d.text((70, y), l, font=fonte(32, 400), fill=(51, 82, 92)); y += 42
    d.text((70, H - 80), "WEATHERLIGHT · ÉVORA", font=fonte(24), fill=(51, 82, 92))
    d.text((70, H - 48), "eventos.weatherlightgames.pt", font=fonte(22, 400), fill=(91, 113, 121))
    im.save(fn, quality=84, optimize=True, progressive=True)


def og_tags(fn_html, url, kicker, titulo, sub, artes):
    os.makedirs(os.path.join(RAIZ, 'og'), exist_ok=True)
    rel = url[len(BASE):].strip('/').replace('/', '-') or 'calendario'
    og_img(os.path.join(RAIZ, 'og', rel + '.jpg'), kicker, titulo, sub, artes)
    p = open(fn_html).read()
    p = re.sub(r'\n?<meta (property="og:[^"]+"|name="twitter:[^"]+"|name="theme-color"|name="apple-mobile[^"]+"|name="mobile-web[^"]+")[^>]*>', '', p)
    p = re.sub(r'\n?<link rel="(manifest|icon|apple-touch-icon)"[^>]*>', '', p)
    t = html.unescape(re.search(r'<title>(.*?)</title>', p, re.S).group(1))
    dsc = re.search(r'<meta name="description" content="([^"]*)"', p); dsc = html.unescape(dsc.group(1)) if dsc else sub
    import hashlib
    img = f"{BASE}/og/{rel}.jpg?v=" + hashlib.md5(open(os.path.join(RAIZ, 'og', rel + '.jpg'), 'rb').read()).hexdigest()[:8]
    tags = "".join(f'\n<meta property="{k}" content="{html.escape(v)}">' for k, v in [
        ("og:type", "website"), ("og:site_name", "Calendário Weatherlight"), ("og:locale", "pt_PT"), ("og:title", t),
        ("og:description", dsc), ("og:url", url), ("og:image", img), ("og:image:width", "1200"), ("og:image:height", "630")])
    tags += f'\n<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:image" content="{img}">'
    tags += ('\n<link rel="manifest" href="/manifest.webmanifest">\n<link rel="icon" type="image/png" sizes="32x32" href="/app/favicon-32.png">'
             '\n<link rel="apple-touch-icon" href="/app/apple-touch-icon.png">\n<meta name="theme-color" content="#ffffff">'
             '\n<meta name="apple-mobile-web-app-title" content="Weatherlight">\n<meta name="apple-mobile-web-app-capable" content="yes">'
             '\n<meta name="mobile-web-app-capable" content="yes">')
    i = p.index('</title>') + len('</title>'); p = p[:i] + tags + p[i:]
    open(fn_html, 'w').write(p)


# ---------------- tudo ----------------
def recolher(DET, FUT, serie_de, modelo):
    """Eventos especiais de todas as semanas do histórico + futuros.json (sem repetidos)."""
    import glob
    hist = os.path.join(AQUI, 'historico'); semanas = []
    for fn in sorted(glob.glob(os.path.join(hist, '*.json'))):
        H = json.load(open(fn)); semanas.append(H)
    chave = lambda e: (e['iso'], e['jogo'], e['hora'])
    todos = {chave(f): f for f in FUT}
    for H in semanas:
        for d in H['dias']:
            for e in d['eventos']:
                if serie_de(e): continue
                x = dict(e, iso=d['iso'])
                k = chave(x)
                if k in todos:
                    todos[k].setdefault('texto', x.get('texto'))
                    continue
                x.setdefault('texto', modelo(e)); x['_slug'] = esp_slug(x) + '-' + d['iso']
                todos[k] = x
    return semanas, sorted(todos.values(), key=lambda e: (e['iso'], e['hora']))


def tipo(e):
    if e.get('tipo'): return e['tipo']
    m = e.get('modelo') or e['evento']
    return re.sub(r"\s*\(.*\)$", "", m)


def url_esp(e): return f"/{PASTA.get(e['jogo'], e['jogo'])}/{e.get('_slug') or (esp_slug(e) + '-' + e['iso'] if e.get('_slug_sufixo') else esp_slug(e))}/"


CURTO = {"magic": "Magic", "poke": "Pokémon", "op": "One Piece", "ygo": "Yu-Gi-Oh!", "rift": "Riftbound", "digi": "Digimon",
         "gundam": "Gundam Card Game", "assemble": "Gundam Assemble", "cyber": "Cyberpunk"}


def arquivo(semanas, ESP, RECAP):
    hoje = dt.date.today().isoformat()
    sem_por_ini = {H['dias'][0]['iso']: H for H in semanas}
    def card(e):
        x = dt.date.fromisoformat(e['iso'])
        im = f'<img src="/img/{e["arte"]}-v.jpg" alt="" width="90" height="120" loading="lazy">' if e.get('arte') else '<span class="ph"></span>'
        return (f'<a class="card ec" data-game="{e["jogo"]}" href="{url_esp(e)}">{im}<div><small>{DIA_NOME[x.weekday()]} · {x.day:02d}/{x.month:02d}</small>'
                f'<strong>{html.escape(e["evento"])}</strong><span class="chip c-{e["jogo"]}">{html.escape(CURTO.get(e["jogo"], e["nome_jogo"]))}</span></div></a>')
    passados = [e for e in ESP if e['iso'] < hoje]
    blocos = ''; mes_atual = None; jogos = []
    # agrupar por semana (segunda a domingo); título e nº de eventos vêm do histórico quando existe
    semanas_d = {}
    for e in passados:
        x = dt.date.fromisoformat(e['iso']); seg = x - dt.timedelta(x.weekday())
        semanas_d.setdefault(seg, []).append(e)
    def hist_de(seg):
        for H in semanas:
            x = dt.date.fromisoformat(H['dias'][0]['iso'])
            if x - dt.timedelta(x.weekday()) == seg: return H
    for seg in sorted(semanas_d, reverse=True):
        evs = semanas_d[seg]; H = hist_de(seg); dom = seg + dt.timedelta(6)
        m0 = dt.date.fromisoformat(min(e['iso'] for e in evs)); mes = f"{MESES[m0.month-1].capitalize()} {m0.year}"
        if mes != mes_atual: blocos += f'<h2 class="mes">{mes}</h2>'; mes_atual = mes
        tit = H['semana'] if H else (f"Semana de {seg.day} a {dom.day} de {MESES[dom.month-1]}" if seg.month == dom.month else f"Semana de {seg.day} de {MESES[seg.month-1]} a {dom.day} de {MESES[dom.month-1]}")
        info = (f"{sum(len(d['eventos']) for d in H['dias'])} eventos · " if H else '') + f"{len(evs)} especia{'is' if len(evs) != 1 else 'l'}"
        rc = RECAP.get(seg.isoformat()) or (RECAP.get(H['dias'][0]['iso']) if H else None)
        blocos += (f'<section class="sem"><div class="sem-h"><h3>{html.escape(tit)}</h3><span>{info}'
                   + (f' · <a href="{rc}">Fotos da semana no Instagram ↗</a>' if rc else '') + '</span></div>'
                   f'<div class="rel">{"".join(card(e) for e in sorted(evs, key=lambda e: (e["iso"], e["hora"])))}</div></section>')
        for e in evs:
            if e['jogo'] not in jogos: jogos.append(e['jogo'])
    # eventos anteriores ao histórico semanal (enviados pela equipa), em anteriores.json
    chips = ''.join(f'<button type="button" class="f" data-g="{g}" aria-pressed="false">{html.escape(next(e["nome_jogo"] for e in passados if e["jogo"]==g))}</button>' for g in jogos)
    url = f"{BASE}/arquivo/"
    desc = "Arquivo dos eventos especiais da Weatherlight em Évora: Prereleases, Release Events, Store Championships e torneios de Magic, Pokémon, One Piece, Yu-Gi-Oh!, Riftbound, Gundam, Digimon e Cyberpunk."
    css = (".mes{font:500 1.3rem/1.2 var(--display);text-transform:uppercase;letter-spacing:.05em;margin:1.6rem 0 .2rem;color:var(--brass)}.mes:first-of-type{margin-top:0}"
           ".sem{margin-top:.9rem}.sem-h{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:.2rem 1rem;margin-bottom:.5rem}"
           ".sem-h h3{font:500 1rem var(--body);margin:0}.sem-h span{font-size:.88rem;color:var(--muted)}.sem-h a{color:var(--sea-2)}"
           ".ec{grid-template-columns:72px minmax(0,1fr);align-items:start;gap:.9rem}.ec img,.ec .ph{width:72px;aspect-ratio:3/4;height:auto;border-radius:5px;object-fit:cover;background:var(--foam);display:block}"
           ".ec div{display:grid;gap:.2rem;min-width:0}.ec small{font-size:.74rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}.ec .chip{font-size:.66rem}"
           ".rel:has(.ec){align-items:stretch}.ec{height:100%;min-height:140px}.ec strong{font-size:.98rem;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.ec small{font-size:.7rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.ec .chip,.ec span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}.sem .rel{grid-template-columns:repeat(auto-fill,minmax(17rem,1fr))}.filters{margin:0 0 1rem}[hidden]{display:none!important}")
    page = cabeca("Arquivo de eventos | Weatherlight, Évora", desc, url, [], css) + f"""
<body>
<header>
  <div class="wrap">
    <span class="crumbs"><a href="/">Calendário Weatherlight</a> › Arquivo</span>
    <h1>Arquivo de eventos</h1>
    <p class="sub">Os eventos especiais que já fizemos na Weatherlight, desde o nosso aniversário a 25 de setembro</p>
  </div>
</header>
<main>
  <div class="wrap">
    <div class="filters" role="group" aria-label="Filtrar por jogo"><button type="button" class="f" data-g="all" aria-pressed="true">Todos</button>{chips}</div>
    {blocos or '<p>Ainda não há eventos no arquivo.</p>'}
    <p class="m small">Os próximos eventos estão no <a href="/">Calendário Weatherlight</a>.</p>
  </div>
</main>
{RODAPE}
<script>(function(){{var b=[].slice.call(document.querySelectorAll('.f'));function a(g){{b.forEach(function(x){{x.setAttribute('aria-pressed',String(x.dataset.g===g))}});
document.querySelectorAll('.sem').forEach(function(s){{var v=0;s.querySelectorAll('.card').forEach(function(c){{var on=g==='all'||c.dataset.game===g;c.hidden=!on;if(on)v++}});s.hidden=!v}});
document.querySelectorAll('.mes').forEach(function(m){{var n=m.nextElementSibling,v=false;while(n&&!n.classList.contains('mes')){{if(!n.hidden&&n.classList.contains('sem'))v=true;n=n.nextElementSibling}}m.hidden=!v}})}}
b.forEach(function(x){{x.addEventListener('click',function(){{a(x.dataset.g)}})}})}})();</script>
</body>
</html>
"""
    os.makedirs(os.path.join(RAIZ, 'arquivo'), exist_ok=True)
    fn = os.path.join(RAIZ, 'arquivo', 'index.html'); open(fn, 'w').write(ALVO(page))
    series.OG.append((fn, url, "Évora · Weatherlight", "Arquivo de eventos", "Os eventos especiais que já fizemos", [e.get('arte') for e in reversed(passados)][:3]))
    return url, passados


def ja_fizemos(passados):
    """Secção 'Já fizemos' nas páginas de cada jogo."""
    for g, pasta in PASTA.items():
        fn = os.path.join(RAIZ, pasta, 'index.html')
        if not os.path.exists(fn): continue
        evs = [e for e in passados if e['jogo'] == g][-4:][::-1]
        if not evs: continue
        def c(e):
            x = dt.date.fromisoformat(e['iso'])
            im = f'<img src="/img/{e["arte"]}-v.jpg" alt="" width="90" height="120" loading="lazy">' if e.get('arte') else '<span class="ph"></span>'
            return f'<a class="card ec" href="{url_esp(e)}">{im}<div><small>{x.day:02d}/{x.month:02d}/{x.year}</small><strong>{html.escape(e["evento"])}</strong><em>Ver página →</em></div></a>'
        sec = f'<section class="sec"><h2>Já fizemos</h2><div class="rel">{"".join(c(e) for e in evs)}</div><p class="m small">Vê todos no <a href="/arquivo/">Arquivo de eventos</a>.</p></section>\n  </div>\n</main>'
        p = open(fn).read(); p = p.replace('\n  </div>\n</main>', '\n    ' + sec, 1); open(fn, 'w').write(p)


def gerar(tpl, SER, DET, S, FUT, FEED, ld, inscricao, serie_de=lambda e: None, modelo=lambda e: None):
    urls = list(series.URLS)
    RP = os.path.join(AQUI, 'recaps.json'); RECAP = json.load(open(RP)) if os.path.exists(RP) else {}
    semanas, ESP = recolher(DET, FUT, serie_de, modelo)
    hoje = dt.date.today().isoformat()
    for H in semanas:
        isos = [d['iso'] for d in H['dias']]
        for e in ESP:
            if isos[0] <= e['iso'] <= isos[-1] and H['dias'][0]['iso'] in RECAP: e['_recap'] = RECAP[H['dias'][0]['iso']]
    for e in ESP:
        x = dt.date.fromisoformat(e['iso']); seg = (x - dt.timedelta(x.weekday())).isoformat()
        if seg in RECAP: e.setdefault('_recap', RECAP[seg])
    for e in ESP:
        if e['iso'] < hoje:
            nx = [f for f in ESP if f['iso'] >= hoje and f['jogo'] == e['jogo'] and tipo(f) == tipo(e)]
            if nx: e['_prox'] = {"iso": nx[0]['iso'], "evento": nx[0]['evento'], "url": url_esp(nx[0]), "tipo": tipo(e)}
    esp = especiais(DET, ESP, inscricao); urls += esp
    u, passados = arquivo(semanas, ESP, RECAP); urls.append(u)
    ja_fizemos(passados)
    urls += primeira_vez(SER)
    feeds(FEED); llms(SER, FUT, S)
    # dados da loja na página principal
    fn = os.path.join(RAIZ, 'index.html'); p = open(fn).read()
    p = re.sub(r'\n<script type="application/ld\+json" id="loja">.*?</script>', '', p, flags=re.S)
    p = p.replace('</head>', f'\n<script type="application/ld+json" id="loja">{json.dumps(LOJA, ensure_ascii=False)}</script>\n</head>', 1)
    open(fn, 'w').write(p)
    # imagem de partilha da semana: primeiro os eventos especiais (os que não são regulares), depois os restantes
    hoje = dt.date.today().isoformat()
    regs = {s.get('arte') for s in SER}
    evs = [e for d in S['dias'] for e in d['eventos'] if e.get('arte') and d['iso'] >= hoje]
    artes = [e['arte'] for e in evs if e['arte'] not in regs] + [e['arte'] for e in evs]
    artes = [a for i, a in enumerate(artes) if a not in artes[:i]][:3]
    og_tags(fn, BASE + '/', S['semana'], "Calendário Weatherlight", "Eventos semanais na tua Local Game Store em Évora", artes)
    for x in series.OG: og_tags(*x)
    series.OG.clear()
    open(os.path.join(RAIZ, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        ''.join(f'  <url><loc>{u}</loc></url>\n' for u in dict.fromkeys(urls)) + '</urlset>\n')
    return len(esp)
