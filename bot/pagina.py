"""Página "Acabou de chegar" (/novidades/) e feed RSS (/novidades/feed.xml).

Lê novidades/dados.json (escrito pelo bot de novidades sempre que deteta produtos novos) e gera a página
com o mesmo visual do calendário. Corre no workflow do bot e também no build do calendário (extras.py).
"""
import datetime as dt, html, json, os, re
from email.utils import format_datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://eventos.weatherlightgames.pt"
LOJA = "https://www.weatherlightgames.pt"
DADOS = os.path.join(RAIZ, "novidades", "dados.json")
DIAS_PAGINA = 42          # a página mostra as últimas 6 semanas
MAX_DADOS = 400           # o ficheiro guarda no máximo 400 produtos
SEM = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

# Tipo do produto a partir do nome (ordem importa: o primeiro que bater ganha)
TIPOS = [
    ("Peluches", r"\b(plush|peluche)"),
    ("Blind Boxes", r"\b(blind ?box|gashapon|capsule|mystery|caixa surpresa|trading figure)"),
    ("Model Kits", r"\b(model kit|gunpla|gundam accessories|30 ?mm|figure-rise|kotobukiya)"),
    ("Figuras", r"\b(figura|figure|nendoroid|figma|statue|estátua)"),
    ("Acessórios", r"\b(sleeves?|deck ?box|playmat|binder|álbum|album|portfolio|dice|dados|toploader|pages|storage|tapete)"),
    ("RPG e Livros", r"\b(daggerheart|dungeons|d&d|rpg|livro|book|manga|mangá)"),
    ("TCG", r"\b(booster|deck|display|bundle|tin|collection|elite trainer|card game|tcg|starter|box)"),
]


def tipo(nome):
    n = (nome or "").lower()
    for t, rx in TIPOS:
        if re.search(rx, n): return t
    return "Outros"


def carregar():
    try: return json.load(open(DADOS))
    except (FileNotFoundError, ValueError): return []


def acrescentar(produtos, quando=None):
    """Junta produtos novos (dicts com url, nome, preco, imagem, stock) ao início do ficheiro."""
    quando = quando or dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
    dados = carregar(); urls = {d["url"] for d in dados}
    novos = [{"url": p["url"], "nome": p["nome"], "preco": p.get("preco"), "imagem": p.get("imagem"),
              "tipo": tipo(p["nome"]), "data": quando} for p in produtos if p["url"] not in urls]
    dados = (novos + dados)[:MAX_DADOS]
    os.makedirs(os.path.dirname(DADOS), exist_ok=True)
    json.dump(dados, open(DADOS, "w"), ensure_ascii=False, indent=1)
    return len(novos)


def preco(p):
    try: return f"{float(p):.2f} €".replace(".", ",")
    except (TypeError, ValueError): return ""


def lisboa(iso):
    """Data/hora em Lisboa (WET/WEST) sem depender de tzdata."""
    t = dt.datetime.fromisoformat(iso)
    if t.tzinfo is None: t = t.replace(tzinfo=dt.timezone.utc)
    t = t.astimezone(dt.timezone.utc)
    y = t.year
    ini = max(dt.datetime(y, 3, d, 1, tzinfo=dt.timezone.utc) for d in range(25, 32) if dt.date(y, 3, d).weekday() == 6)
    fim = max(dt.datetime(y, 10, d, 1, tzinfo=dt.timezone.utc) for d in range(25, 32) if dt.date(y, 10, d).weekday() == 6)
    return t + dt.timedelta(hours=1 if ini <= t < fim else 0)


def concha():
    """Fontes e estilos do calendário, tirados de uma página já gerada."""
    for f in ("en/index.html", "primeira-vez/index.html", "index.html"):
        p = os.path.join(RAIZ, f)
        if os.path.exists(p):
            t = open(p).read(); head = t.split("</head>")[0] if "</head>" in t else t.split("<body")[0]
            fontes = "\n".join(re.findall(r'<link rel="(?:preconnect|stylesheet)"[^>]*>', head))
            estilos = re.findall(r"<style>.*?</style>", head, re.S)
            return fontes, "\n".join(estilos[:2])
    return "", ""


