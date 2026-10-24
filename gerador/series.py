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

# Perguntas da Central de Ajuda (texto da própria Central, ligeiramente encurtado)
CENTRAL={
 "primeira":("Nunca participei num evento. Posso aparecer na mesma?","Claro! Muitas pessoas participam nos nossos eventos pela primeira vez e não é preciso ter um deck perfeito ou muita experiência para desfrutar do hobby. Cada evento é uma oportunidade para aprender, conhecer a comunidade e passar um bom momento à volta da mesa."),
 "sozinho":("Posso aparecer sozinho?","Claro! Muitas pessoas vieram ao seu primeiro evento sem conhecer ninguém. A nossa comunidade está habituada a receber novos jogadores e teremos todo o gosto em ajudar-te a dar os primeiros passos. O mais difícil costuma ser entrar pela porta. Depois disso, o hobby faz o resto."),
 "iniciante":("Posso participar mesmo sendo iniciante?","Claro. Os encontros semanais são pensados precisamente para jogar, aprender e divertir-se. Se for a tua primeira experiência, não hesites em pedir ajuda: a comunidade costuma ser bastante acolhedora."),
 "competitivos":("Os eventos são muito competitivos?","Existem eventos para diferentes tipos de jogadores: alguns mais competitivos, outros pensados para experimentar estratégias num ambiente descontraído. Para nós, cada evento é mais do que uma competição."),
 "sleeves_ilustradas":("Posso usar Sleeves ilustradas?","Sim. Desde que todas as sleeves do deck sejam iguais, estejam em bom estado e cumpram as regras do jogo. Muitos jogadores protegem-nas com Outer Sleeves para reduzir o desgaste."),
 "sleeves_ygo":("Que Sleeves preciso para Yu-Gi-Oh!?","As cartas de Yu-Gi-Oh! são mais pequenas do que as da maioria dos jogos, por isso precisas de sleeves Japanese Size. Se tiveres dúvidas, teremos todo o gosto em ajudar-te a escolher."),
}
DIA_ISO={"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4,"Saturday":5,"Sunday":6}
DIA_NOME=["Segunda-feira","Terça-feira","Quarta-feira","Quinta-feira","Sexta-feira","Sábado","Domingo"]
MESES=["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]

# Pergunta "Como me posso inscrever?" por jogo (confirmado pela equipa a 24/10/2026: contas obrigatórias; pagamento no check-in ao balcão)
def _app(nome,url,app=True): return (f'Inscreves-te na <a href="{url}">{nome}</a>: precisas de ter '+('a app e uma conta, que são obrigatórias' if app else 'uma conta, que é obrigatória')+' para participar. '
                            'É lá também que acompanhas as rondas e os resultados.')
APPS={
 "op":_app("Bandai TCG+","https://www.bandai-tcg-plus.com/"),"digi":_app("Bandai TCG+","https://www.bandai-tcg-plus.com/"),
 "gundam":_app("Bandai TCG+","https://www.bandai-tcg-plus.com/"),
 "cyber":_app("Melee","https://melee.gg/",False),
 "rift":_app("Riftbound Gaming Network","https://playriftbound.com/",False),
 "ygo":"Precisas de ter a app Neuron e um KONAMI ID, que são obrigatórios para participar. Se ainda não tens, não há problema: criamos contigo aqui na loja.",
 "magic":'Precisas de ter a app Magic: The Gathering Companion e uma conta Wizards, que são obrigatórias para participar. Entras no evento com o código que partilhamos no <a href="/">Calendário Weatherlight</a>.',
 "poke":"Precisas de ter um Player ID da Pokémon, que é obrigatório para participar. Se ainda não tens, fazemos contigo aqui na loja. Recomendamos também a app Pokémon Access, para teres os teus dados de jogador sempre à mão.",
}
PAGA=" O pagamento da inscrição é feito no check-in, no nosso balcão, com um de nós."
GRATIS=" Este evento é gratuito: não há nada a pagar, basta fazeres o check-in no nosso balcão."

def proximas(s,S,n=4):
    """Próximas n datas: as desta semana vêm do calendário; as seguintes são previstas pelo horário fixo."""
    import datetime as dt
    hoje=dt.date.today(); isos=[dt.date.fromisoformat(d['iso']) for d in S['dias']]
    ini,fim=(min(isos),max(isos)) if isos else (hoje,hoje)
    reais={d['iso']:(d,e) for d in S['dias'] for e in d['eventos'] if e['jogo']==s['jogo'] and (e['evento'] in s['eventos'] or e.get('modelo')==s['modelo'])}
    out=[]; x=hoje+dt.timedelta((DIA_ISO[s['dia']]-hoje.weekday())%7)
    while len(out)<n:
        iso=x.isoformat()
        if iso in reais:
            d,e=reais[iso]; out.append((f"{d['dia']}, {d['data']}",e['hora'],float(e['preco']),e.get('esgotado',False),True))
        elif not (ini<=x<=fim):
            out.append((f"{DIA_NOME[x.weekday()]}, {x.day} de {MESES[x.month-1]}",s['hora'],float(s['preco']),False,False))
        x+=dt.timedelta(7)
    return out

BASE_DB=json.load(open(os.path.join(AQUI,'base.json')))
def limpar(k): return re.sub(r"\s*\((Semanal|Fim de semana|Magic|One Piece|Digimon|Pokémon)\)$","",k)
def preco_db(txt):
    m=re.search(r"Pre[çc]o[^:\n]*:[ \t]*\n?-?[ \t]*([^\n]+)",txt or '')
    if not m: return None
    v=m.group(1).split(' - ')[0].strip().rstrip('.')
    v=re.sub(r'\s*por Jogador$','',v,flags=re.I)
    return 'Gratuito' if v.lower().startswith('free') else v

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
        art_='o' if s['titulo'].split()[0] in ('Modern','Duelist','Pilot') else 'a'
        if float(s['preco'])==0:
            custo=f"A {s['titulo']} é gratuita!"+(" "+re.sub(r"\s+"," ",re.search(r"Prémios:\s*\n(.+)",txt).group(1)).strip() if txt and re.search(r"Prémios:\s*\n(.+)",txt) else "")
        else:
            custo=f"A inscrição custa {pr}."+(" Além dos prémios, todos os participantes levam para casa: "+"; ".join(part)+"." if part else "")
        quando_html=(f"{PL[s['dia']]} às {s['hora']}, aqui na <a href=\"{MAPS}\">Weatherlight</a>, em Évora. "
                     "Em semanas de feriados ou férias o horário pode mudar: confirma sempre no <a href=\"/\">Calendário Weatherlight</a>.")
        perg=[("Quando e onde é?", re.sub(r"<[^>]+>","",quando_html), quando_html)]
        if fmt: perg.append(("Que formato se joga?", fmt+". Se algum termo for novo para ti, o Glossário explica tudo.", html.escape(fmt)+f". Se algum termo for novo para ti, o <a href=\"{GL}\">Glossário</a> explica tudo."))
        if s['jogo'] in APPS:
            ah=APPS[s['jogo']]+(GRATIS if float(s['preco'])==0 else PAGA); perg.append(("Como me posso inscrever?", re.sub(r"<[^>]+>","",ah), ah))
        perg+=[(q,a,html.escape(a)) for q,a in (CENTRAL[k] for k in s.get('faq',[]) if k in CENTRAL)]
        perg+=[(q['pergunta'],q['resposta'],html.escape(q['resposta'])) for q in s.get('perguntas',[])]
        perg.append(("Como sei quando há eventos?","Anunciamos todos os eventos no nosso Instagram e no Calendário Weatherlight, atualizado todas as semanas. Segue-nos para não perderes nenhum.",
                     'Anunciamos todos os eventos no nosso <a href="https://www.instagram.com/weatherlightgames/">Instagram</a> e no <a href="/">Calendário Weatherlight</a>, atualizado todas as semanas. Segue-nos para não perderes nenhum.'))
        faq={"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a,_ in perg]}
        pd=proximas(s,S)
        prox='<ul class="dates">'+''.join(f'<li><span>{l}</span><span>{h} · {preco_txt(p)}{" · Esgotado" if esg else ""}{"" if conf else " · previsto"}</span></li>' for l,h,p,esg,conf in pd)+'</ul>'
        prox+='<p class="m small">As datas marcadas como previstas seguem o horário habitual. Férias e feriados são anunciados no <a href="/">Calendário Weatherlight</a>.</p>'
        outros=[o for o in SER if o['jogo']==s['jogo'] and o is not s]
        rel=''.join(f'<a class="card" href="/{o["slug"]}/"><strong>{html.escape(o["titulo"])}</strong><span>{PL[o["dia"]]} · {o["hora"]} · {preco_txt(float(o["preco"]))}</span><em>Ver página →</em></a>' for o in outros)
        cobertos={re.sub(r"\s*\(.*\)$","",n) for o in SER if o['jogo']==s['jogo'] for n in o['eventos']+[o['modelo']]}
        for k in BASE_DB.get(s['jogo'],[]):
            nome=limpar(k)
            if k in [o['modelo'] for o in SER] or re.sub(r"\s*\(.*\)$","",k) in cobertos: continue
            t2=DET.get(k)
            if not t2: continue
            info=" · ".join(x for x in [formato(t2), preco_db(t2)] if x)
            rel+=(f'<details class="card ot"><summary><strong>{html.escape(nome)}</strong><span>{html.escape(info)}</span><em>Ver detalhes</em></summary>'
                  f'<p class="pre">{html.escape(t2)}</p><p class="m small">Datas anunciadas no <a href="/">Calendário Weatherlight</a> e no nosso Instagram.</p></details>')
        rel+='<a class="card" href="/"><strong>Calendário Weatherlight</strong><span>Todos os eventos desta semana</span><em>Ver calendário →</em></a>'
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
<style>:root{{--ans:#4a7c88}}@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--ans:#9fc9d3}}}}:root[data-theme="dark"]{{--ans:#9fc9d3}}
*,*::before,*::after{{box-sizing:border-box}}body{{margin:0}}img{{max-width:100%}}
.crumbs{{font-size:.85rem;color:var(--hd-soft)}}.crumbs a{{color:var(--hd-ink)}}
.facts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:.6rem;margin:0;padding:0;list-style:none}}
.facts li{{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:.7rem .9rem;display:grid;gap:.1rem;min-width:0}}
.facts small{{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}.facts strong{{font-weight:500}}
.intro{{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:1.5rem;align-items:start}}
.intro img{{width:180px;border-radius:8px;aspect-ratio:3/4;object-fit:cover}}
.box{{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:1.1rem 1.25rem;min-width:0}}
.box h2,.sec h2{{font:500 1.15rem/1.2 var(--display);text-transform:uppercase;letter-spacing:.04em;margin:0 0 .6rem}}
.pre{{white-space:pre-line;margin:0}}.m{{margin:0}}.small{{font-size:.88rem;color:var(--muted);margin-top:1.1rem}}.nota{{margin:0;color:var(--muted)}}
.dates{{list-style:none;margin:0;padding:0;display:grid;gap:.4rem}}
.dates li{{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;border-top:1px dashed var(--line);padding-top:.4rem}}.dates li:first-child{{border-top:0;padding-top:0}}
.faq dl{{margin:0}}.faq dt{{font-weight:500;margin-top:.7rem}}.faq dt:first-child{{margin-top:0}}.faq dd{{margin:.2rem 0 0;color:var(--ans);font-size:.94rem;line-height:1.55}}.faq dd a{{color:inherit}}
.rel{{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:.6rem}}
.rel{{align-items:start}}.card{{display:grid;gap:.15rem;text-decoration:none;color:var(--ink);background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:.75rem .9rem}}.card em{{font-style:normal;font-size:.88rem;color:var(--sea-2);margin-top:.2rem}}.ot summary{{display:grid;gap:.15rem;cursor:pointer;list-style:none}}.ot summary::-webkit-details-marker{{display:none}}.ot[open]{{grid-column:1/-1}}.ot[open] em{{display:none}}.ot .pre{{margin-top:.7rem;font-size:.97rem}}
.card:hover{{border-color:var(--sea-2)}}.card strong{{font-weight:500}}.card span{{font-size:.9rem;color:var(--muted)}}
main a:not(.card),footer a{{color:var(--sea-2)}}
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
    <section class="box"><h2>Próximas datas</h2>{prox}</section>
    <section class="box faq"><h2>Perguntas frequentes</h2><dl>{''.join(f'<dt>{html.escape(q)}</dt><dd>{ah}</dd>' for q,a,ah in perg)}</dl>
      <p class="m" style="margin-top:.9rem">Estas e outras respostas estão na <a href="{CA}">Central de Ajuda</a>. Vê também o <a href="{GL}">Glossário</a>, ou junta-te à nossa comunidade no <a href="{DISCORD}">Discord</a>.</p></section>
    <section class="sec"><h2>Outros eventos de {html.escape(s["nome_jogo"])}</h2><div class="rel">{rel}</div></section>
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
