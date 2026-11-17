# Página em inglês (/en/) para turistas, estudantes Erasmus e jogadores de passagem por Évora.
# Gerada a partir de series.json (eventos regulares) e futuros.json (eventos especiais): fica sempre atualizada.
import datetime as dt, html, json, os
import series
from series import BASE, MAPS, DISCORD, PASTA, preco_txt, esp_slug

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAS = {"Monday": "Mondays", "Tuesday": "Tuesdays", "Wednesday": "Wednesdays", "Thursday": "Thursdays",
        "Friday": "Fridays", "Saturday": "Saturdays", "Sunday": "Sundays"}
ORDEM = list(DIAS)
WD = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MESES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
# Igual a HORARIO em extras.py (mudar os dois juntos)
HOURS = [("Monday and Tuesday", "Closed"), ("Wednesday and Friday", "3 pm – 11 pm"), ("Thursday, Saturday and Sunday", "3 pm – 8:30 pm")]
# Igual a PRECISA em extras.py, em inglês
NEEDS = {"magic": "Magic: The Gathering Companion app and a Wizards account (you join with the event code)",
         "poke": "Pokémon Player ID (we can create one with you in store); the Pokémon Access app is recommended",
         "op": "Bandai TCG+ app and account", "digi": "Bandai TCG+ app and account", "gundam": "Bandai TCG+ app and account",
         "ygo": "Neuron app and KONAMI ID (we can create one with you in store)",
         "rift": "Riftbound Gaming Network account", "cyber": "Melee account"}


def preco(p):
    p = float(p)
    if p == 0: return "Free"
    return f"€{int(p)}" if p == int(p) else f"€{p:.2f}"


def hora(h):
    hh, mm = map(int, h.split(':'))
    return f"{(hh - 1) % 12 + 1}{'' if mm == 0 else f':{mm:02d}'} {'am' if hh < 12 else 'pm'}"


def data(iso):
    x = dt.date.fromisoformat(iso)
    return f"{WD[x.weekday()]}, {MESES[x.month - 1]} {x.day}"


def pagina(SER, FUT):
    url = f"{BASE}/en/"
    hoje = dt.date.today().isoformat()
    regs = sorted([s for s in SER if not s.get('pausa')], key=lambda s: (ORDEM.index(s['dia']), s['hora']))
    linhas = ''.join(
        f'<li><span>{DIAS[s["dia"]]} · {hora(s["hora"])}</span><span><a href="/{s["slug"]}/">{html.escape(s["titulo"])}</a> — {html.escape(s["nome_jogo"])}</span><span>{preco(s["preco"])}</span></li>'
        for s in regs)
    fut = [f for f in sorted(FUT, key=lambda x: (x['iso'], x['hora'])) if f['iso'] >= hoje][:8]
    esp = ''.join(
        f'<li><span>{data(f["iso"])} · {hora(f["hora"])}</span><span><a href="/{PASTA.get(f["jogo"], f["jogo"])}/{esp_slug(f)}/">{html.escape(f["evento"])}</a> — {html.escape(f["nome_jogo"])}</span><span>{preco(f["preco"])}</span></li>'
        for f in fut)
    jogos = []
    for s in SER:
        if s['jogo'] not in [j for j, _ in jogos]: jogos.append((s['jogo'], s['nome_jogo']))
    apps = ''.join(f'<li><span>{html.escape(n)}</span><span>{html.escape(NEEDS[g])}</span></li>' for g, n in jogos if g in NEEDS)
    desc = ("Trading card game store in Évora, Portugal. Weekly Magic: The Gathering, Pokémon, One Piece, Yu-Gi-Oh!, Riftbound, "
            "Digimon and Gundam tournaments, open to visitors. Schedule, prices and how to join.")
    ld = {"@context": "https://schema.org", "@type": "WebPage", "inLanguage": "en", "name": "Weatherlight — Game store in Évora, Portugal",
          "url": url, "about": {"@type": "GameStore", "name": "Weatherlight Games & Collectibles", "url": "https://www.weatherlightgames.pt/"}}
    css = (".evl{list-style:none;margin:0;padding:0}"
           ".evl li{display:grid;grid-template-columns:minmax(10rem,14rem) minmax(0,1fr) auto;gap:.15rem 1rem;padding:.5rem 0;border-top:1px dashed var(--line)}"
           ".evl li:first-child{border-top:0;padding-top:0}.evl li span:first-child,.evl li span:last-child{color:var(--muted)}"
           ".evl a,.box a{color:var(--link)}"
           ".apps li{display:grid;grid-template-columns:minmax(9rem,15rem) 1fr;gap:.2rem 1rem}.apps li span:last-child{color:var(--muted)}"
           ".horario li span:last-child{color:var(--muted)}.box p+p{margin-top:.7rem}"
           "@media (max-width:560px){.evl li{grid-template-columns:1fr auto}.evl li span:first-child{grid-column:1/-1}.apps li{grid-template-columns:1fr}}")
    head = series.SHELL
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Game store in Évora, Portugal: Magic, Pokémon & TCG tournaments | Weatherlight</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="{url}">
<link rel="alternate" hreflang="pt" href="{BASE}/">
{head['fonts']}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{head['style']}
{head['css2']}
<style>{css}</style>
</head>
<body>
<header>
  <div class="wrap">
    <span class="crumbs"><a href="/">Calendário Weatherlight</a> › English</span>
    <h1>Game store in Évora, Portugal</h1>
    <p class="sub">Trading card games, tournaments and collectibles at Weatherlight</p>
  </div>