def gerar():
    dados = carregar()
    limite = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DIAS_PAGINA)
    vis = [d for d in dados if dt.datetime.fromisoformat(d["data"]).astimezone(dt.timezone.utc) >= limite]
    grupos, ordem = {}, []
    for d in vis:
        l = lisboa(d["data"]); k = l.date()
        if k not in grupos: grupos[k] = []; ordem.append(k)
        grupos[k].append(d)
    tipos = [t for t, _ in TIPOS] + ["Outros"]
    presentes = [t for t in tipos if any(d["tipo"] == t for d in vis)]
    filtros = '<button class="chip on" data-t="">Tudo</button>' + "".join(
        f'<button class="chip" data-t="{html.escape(t)}">{html.escape(t)}</button>' for t in presentes)

    def card(d):
        img = (f'<img src="{html.escape(d["imagem"])}" alt="" loading="lazy">'
               if d.get("imagem") else '<i></i>')
        return (f'<a class="np" data-t="{html.escape(d["tipo"])}" href="{html.escape(d["url"])}" target="_blank" rel="noopener">'
                f'<span class="ph">{img}</span><span class="tg">{html.escape(d["tipo"])}</span>'
                f'<strong>{html.escape(d["nome"])}</strong><span class="pr">{preco(d.get("preco"))}</span>'
                f'<em>Ver na loja ↗</em></a>')

    blocos = "".join(
        f'<section class="dia"><h2>{SEM[k.weekday()].capitalize()}, {k.day} de {MES[k.month - 1]}</h2>'
        f'<div class="grid">{"".join(card(d) for d in grupos[k])}</div></section>' for k in ordem)
    if not blocos:
        blocos = '<section class="box"><p class="m">As novidades aparecem aqui assim que chegam à loja online.</p></section>'
    fontes, estilos = concha()
    url = f"{BASE}/novidades/"
    desc = ("Os produtos que acabaram de chegar à Weatherlight, em Évora: TCG, figuras de anime, blind boxes, "
            "Gunpla, peluches e acessórios. Atualizado automaticamente.")
    og = next((d["imagem"] for d in vis if d.get("imagem")), "")
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "Acabou de chegar — Weatherlight",
          "url": url, "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": d["url"], "name": d["nome"]}
                                          for i, d in enumerate(vis[:50])]}
    css = (".chips{display:flex;flex-wrap:wrap;gap:.5rem;margin:0 0 1.4rem}"
           ".chip{font:inherit;font-size:.9rem;padding:.4rem .9rem;border-radius:999px;border:1px solid var(--line);background:#fff;color:var(--ink);cursor:pointer}"
           ".chip.on{background:var(--ink);color:#fff;border-color:var(--ink)}"
           ".dia{margin:0 0 2rem}.dia h2{font-size:1.05rem;letter-spacing:.06em;text-transform:uppercase;margin:0 0 .8rem}"
           ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:1rem}"
           ".np{display:flex;flex-direction:column;gap:.35rem;background:#fff;border:1px solid var(--line);border-radius:12px;padding:.7rem;color:inherit;text-decoration:none;transition:transform .15s,box-shadow .15s}"
           ".np:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(40,70,85,.12)}"
           ".ph{display:block;aspect-ratio:1;background:#fff;border-radius:8px;overflow:hidden}"
           ".ph img{width:100%;height:100%;object-fit:contain;display:block;transform:scale(1.25)}.ph i{display:block;width:100%;height:100%;background:var(--foam)}"
           ".tg{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}"
           ".np strong{font-weight:500;font-size:.92rem;line-height:1.3;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}"
           ".pr{font-weight:600;color:var(--brass)}.np em{font-style:normal;font-size:.85rem;color:var(--link);margin-top:auto}"
           ".hid{display:none!important}"
           "@media (max-width:480px){.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:.7rem}}")
    js = ("document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{document.querySelectorAll('.chip').forEach(x=>x.classList.toggle('on',x===b));"
          "const t=b.dataset.t;document.querySelectorAll('.np').forEach(c=>c.classList.toggle('hid',!!t&&c.dataset.t!==t));"
          "document.querySelectorAll('.dia').forEach(s=>s.classList.toggle('hid',!s.querySelector('.np:not(.hid)')))});")
    page = f"""<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Acabou de chegar: novidades da Weatherlight em Évora</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<link rel="alternate" type="application/rss+xml" title="Novidades Weatherlight" href="{url}feed.xml">
<meta property="og:type" content="website"><meta property="og:title" content="Acabou de chegar — Weatherlight">
<meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{url}">
{f'<meta property="og:image" content="{html.escape(og)}">' if og else ''}
<link rel="icon" type="image/png" sizes="32x32" href="/app/favicon-32.png">
{fontes}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{estilos}
<style>{css}</style>
</head>
<body>
<header>
  <div class="wrap">
    <span class="crumbs"><a href="/">Calendário Weatherlight</a> › Novidades</span>
    <h1>Acabou de chegar</h1>
    <p class="sub">Os produtos novos da Weatherlight, assim que chegam à loja online</p>
    <div class="info"><a href="{LOJA}/" target="_blank" rel="noopener">🛒 Loja online</a><a href="https://discord.com/channels/685894659855220743/1573781369597861978" target="_blank" rel="noopener">🔔 Alertas no Discord</a><a href="{url}feed.xml">RSS</a><a href="/">📅 Eventos</a></div>
  </div>
</header>
<main>
  <div class="wrap">
    <div class="chips">{filtros}</div>
    {blocos}
    <p class="m small">Atualizado automaticamente de hora a hora. Preços e stock confirmados na loja online.</p>
  </div>
</main>
<footer><div class="wrap"><p class="close">Queres saber primeiro? Ativa as notificações do canal ✨│novidades-wl no nosso <a href="https://discord.com/channels/685894659855220743/1573781369597861978" target="_blank" rel="noopener">Discord</a>.</p></div></footer>
<script>{js}</script>
</body>
</html>
"""
    os.makedirs(os.path.join(RAIZ, "novidades"), exist_ok=True)
    open(os.path.join(RAIZ, "novidades", "index.html"), "w").write(page)
    # RSS
    itens = "".join(
        f"<item><title>{html.escape(d['nome'])}</title><link>{html.escape(d['url'])}</link><guid>{html.escape(d['url'])}</guid>"
        f"<pubDate>{format_datetime(dt.datetime.fromisoformat(d['data']).astimezone(dt.timezone.utc))}</pubDate>"
        f"<category>{html.escape(d['tipo'])}</category>"
        f"<description>{html.escape(preco(d.get('preco')) + ((' &lt;br&gt;&lt;img src=&quot;' + d['imagem'] + '&quot;&gt;') if d.get('imagem') else ''))}</description></item>"
        for d in dados[:60])
    rss = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Novidades Weatherlight</title>'
           f"<link>{url}</link><description>{html.escape(desc)}</description><language>pt-PT</language>{itens}</channel></rss>\n")
    open(os.path.join(RAIZ, "novidades", "feed.xml"), "w").write(rss)
    return url


if __name__ == "__main__":
    print(gerar())
