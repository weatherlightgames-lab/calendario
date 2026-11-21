"""Bot de novidades da Weatherlight para o Discord.

De hora a hora (GitHub Actions) lê o sitemap da loja, descobre produtos que ainda não tinha visto
e publica-os no canal ✨│novidades-wl através de um webhook (segredo DISCORD_WEBHOOK).

- Primeira execução (sem estado): regista todos os produtos existentes e não publica nada.
- Um produto já visto nunca é anunciado outra vez (mesmo que seja escondido e volte).
- Vários produtos novos de uma vez: até 10 por mensagem (limite do Discord).

Os produtos anunciados também entram na página "Acabou de chegar" (novidades/, ver bot/pagina.py).

Uso: python3 bot/novidades.py <ficheiro de estado> [--teste URL ...] [--adicionar URL ...]
  --teste      publica esses produtos no Discord (e na página) já
  --adicionar  junta esses produtos só à página, sem os publicar no Discord
"""
import gzip, json, os, re, sys, time, urllib.error, urllib.request, xml.etree.ElementTree as ET
from html import unescape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pagina

SITE = "https://www.weatherlightgames.pt"
COR = 0x46677A
UA = {"User-Agent": "Mozilla/5.0 (compatible; WeatherlightNovidadesBot/1.0; +https://www.weatherlightgames.pt)", "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8"}
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def get(url):
    """GET com pausas: a loja responde 429 a pedidos muito seguidos."""
    for espera in (0, 15, 45, 90):
        time.sleep(espera or 1)
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                b = r.read()
                if b[:2] == b"\x1f\x8b": b = gzip.decompress(b)  # sitemaps .xml.gz
                return b.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or espera == 90: raise
            print(f"{e.code} em {url}; nova tentativa daqui a pouco")


def produtos_do_sitemap():
    """Devolve o conjunto de URLs de produtos (segue sitemaps-índice)."""
    vistos, fila, urls = set(), [SITE + "/sitemap.xml"], set()
    while fila:
        sm = fila.pop()
        if sm in vistos: continue
        vistos.add(sm)
        txt = get(sm)
        try:
            root = ET.fromstring(txt.lstrip("\ufeff \r\n\t"))
        except ET.ParseError:
            sys.exit(f"Sitemap {sm} não veio em XML. Início da resposta: {txt[:300]!r}")
        for loc in root.iter(NS + "loc"):
            u = (loc.text or "").strip()
            if root.tag.endswith("sitemapindex"):
                if "product" in u.rsplit("/", 1)[-1]: fila.append(u)  # só os sitemaps de produtos
            elif "/product/" in u:
                urls.add(u.split("?")[0].rstrip("/"))
    return urls


def dados_produto(url):
    """Nome, preço, imagem e disponibilidade a partir do JSON-LD (Product) da página."""
    html = get(url)
    d = {"url": url, "nome": None, "preco": None, "imagem": None, "stock": None}
    for bloco in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try:
            j = json.loads(bloco.strip())
        except Exception:
            continue
        for x in (j if isinstance(j, list) else j.get("@graph", [j])):
            if isinstance(x, dict) and x.get("@type") == "Product":
                d["nome"] = x.get("name")
                img = x.get("image")
                d["imagem"] = img[0] if isinstance(img, list) else (img.get("url") if isinstance(img, dict) else img)
                of = x.get("offers") or {}
                of = of[0] if isinstance(of, list) else of
                d["preco"] = of.get("price")
                d["stock"] = (of.get("availability") or "").rsplit("/", 1)[-1]
    if not d["nome"]:
        m = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        d["nome"] = unescape(m.group(1)) if m else url.rsplit("/", 1)[-1]
    if not d["imagem"]:
        m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        d["imagem"] = m.group(1) if m else None
    return d


def preco_txt(p):
    try:
        return f"{float(p):.2f} €".replace(".", ",")
    except (TypeError, ValueError):
        return None


def embed(d):
    e = {"title": d["nome"][:256], "url": d["url"], "color": COR,
         "footer": {"text": "Weatherlight Games & Collectibles · Évora"}}
    campos = []
    if preco_txt(d["preco"]): campos.append({"name": "Preço", "value": preco_txt(d["preco"]), "inline": True})
    if d["stock"] == "OutOfStock": campos.append({"name": "Estado", "value": "Esgotado", "inline": True})
    if campos: e["fields"] = campos
    if d["imagem"]: e["thumbnail"] = {"url": d["imagem"]}  # miniatura à direita (mais pequena que "image")
    return e


def publicar(webhook, produtos):
    for i in range(0, len(produtos), 10):
        lote = produtos[i:i + 10]
        texto = "✨ **Acabou de chegar à Weatherlight!**" if len(lote) == 1 else f"✨ **{len(lote)} novidades acabaram de chegar à Weatherlight!**"
        corpo = json.dumps({"username": "Weatherlight Novidades", "content": texto,
                            "embeds": [embed(d) for d in lote],
                            "allowed_mentions": {"parse": []}}).encode()
        req = urllib.request.Request(webhook, data=corpo, headers={**UA, "Content-Type": "application/json"})
        for tentativa in range(3):
            try:
                urllib.request.urlopen(req, timeout=30).read(); break
            except urllib.error.HTTPError as e:
                if e.code == 429 and tentativa < 2: time.sleep(5); continue
                raise
        time.sleep(2)


def main():
    estado_f = sys.argv[1]
    webhook = os.environ.get("DISCORD_WEBHOOK", "").strip()
    for modo in ("--teste", "--adicionar"):  # produtos indicados à mão
        if modo in sys.argv:
            urls = [u.split("?")[0].rstrip("/") for u in sys.argv[sys.argv.index(modo) + 1:]]
            ds = [dados_produto(u) for u in urls]
            print(json.dumps([embed(d) for d in ds], ensure_ascii=False, indent=1))
            if modo == "--teste" and webhook: publicar(webhook, ds)
            print(f"Página: {pagina.acrescentar(ds)} produtos juntados."); pagina.gerar()
            return
    atuais = produtos_do_sitemap()
    if len(atuais) < 50:
        sys.exit(f"Sitemap com só {len(atuais)} produtos: algo correu mal, não faço nada.")
    if not os.path.exists(estado_f):
        json.dump(sorted(atuais), open(estado_f, "w"), indent=0)
        print(f"Primeira execução: {len(atuais)} produtos registados, nada publicado.")
        return
    vistos = set(json.load(open(estado_f)))
    novos = sorted(atuais - vistos)
    print(f"{len(atuais)} produtos no site, {len(novos)} novos.")
    if novos:
        if not webhook: sys.exit("Falta o segredo DISCORD_WEBHOOK.")
        ds = []
        for u in novos[:30]:  # proteção: no máximo 30 por hora
            try: ds.append(dados_produto(u))
            except Exception as e: print("Falhou", u, e)
        publicar(webhook, ds)
        pagina.acrescentar(ds); pagina.gerar()
        vistos |= set(novos)
        json.dump(sorted(vistos), open(estado_f, "w"), indent=0)


if __name__ == "__main__":
    main()
