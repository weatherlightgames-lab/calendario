#!/usr/bin/env python3
"""Anuncia no Discord os produtos novos do site da Weatherlight (weatherlightgames.pt).

Corre de hora a hora (GitHub Actions, .github/workflows/novidades.yml):
  1. lê o sitemap do site e junta todos os URLs de produto (/product/...);
  2. compara com os já vistos (bot/estado/vistos.json, guardado no ramo `novidades-estado`);
  3. para cada produto novo, lê nome, preço, foto e stock da página do produto;
  4. publica no canal do Discord através do webhook (segredo DISCORD_WEBHOOK).

Na primeira execução (sem estado) regista todos os produtos existentes sem anunciar nada.
Sem DISCORD_WEBHOOK, ou com --teste, só mostra o que publicaria (não envia nada).
Só usa a biblioteca padrão do Python.
"""
import json, os, re, sys, time, html, urllib.request, xml.etree.ElementTree as ET

SITE = "https://www.weatherlightgames.pt"
SITEMAP = SITE + "/sitemap.xml"
ESTADO = os.environ.get("NOVIDADES_ESTADO", os.path.join(os.path.dirname(os.path.abspath(__file__)), "estado", "vistos.json"))
UA = "WeatherlightNovidadesBot/1.0 (+https://eventos.weatherlightgames.pt)"
MAX_POR_EXECUCAO = 30          # proteção: se aparecerem mais (ex.: importação em massa), anuncia só um resumo
EMBEDS_POR_MENSAGEM = 10       # limite do Discord
COR = 0xDEB455                 # dourado Weatherlight


def get(url, tentativas=3):
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if i == tentativas - 1:
                raise
            time.sleep(3 * (i + 1))


def urls_sitemap(url, visitados=None):
    """Devolve todos os URLs de produto, seguindo índices de sitemaps."""
    visitados = visitados or set()
    if url in visitados:
        return set()
    visitados.add(url)
    root = ET.fromstring(get(url).encode("utf-8"))
    ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
    locs = [e.text.strip() for e in root.iter(ns + "loc") if e.text]
    if root.tag.endswith("sitemapindex"):
        out = set()
        for l in locs:
            # só os sitemaps que podem ter produtos (evita tags, posts, etc.)
            if re.search(r"product|produto", l, re.I) or not re.search(r"(tag|post|blog|categor|brand|marca|page)", l, re.I):
                out |= urls_sitemap(l, visitados)
        return out
    return {l.split("?")[0].rstrip("/") for l in locs if "/product/" in l}


def dados_produto(url):
    """Nome, preço, foto e disponibilidade a partir do JSON-LD Product (o mesmo que o Google lê)."""
    pag = get(url)
    prod = None
    for bloco in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', pag, re.S | re.I):
        try:
            j = json.loads(bloco.strip())
        except Exception:
            continue
        for c in (j if isinstance(j, list) else j.get("@graph", [j])):
            if isinstance(c, dict) and c.get("@type") == "Product":
                prod = c
                break
        if prod:
            break
    def meta(p):
        m = re.search(r'<meta[^>]+property=["\']%s["\'][^>]+content=["\']([^"\']+)' % re.escape(p), pag, re.I)
        return html.unescape(m.group(1)) if m else None
    nome = (prod or {}).get("name") or meta("og:title") or url.rsplit("/", 1)[-1]
    img = (prod or {}).get("image") or meta("og:image")
    if isinstance(img, list):
        img = img[0] if img else None
    if isinstance(img, dict):
        img = img.get("url")
    ofertas = (prod or {}).get("offers") or {}
    if isinstance(ofertas, list):
        ofertas = ofertas[0] if ofertas else {}
    preco = ofertas.get("price")
    stock = str(ofertas.get("availability", ""))
    return {"url": url, "nome": html.unescape(str(nome)).strip(), "img": img, "preco": preco,
            "esgotado": "OutOfStock" in stock, "encomenda": "PreOrder" in stock or "BackOrder" in stock}


