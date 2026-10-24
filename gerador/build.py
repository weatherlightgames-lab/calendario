"""Gera ../index.html (Calendário Weatherlight) a partir de semana.json, details.json e tpl.html.
Uso: python3 build.py   (a partir da pasta gerador/)"""
import json, html, re, os
AQUI=os.path.dirname(os.path.abspath(__file__)); RAIZ=os.path.dirname(AQUI)
S=json.load(open(os.path.join(AQUI,'semana.json')))
DET=json.load(open(os.path.join(AQUI,'details.json')))
SER=json.load(open(os.path.join(AQUI,'series.json')))
# links/códigos que chegaram antes da semana ser publicada: {"AAAA-MM-DD": {"Evento": {"inscricao": …, "companion": …}}}
PEND=json.load(open(os.path.join(AQUI,'pendentes.json'))) if os.path.exists(os.path.join(AQUI,'pendentes.json')) else {}
for _d in S['dias']:
    for _e in _d['eventos']:
        for _k,_v in PEND.get(_d['iso'],{}).get(_e['evento'],{}).items(): _e.setdefault(_k,_v)
def serie_de(e):
    for s in SER:
        if s['jogo']==e['jogo'] and (e['evento'] in s['eventos'] or e.get('modelo')==s['modelo']): return s
    return None
BASE='https://eventos.weatherlightgames.pt/'
DISCORD='https://discord.gg/HTCZeJZuVk'
ADDR={"@type":"Place","name":"Weatherlight Games & Collectibles","address":{"@type":"PostalAddress","streetAddress":"Rua Frei José Maria Évora, Nº2","postalCode":"7005-495","addressLocality":"Évora","addressCountry":"PT"}}
ORG={"@type":"Organization","name":"Weatherlight Games & Collectibles","url":"https://www.weatherlightgames.pt",
     "sameAs":["https://www.instagram.com/weatherlightgames/","https://www.facebook.com/weatherlightgames","https://www.tiktok.com/@weatherlightcollectibles",DISCORD]}
JOGOS={"magic":"Magic","poke":"Pokémon","op":"One Piece","ygo":"Yu-Gi-Oh!","rift":"Riftbound","digi":"Digimon","gundam":"Gundam","cyber":"Cyberpunk","lorcana":"Lorcana","swu":"Star Wars"}

def modelo(e):
    """Texto de detalhes: 'modelo' explícito, senão o nome do evento, senão um título único 'Evento (…)'."""
    for k in [e.get('modelo'), e['evento']]:
        if k and k in DET: return DET[k]
    c=[k for k in DET if k.startswith(e['evento']+' (')]
    return DET[c[0]] if len(c)==1 else None

def det(txt,s=None,cal=''):
    """Devolve (botão, painel). O painel abre por baixo da fila de botões (CSS :has)."""
    if txt:
        return ('<details class="det d1"><summary>Ver detalhes</summary></details>',
                '<div class="txt p1">'+html.escape(txt)+
                '<span class="more">Algum termo que não conheces? Vê o <a href="https://www.weatherlightgames.pt/page/glossario">Glossário</a> '
                'ou a <a href="https://www.weatherlightgames.pt/page/central-de-ajuda-weatherlight">Central de Ajuda</a>.</span>'+
                '<span class="lks">'+(f'<a class="pg" href="/{s["slug"]}/">Página do evento →</a>' if s else '')+cal+'</span></div>')
    return (f'<p class="det none">Detalhes no nosso <a href="{DISCORD}">Discord</a>.</p>','')

# Inscrição: link da aplicação do torneio (semana.json "inscricao") e código Companion do Magic ("companion")
PLAT=[("melee.gg","Melee"),("bandai-tcg-plus","Bandai TCG+"),("playriftbound","Riftbound Gaming Network"),("riftbound","Riftbound Gaming Network"),
      ("neuron","Neuron"),("konami","Neuron"),("companion.wizards","Companion"),("eventlink","EventLink"),
      ("limitlesstcg","Limitless"),("pokemon","Pokémon"),("digimoncard","Bandai TCG+")]
def plataforma(u):
    for k,v in PLAT:
        if k in u: return v
    return None
def inscricao(e):
    h=""
    u=e.get('inscricao')
    if u and not e.get('esgotado'):
        pl=plataforma(u)
        h+=(f'<a class="insc" href="{html.escape(u)}" target="_blank" rel="noopener"'
            f'{f" title=\"Inscreve-te na {pl}\"" if pl else ""}>Inscreve-te{f" · {pl}" if pl else ""}<span aria-hidden="true">↗</span></a>')
    pn=""
    c=e.get('companion')
    if c and not e.get('esgotado'):
        h+='<details class="det d2"><summary>Código Companion</summary></details>'
        pn=('<div class="txt p2 cmp">'f'<span class="cl"><span class="code">{html.escape(c)}</span><button type="button" class="cp" data-code="{html.escape(c)}">Copiar</button></span>'
            'Na app <strong>Magic: The Gathering Companion</strong>, toca em <em>Enter Event Code</em> e cola o código.</div>')
    return h,pn

