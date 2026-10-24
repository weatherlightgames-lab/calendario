"""Gera as páginas fixas dos eventos regulares (../<jogo>/<evento>/index.html), o sitemap.xml e o robots.txt.
Chamado no fim de build.py. Dados: series.json (eventos regulares), details.json (textos) e semana.json (datas desta semana)."""
import json, html, re, os
AQUI=os.path.dirname(os.path.abspath(__file__)); RAIZ=os.path.dirname(AQUI)
BASE='https://eventos.weatherlightgames.pt'
DISCORD='https://discord.gg/HTCZeJZuVk'; MAPS='https://maps.app.goo.gl/GnKdFUwrm1J6o46P9'
CA='https://www.weatherlightgames.pt/page/central-de-ajuda-weatherlight'; GL='https://www.weatherlightgames.pt/page/glossario'
MORADA='Rua Frei José Maria Évora, Nº2, 7005-495 Évora'
ADDR={"@type":"Place","name":"Weatherlight Games & Collectibles","address":{"@type":"PostalAddress","streetAddress":"Rua Frei José Maria Évora, Nº2","postalCode":"7005-495","addressLocality":"Évora","addressCountry":"PT"}}
ORG={"@type":"Organization","name":"Weatherlight Games & Collectibles","url":"https://www.weatherlightgames.pt"}
PL={"Monday":"Todas as segundas","Tuesday":"Todas as terças","Wednesday":"Todas as quartas","Thursday":"Todas as quintas",
    "Friday":"Todas as sextas","Saturday":"Todos os sábados","Sunday":"Todos os domingos"}

def formato(txt):
    m=re.search(r'Formato:[ \t]*(.*)',txt or '')
    if not m: return None
    if m.group(1).strip(): return m.group(1).strip()
    linhas=txt[m.end():].strip('\n').split('\n'); out=[]
    for l in linhas:
        if not l.strip(): break
        out.append(l.strip())
    return ' · '.join(out) or None

def participacao(txt):
    m=re.search(r'(E AINDA!|De participação:|PARTICIPAÇÃO:|GOODIES DE PARTICIPAÇÃO:)\s*\n+((?:- .*\n?)+)',txt or '')
    if not m: return []
    return [re.sub(r'[;.!]+$','',l[2:].strip()) for l in m.group(2).strip().split('\n') if l.startswith('- ')]

def preco_txt(p): return 'Gratuito' if p==0 else f"{p:.2f}".replace('.',',')+' €'