def preco_txt(p):
    try:
        return f"{float(p):.2f} €".replace(".", ",")
    except (TypeError, ValueError):
        return None


def embed(d):
    e = {"title": d["nome"][:256], "url": d["url"] + "?utm_source=discord&utm_medium=novidades", "color": COR,
         "footer": {"text": "Weatherlight Games & Collectibles · Évora"}}
    campos = []
    if preco_txt(d["preco"]):
        campos.append({"name": "Preço", "value": preco_txt(d["preco"]), "inline": True})
    campos.append({"name": "Disponibilidade", "inline": True,
                   "value": "Esgotado" if d["esgotado"] else ("Por encomenda" if d["encomenda"] else "Em stock · loja e site")})
    e["fields"] = campos
    if d["img"]:
        e["image"] = {"url": d["img"]}
    return e


def mensagens(novos):
    """Lista de payloads do Discord para os produtos novos."""
    if not novos:
        return []
    texto = "✨ **Acabou de chegar à Weatherlight!**" if len(novos) == 1 else f"✨ **{len(novos)} novidades acabaram de chegar à Weatherlight!**"
    out = []
    for i in range(0, len(novos), EMBEDS_POR_MENSAGEM):
        out.append({"content": texto if i == 0 else None, "embeds": [embed(d) for d in novos[i:i + EMBEDS_POR_MENSAGEM]],
                    "allowed_mentions": {"parse": []}})
    return out


def resumo(n):
    return [{"content": f"✨ **Chegaram {n} produtos novos à Weatherlight!** Vê tudo em {SITE}/new",
             "allowed_mentions": {"parse": []}}]


def enviar(webhook, payload):
    dados = json.dumps({k: v for k, v in payload.items() if v is not None}).encode("utf-8")
    for i in range(5):
        req = urllib.request.Request(webhook + "?wait=true", data=dados, method="POST",
                                     headers={"Content-Type": "application/json", "User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30):
                return
        except urllib.error.HTTPError as e:
            if e.code == 429:  # limite de envios: esperar o que o Discord pede
                time.sleep(float(json.loads(e.read() or b"{}").get("retry_after", 2)) + 0.5)
                continue
            raise
    raise RuntimeError("Discord recusou o envio depois de várias tentativas")


def main():
    teste = "--teste" in sys.argv
    webhook = os.environ.get("DISCORD_WEBHOOK", "").strip()
    atuais = urls_sitemap(SITEMAP)
    if len(atuais) < 50:
        sys.exit(f"Só encontrei {len(atuais)} produtos no sitemap: algo está errado, não mexo no estado.")
    vistos = set(json.load(open(ESTADO))["vistos"]) if os.path.exists(ESTADO) else None

    if vistos is None:
        print(f"Primeira execução: registo {len(atuais)} produtos existentes sem anunciar.")
        novos_urls = []
        vistos = set()
    else:
        novos_urls = sorted(atuais - vistos)
    print(f"{len(atuais)} produtos no site, {len(novos_urls)} novos.")

    if len(novos_urls) > MAX_POR_EXECUCAO:
        payloads = resumo(len(novos_urls))
    else:
        novos = []
        for u in novos_urls:
            try:
                novos.append(dados_produto(u))
            except Exception as e:
                print(f"Não consegui ler {u}: {e} (tento outra vez na próxima hora)")
                atuais.discard(u)  # não marcar como visto, para voltar a tentar
        payloads = mensagens(novos)

    if payloads and not webhook and not teste:
        sys.exit("Há produtos novos mas falta o segredo DISCORD_WEBHOOK: não anuncio nem guardo o estado.")
    for p in payloads:
        if teste:
            print(json.dumps(p, ensure_ascii=False, indent=1))
        else:
            enviar(webhook, p)
            time.sleep(1)

    if not teste:
        os.makedirs(os.path.dirname(ESTADO), exist_ok=True)
        json.dump({"atualizado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "vistos": sorted(vistos | atuais)},
                  open(ESTADO, "w"), ensure_ascii=False, indent=0)


if __name__ == "__main__":
    main()