# Adicionar ao calendário: link Google Calendar + ficheiro .ics (Apple/Outlook) em /ics/
from datetime import datetime, timedelta, timezone
import urllib.parse, shutil
ICS=os.path.join(RAIZ,'ics'); shutil.rmtree(ICS,ignore_errors=True); os.makedirs(ICS)
MORADA="Weatherlight Games & Collectibles, Rua Frei José Maria Évora, Nº2, 7005-495 Évora"
def calendario(d,e,s):
    h,m=map(int,e['hora'].split(':')); sg=-1 if d['fuso'].startswith('-') else 1
    off=timedelta(hours=int(d['fuso'][1:3]),minutes=int(d['fuso'][4:6]))*sg
    ini=datetime(*map(int,d['iso'].split('-')),h,m,tzinfo=timezone(off)).astimezone(timezone.utc); fim=ini+timedelta(hours=3)
    f=lambda x:x.strftime('%Y%m%dT%H%M%SZ')
    tit=f"{e['evento']} · {e['nome_jogo']} (Weatherlight)"
    desc=[]
    if e.get('inscricao'): desc.append("Inscrição: "+e['inscricao'])
    if e.get('companion'): desc.append("Código Companion: "+e['companion'])
    desc.append("Detalhes: "+BASE+(s['slug']+'/' if s else ''))
    g=('https://calendar.google.com/calendar/render?action=TEMPLATE&'+urllib.parse.urlencode(
        {'text':tit,'dates':f(ini)+'/'+f(fim),'details':"\n".join(desc),'location':MORADA},quote_via=urllib.parse.quote))
    nome=re.sub(r'[^a-z0-9]+','-',(d['iso']+'-'+e['jogo']+'-'+e['evento']).lower()).strip('-')+'.ics'
    esc=lambda x:x.replace('\\','\\\\').replace(';','\\;').replace(',','\\,').replace('\n','\\n')
    ics="\r\n".join(["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Weatherlight//Calendario//PT","CALSCALE:GREGORIAN","METHOD:PUBLISH",
        "BEGIN:VEVENT",f"UID:{nome[:-4]}@eventos.weatherlightgames.pt",f"DTSTAMP:{f(datetime.now(timezone.utc))}",
        f"DTSTART:{f(ini)}",f"DTEND:{f(fim)}",f"SUMMARY:{esc(tit)}",f"DESCRIPTION:{esc(chr(10).join(desc))}",
        f"LOCATION:{esc(MORADA)}",f"URL:{BASE+(s['slug']+'/' if s else '')}","END:VEVENT","END:VCALENDAR",""])
    open(os.path.join(ICS,nome),'w',newline='').write(ics)
    return (f'<span class="cal">📅 Adicionar ao calendário: <a href="{html.escape(g)}">Google</a> · '
            f'<a href="/ics/{nome}" download>Apple / Outlook</a></span>')

ld=[]; rows=""; usados=[]; sem_modelo=[]
def item(d,e,quando=None):
    """Um evento (li) + o seu JSON-LD. quando = rótulo da data (eventos futuros)."""
    g=e['jogo']; usados.append(g); txt=modelo(e); s=serie_de(e); art=e.get('arte'); preco=float(e['preco'])
    if not txt: sem_modelo.append(f"{d['dia']} {e['hora']} {e['evento']}")
    ld.append({"@context":"https://schema.org","@type":"Event","name":f"{e['nome_jogo']} - {e['evento']}",
      "startDate":f"{d['iso']}T{e['hora']}:00{d['fuso']}","eventStatus":"https://schema.org/EventScheduled",
      "eventAttendanceMode":"https://schema.org/OfflineEventAttendanceMode","location":ADDR,"organizer":ORG,
      **({"image":BASE+f"img/{art}-g.jpg"} if art else {}),
      "description":re.sub(r"\s+"," ",txt).strip() if txt else f"{e['evento']} de {e['nome_jogo']} na Weatherlight, em Évora.",
      "offers":{"@type":"Offer","price":f"{preco:.2f}","priceCurrency":"EUR","url":e.get('inscricao') or BASE,
                "availability":"https://schema.org/"+("SoldOut" if e.get('esgotado') else "InStock")}})
    b1,p1=det(txt,s,calendario(d,e,s)); b2,p2=inscricao(e)
    p="Gratuito" if preco==0 else f"{preco:.2f}".replace('.',',')+" €"
    sp='<span class="sold">Esgotado</span>' if e.get('esgotado') else ''
    th=f'<img class="thumb" src="/img/{art}-v.jpg" alt="" width="90" height="120" loading="lazy">' if art else '<span class="thumb"></span>'
    return (f'<li class="ev" data-game="{g}">{th}<time class="t" datetime="{d["iso"]}T{e["hora"]}">{quando or ''}{e["hora"]}</time>'
            f'<div class="what"><span class="chip c-{g}">{html.escape(e["nome_jogo"])}</span>{(f'<a class="nm" href="/{s["slug"]}/"><strong>{html.escape(e["evento"])}</strong></a>' if s else f'<strong>{html.escape(e["evento"])}</strong>')}{sp}</div>'
            f'<span class="price{" free" if preco==0 else ""}">{p}</span><div class="acts">{b1}{b2}</div>{f'<div class="det pns">{p1}{p2}</div>' if p1 or p2 else ''}</li>')