def gerar(tpl, SER, DET, S):
    style=tpl[tpl.index('<style>'):tpl.index('</style>')+8]
    fonts=re.search(r'<link rel="preconnect".*?display=swap">',tpl,re.S).group(0)
    urls=[BASE+'/']
    for s in SER:
        txt=DET.get(s['modelo']); fmt=formato(txt); part=participacao(txt); pr=preco_txt(float(s['preco']))
        quando=f"{PL[s['dia']]} · {s['hora']}"
        # datas desta semana (do calendário)
        datas=[(d,e) for d in S['dias'] for e in d['eventos'] if e['jogo']==s['jogo'] and (e['evento'] in s['eventos'] or e.get('modelo')==s['modelo'])]
        sub=[{"@type":"Event","name":f"{s['titulo']} - {s['nome_jogo']}","startDate":f"{d['iso']}T{e['hora']}:00{d['fuso']}",
              "location":ADDR,"eventAttendanceMode":"https://schema.org/OfflineEventAttendanceMode","eventStatus":"https://schema.org/EventScheduled",
              "offers":{"@type":"Offer","price":f"{float(e['preco']):.2f}","priceCurrency":"EUR",
                        "availability":"https://schema.org/"+("SoldOut" if e.get('esgotado') else "InStock")}} for d,e in datas]
        desc=f"{s['titulo']} de {s['nome_jogo']} em Évora: {PL[s['dia']].lower()} às {s['hora']} na Weatherlight. {pr}."+(f" Formato: {fmt}." if fmt else "")
        ld={"@context":"https://schema.org","@type":"EventSeries","name":f"{s['titulo']} - {s['nome_jogo']} em Évora","description":desc,
            "url":f"{BASE}/{s['slug']}/","location":ADDR,"organizer":ORG,
            "eventSchedule":{"@type":"Schedule","repeatFrequency":"P1W","byDay":f"https://schema.org/{s['dia']}","startTime":s['hora'],"scheduleTimezone":"Europe/Lisbon"},
            **({"image":f"{BASE}/img/{s['arte']}-g.jpg"} if s.get('arte') else {}), **({"subEvent":sub} if sub else {})}
        perg=[(f"Quando é a {s['titulo']}?", f"{PL[s['dia']]} às {s['hora']}, na Weatherlight Games & Collectibles ({MORADA}). Em feriados e férias, confirma no Calendário Weatherlight."),
              (f"Quanto custa participar?", f"{pr}."+(" Todos os participantes recebem: "+"; ".join(part)+"." if part else ""))]
        if fmt: perg.append(("Que formato se joga?", fmt+"."))
        perg+= [(q['pergunta'],q['resposta']) for q in s.get('perguntas',[])]
        faq={"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in perg]}
        if datas:
            prox='<ul class="dates">'+''.join(f'<li><span>{d["dia"]}, {d["data"]}</span><span>{e["hora"]} · {preco_txt(float(e["preco"]))}{" · Esgotado" if e.get("esgotado") else ""}</span></li>' for d,e in datas)+'</ul>'
        else:
            prox=f'<p class="m">Esta semana não há {html.escape(s["titulo"])}. Vê as próximas datas no <a href="/">Calendário Weatherlight</a>.</p>'
        outros=[o for o in SER if o['jogo']==s['jogo'] and o is not s]
        rel=''.join(f'<a href="/{o["slug"]}/"><strong>{html.escape(o["titulo"])}</strong><span>{PL[o["dia"]]} · {o["hora"]}</span></a>' for o in outros)
        rel+='<a href="/"><strong>Calendário Weatherlight</strong><span>Todos os eventos desta semana</span></a>'
        img=f'<img src="/img/{s["arte"]}-g.jpg" alt="" width="180" height="240">' if s.get('arte') else ''
        page=f'''<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(s['titulo'])} · {html.escape(s['nome_jogo'])} em Évora | Weatherlight</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{BASE}/{s['slug']}/">
{fonts}
<script type="application/ld+json">{json.dumps(ld,ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(faq,ensure_ascii=False)}</script>
{style}
<style>*,*::before,*::after{{box-sizing:border-box}}body{{margin:0}}img{{max-width:100%}}
.crumbs{{font-size:.85rem;color:var(--hd-soft)}}.crumbs a{{color:var(--hd-ink)}}
.facts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:.6rem;margin:0;padding:0;list-style:none}}
.facts li{{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:.7rem .9rem;display:grid;gap:.1rem;min-width:0}}
.facts small{{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}.facts strong{{font-weight:500}}
.intro{{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:1.5rem;align-items:start}}
.intro img{{width:180px;border-radius:8px;aspect-ratio:3/4;object-fit:cover}}
.box{{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:1.1rem 1.25rem;min-width:0}}
.box h2,.sec h2{{font:500 1.15rem/1.2 var(--display);text-transform:uppercase;letter-spacing:.04em;margin:0 0 .6rem}}
.pre{{white-space:pre-line;margin:0}}.m{{margin:0}}.nota{{margin:0;color:var(--muted)}}
.dates{{list-style:none;margin:0;padding:0;display:grid;gap:.4rem}}
.dates li{{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;border-top:1px dashed var(--line);padding-top:.4rem}}.dates li:first-child{{border-top:0;padding-top:0}}
.faq dl{{margin:0}}.faq dt{{font-weight:500;margin-top:.7rem}}.faq dt:first-child{{margin-top:0}}.faq dd{{margin:.2rem 0 0}}
.rel{{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:.6rem}}
.rel a{{display:grid;gap:.1rem;text-decoration:none;color:var(--ink);background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:.7rem .9rem}}
.rel a:hover{{border-color:var(--sea-2)}}.rel strong{{font-weight:500}}.rel span{{font-size:.9rem;color:var(--muted)}}
main a:not(.rel a),footer a{{color:var(--sea-2)}}
@media (max-width:560px){{.intro{{grid-template-columns:1fr}}.intro img{{width:150px}}}}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <span class="crumbs"><a href="/">Calendário Weatherlight</a> › {html.escape(s['nome_jogo'])}</span>
    <h1>{html.escape(s['titulo'])}</h1>
    <p class="sub">{html.escape(s['nome_jogo'])} em Évora · {quando}</p>
  </div>
</header>
<main>
  <div class="wrap">
    <ul class="facts">
      <li><small>Quando</small><strong>{quando}</strong></li>
      <li><small>Preço</small><strong>{pr}</strong></li>
      {f'<li><small>Formato</small><strong>{html.escape(fmt)}</strong></li>' if fmt else ''}
      <li><small>Onde</small><strong><a href="{MAPS}">Weatherlight, Évora</a></strong></li>
    </ul>
    {f'<p class="nota">{html.escape(s["nota"])}</p>' if s.get('nota') else ''}
    <section class="intro"><div class="box"><h2>Como funciona</h2><p class="pre">{html.escape(txt or "Detalhes no nosso Discord.")}</p></div>{img}</section>
    <section class="box"><h2>Esta semana</h2>{prox}</section>
    <section class="box faq"><h2>Perguntas frequentes</h2><dl>{''.join(f'<dt>{html.escape(q)}</dt><dd>{html.escape(a)}</dd>' for q,a in perg)}</dl>
      <p class="m" style="margin-top:.9rem">Mais dúvidas? Vê a <a href="{CA}">Central de Ajuda</a> e o <a href="{GL}">Glossário</a>, ou junta-te à nossa comunidade no <a href="{DISCORD}">Discord</a>.</p></section>
    <section class="sec"><h2>Mais eventos</h2><div class="rel">{rel}</div></section>
  </div>
</main>
<footer><div class="wrap"><p class="close">Se nenhum dos eventos é o que procuras, temos uma <a href="{MAPS}">loja inteira ao teu dispor</a> — vem visitar-nos ☁️</p></div></footer>
</body>
</html>
'''
        page=re.sub(r'<a href="(https?://[^"]+)"(?![^>]*target=)',r'<a href="\1" target="_blank" rel="noopener"',page)
        pasta=os.path.join(RAIZ,s['slug']); os.makedirs(pasta,exist_ok=True)
        open(os.path.join(pasta,'index.html'),'w').write(page)
        urls.append(f"{BASE}/{s['slug']}/")
    open(os.path.join(RAIZ,'sitemap.xml'),'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+
        ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls)+'</urlset>\n')
    open(os.path.join(RAIZ,'robots.txt'),'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n')
    return len(SER)
