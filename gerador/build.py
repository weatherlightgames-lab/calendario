import json, html, re
DET=json.load(open('details.json'))
ADDR={"@type":"Place","name":"Weatherlight Games & Collectibles","address":{"@type":"PostalAddress","streetAddress":"Rua Frei José Maria Évora, Nº2","postalCode":"7005-495","addressLocality":"Évora","addressCountry":"PT"}}
ORG={"@type":"Organization","name":"Weatherlight Games & Collectibles","url":"https://www.weatherlightgames.pt","sameAs":["https://www.instagram.com/weatherlightgames/","https://www.facebook.com/weatherlightgames","https://www.tiktok.com/@weatherlightcollectibles","https://discord.gg/HTCZeJZuVk"]}
IMG="https://cdn-shopkit.com/usercontent/weatherlightgames/media/images/46375d5-190356-weatherlight-calendario-semanal.jpg"
# (dia, data, iso, fuso, eventos) — eventos: hora, jogo, nome do jogo, evento, preço, esgotado
days=[("Quarta-feira","21 de outubro","2026-10-21","+01:00",[
 ("16:00","magic","Magic: The Gathering","Commander Afternoon",0,False),
 ("20:00","magic","Magic: The Gathering","Modern",6,False),
 ("20:00","ygo","Yu-Gi-Oh!","Duelist Lounge",5,False),
 ("20:30","op","One Piece Card Game","Pirate Party",5.5,False)]),
 ("Sexta-feira","23 de outubro","2026-10-23","+01:00",[
 ("20:00","magic","Magic: The Gathering","Standard Store Championship",13,False),
 ("20:00","rift","Riftbound: League of Legends TCG","Nexus Night",6.5,False),
 ("20:00","digi","Digimon Card Game","Tamer Party",5.5,False),
 ("21:00","gundam","Gundam Card Game","Pilot Lounge",5.5,False)]),
 ("Sábado","24 de outubro","2026-10-24","+01:00",[
 ("15:00","op","One Piece Card Game","Store Championship",20,True),
 ("15:00","cyber","Cyberpunk TCG","Night City Brawl",6.5,False),
 ("18:00","gundam","Gundam Card Game","Pilot Party",5.5,False)]),
 ("Domingo","25 de outubro","2026-10-25","+00:00",[
 ("15:00","poke","Pokémon TCG","Prerelease Delta Reign",32,False),
 ("15:00","gundam","Gundam Assemble","Demo Event #1 - Learn to Play",0,False),
 ("15:00","rift","Riftbound: League of Legends TCG","Nexus Afternoon",6.5,False)])]
games={"magic":"Magic","poke":"Pokémon","op":"One Piece","ygo":"Yu-Gi-Oh!","rift":"Riftbound","digi":"Digimon","gundam":"Gundam","cyber":"Cyberpunk"}
# modelo da base de dados a usar quando difere do nome no cartaz
# One Piece: Pirate Lounge e Pirate Party são Standard; Extra Regulation só quando o calendário avisa
ALIAS={}
# arte de cada evento, recortada dos cartazes (img/<slug>.jpg e img/<slug>-sq.jpg)
ARTE={('2026-10-21','Commander Afternoon'):'commander',('2026-10-21','Modern'):'modern',('2026-10-21','Duelist Lounge'):'duelist',('2026-10-21','Pirate Party'):'pirate',
 ('2026-10-23','Standard Store Championship'):'mtg-sc',('2026-10-23','Nexus Night'):'nexus-night',('2026-10-23','Tamer Party'):'tamer',('2026-10-23','Pilot Lounge'):'pilot-lounge',
 ('2026-10-24','Store Championship'):'op-sc',('2026-10-24','Night City Brawl'):'nightcity',('2026-10-24','Pilot Party'):'pilot-party',
 ('2026-10-25','Prerelease Delta Reign'):'delta',('2026-10-25','Demo Event #1 - Learn to Play'):'assemble',('2026-10-25','Nexus Afternoon'):'nexus-afternoon'}
BASE='https://eventos.weatherlightgames.pt/'
MODELO={}
def det(n):
    if n in DET:
        return f'<details class="det"><summary>Ver detalhes</summary><div class="txt">{html.escape(DET[n])}<span class="more">Algum termo que não conheces? Vê o <a href="https://www.weatherlightgames.pt/page/glossario">Glossário</a> ou a <a href="https://www.weatherlightgames.pt/page/central-de-ajuda-weatherlight">Central de Ajuda</a>.</span></div></details>'
    return '<p class="det none">Detalhes no nosso <a href="https://discord.gg/HTCZeJZuVk">Discord</a>.</p>'
ld=[]
rows=""
for dname,dlabel,iso,tz,evs in days:
    items=""
    for t,g,game,name,price,sold in evs:
        k=MODELO.get((iso,name),ALIAS.get(name,name))
        art=ARTE.get((iso,name))
        ld.append({"@context":"https://schema.org","@type":"Event","name":f"{game} - {name}","startDate":f"{iso}T{t}:00{tz}",
          "eventStatus":"https://schema.org/EventScheduled","eventAttendanceMode":"https://schema.org/OfflineEventAttendanceMode",
          "location":ADDR,"organizer":ORG,"image":(BASE+f"img/{art}.jpg" if art else IMG),"description":(re.sub(r"\s+"," ",DET[k]).strip() if k in DET else f"{name} de {game} na Weatherlight, em Évora."),
          "offers":{"@type":"Offer","price":f"{price:.2f}","priceCurrency":"EUR","availability":"https://schema.org/"+("SoldOut" if sold else "InStock"),"url":"https://eventos.weatherlightgames.pt/"}})
        p="Gratuito" if price==0 else f"{price:.2f}".replace('.',',')+" €"
        sp='<span class="sold">Esgotado</span>' if sold else ''
        thumb=f'<img class="thumb" src="img/{art}-v.jpg" alt="" width="90" height="120" loading="lazy">' if art else '<span class="thumb"></span>'
        bg=''
        items+=f'''<li class="ev" data-game="{g}"{bg}>{thumb}<time class="t" datetime="{iso}T{t}">{t}</time><div class="what"><span class="chip c-{g}">{html.escape(game)}</span><strong>{html.escape(name)}</strong>{sp}</div><span class="price{' free' if price==0 else ''}">{p}</span>{det(k)}</li>'''
    rows+=f'''<section class="day"><h2><span>{dname}</span> <small>{dlabel}</small></h2><ol class="evs">{items}</ol></section>'''
chips="".join(f'<button type="button" class="f" data-g="{k}" aria-pressed="false">{v}</button>' for k,v in games.items())
tpl=open('tpl.html').read()
out=tpl.replace('%%LD%%',json.dumps(ld,ensure_ascii=False,indent=1)).replace('%%DAYS%%',rows).replace('%%CHIPS%%',chips)
open('eventos-weatherlight.html','w').write(out)
print(len(ld))