for d in S['dias']:
    items="".join(item(d,e) for e in d['eventos'])
    rows+=f'<section class="day"><h2><span>{d["dia"]}</span> <small>{d["data"]}</small></h2><ol class="evs">{items}</ol></section>'

# Eventos que não podes perder: futuros.json (eventos especiais anunciados com antecedência).
# Aparecem enquanto a data é posterior à semana publicada e ainda não passou; depois entram em semana.json.
from zoneinfo import ZoneInfo
from datetime import date
FUT_P=os.path.join(AQUI,'futuros.json'); FUT=json.load(open(FUT_P)) if os.path.exists(FUT_P) else []
ULT=max(d['iso'] for d in S['dias']); HOJE=date.today().isoformat()
DS=["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]
fit=""
for e in sorted(FUT,key=lambda x:(x['iso'],x['hora'])):
    if e['iso']<=ULT or e['iso']<HOJE: continue
    y,mo,da=map(int,e['iso'].split('-')); h,mi=map(int,e['hora'].split(':'))
    fz=datetime(y,mo,da,h,mi,tzinfo=ZoneInfo('Europe/Lisbon')).strftime('%z'); fz=fz[:3]+':'+fz[3:]
    dd={'iso':e['iso'],'fuso':fz,'dia':DS[date(y,mo,da).weekday()]}
    fit+=item(dd,e,f'<span class="dt">{dd["dia"]} {da:02d}/{mo:02d}</span>')
if fit: rows+=f'<section class="day fut"><h2><span>Eventos que não podes perder</span> <small>próximas semanas</small></h2><ol class="evs">{fit}</ol></section>'

DIA_PT={"Monday":"Segunda","Tuesday":"Terça","Wednesday":"Quarta","Thursday":"Quinta","Friday":"Sexta","Saturday":"Sábado","Sunday":"Domingo"}
ORD=list(DIA_PT)
reg=""
for k,v in JOGOS.items():
    ss=[s for s in SER if s['jogo']==k]
    if not ss: continue
    ss.sort(key=lambda s:(ORD.index(s['dia']),s['hora']))
    reg+=f'<div class="rg"><span class="chip c-{k}">{html.escape(ss[0]["nome_jogo"])}</span><ul>'+''.join(
        f'<li><a href="/{s["slug"]}/">{html.escape(s["titulo"])}</a><span>{DIA_PT[s["dia"]]} · {s["hora"]}</span></li>' for s in ss)+'</ul></div>'
regulares=f'<section class="regs"><h2>Eventos regulares</h2><p class="regs-sub">Todas as semanas, à mesma hora. Em feriados e férias, confirma no calendário acima.</p><div class="rgs">{reg}</div></section>'
chips="".join(f'<button type="button" class="f" data-g="{k}" aria-pressed="false">{v}</button>' for k,v in JOGOS.items() if k in usados)
lede="\n    ".join(f'<p class="lede">{html.escape(x)}</p>' for x in S['introducao'])
dest="\n        "+"\n        ".join(f'<li>{html.escape(x)}</li>' for x in S['destaques'])+"\n      "
t=open(os.path.join(AQUI,'tpl.html')).read()
out=(t.replace('%%LD%%',json.dumps(ld,ensure_ascii=False,indent=1)).replace('%%DAYS%%',rows).replace('%%CHIPS%%',chips)
      .replace('%%SEMANA%%',html.escape(S['semana'])).replace('%%LEDE%%',lede).replace('%%DESTAQUES%%',dest).replace('%%REGULARES%%',regulares))
if not S['destaques']: out=re.sub(r'\s*<aside class="weekend">.*?</aside>','',out,flags=re.S)
out=re.sub(r'<a href="(https?://[^"]+)"(?![^>]*target=)',r'<a href="\1" target="_blank" rel="noopener"',out)
i=out.index('<title>'); j=out.index('</style>')+len('</style>')
site=('<!doctype html>\n<html lang="pt">\n<head>\n<meta charset="utf-8">\n'
      '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'+out[i:j]+
      '\n<style>*,*::before,*::after{box-sizing:border-box}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
      '</head>\n<body>\n'+out[j:]+'\n</body>\n</html>\n')
open(os.path.join(RAIZ,'index.html'),'w').write(site)
import sys; sys.path.insert(0,AQUI); import series
print(f"{len(ld)} eventos gerados; {series.gerar(t,SER,DET,S)} páginas de eventos regulares.")
if sem_modelo: print("Sem modelo na base de dados:", "; ".join(sem_modelo))