</header>
<main>
  <div class="wrap">
    <section class="box"><h2>Welcome aboard</h2>
      <p class="m">Weatherlight Games &amp; Collectibles is a game store in the centre of Évora, open since 2020. We run around 15 events a week for Magic: The Gathering, Pokémon TCG, One Piece Card Game, Yu-Gi-Oh!, Riftbound, Digimon, Gundam and Cyberpunk TCG, from relaxed weekly events to official tournaments.</p>
      <p class="m">Visiting Évora? You are welcome to join any event. English cards are allowed in most official tournaments in Portugal, and you can buy boosters, decks, sleeves and other accessories in store.</p></section>
    <section class="box"><h2>Weekly events</h2><ul class="evl">{linhas}</ul>
      <p class="m small">Holidays and schedule changes are announced in the <a href="/">weekly calendar</a> (in Portuguese, with dates and times).</p></section>
    {f'<section class="box"><h2>Upcoming special events</h2><ul class="evl">{esp}</ul></section>' if esp else ''}
    <section class="box"><h2>How to join</h2>
      <p class="m">Most games use an official app for sign-ups, pairings and results, so create your account before you come. On the day, check in at our counter within the time shown in the event details. The entry fee is paid at check-in.</p>
      <ul class="dates apps" style="margin-top:.9rem">{apps}</ul>
      <p class="m small">For Constructed events, bring your own deck. For Sealed, Draft and Prereleases, you get the cards at the event. Questions? Ask us on <a href="{DISCORD}">Discord</a>.</p></section>
    <section class="box"><h2>Visit us</h2><ul class="dates horario">{''.join(f'<li><span>{d}</span><span>{h}</span></li>' for d, h in HOURS)}</ul>
      <p class="m small">Rua Frei José Maria Évora, Nº2, 7005-495 Évora, Portugal · <a href="{MAPS}">Open in Maps</a> · +351 266 735 119 · <a href="https://www.weatherlightgames.pt/">Online store</a> (in Portuguese)</p></section>
  </div>
</main>
<footer><div class="wrap"><p class="close">See you at the table! Join our community on <a href="{DISCORD}">Discord</a> or follow us on <a href="https://www.instagram.com/weatherlightgames/">Instagram</a>.</p></div></footer>
</body>
</html>
"""
    page = page.replace('<a href="http', '<a target="_blank" rel="noopener" href="http')
    os.makedirs(os.path.join(RAIZ, 'en'), exist_ok=True)
    fn = os.path.join(RAIZ, 'en', 'index.html'); open(fn, 'w').write(page)
    series.OG.append((fn, url, "Évora, Portugal", "Game store in Évora", "Weekly TCG tournaments, open to visitors", []))
    return [url]
