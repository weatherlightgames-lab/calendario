"""Recorta a arte das stories (9:16) para cada evento de semana.json e futuros.json.
Uso: python3 recortar.py <pasta-das-stories>
Cada evento tem "story" (início do nome do ficheiro) e "recorte": [centro_x, topo_y, base_y] em frações (0–1).
Gera ../img/<arte>-v.jpg (miniatura 180x240) e ../img/<arte>-g.jpg (720x960, para o Google)."""
import json, os, sys, glob
from PIL import Image
AQUI=os.path.dirname(os.path.abspath(__file__)); IMG=os.path.join(os.path.dirname(AQUI),'img')
pasta=sys.argv[1]; os.makedirs(IMG,exist_ok=True)
S=json.load(open(os.path.join(AQUI,'semana.json')))
FUT=os.path.join(AQUI,'futuros.json')
EVS=[e for d in S['dias'] for e in d['eventos']]+(json.load(open(FUT)) if os.path.exists(FUT) else [])
if True:
    for e in EVS:
        if not e.get('story'): continue
        f=sorted(glob.glob(os.path.join(pasta,e['story']+'*')))
        if not f: print('Falta a story de',e['evento']); continue
        im=Image.open(f[0]).convert('RGB'); W,H=im.size; cx,y0,y1=e['recorte']
        t=int(y0*H); h=int(y1*H)-t; w=int(h*3/4)
        if w>W: w=W; h=int(w*4/3)
        l=max(0,min(W-w,int(cx*W-w/2))); c=im.crop((l,t,l+w,t+h))
        c.resize((180,240),Image.LANCZOS).save(os.path.join(IMG,e['arte']+'-v.jpg'),quality=82,optimize=True,progressive=True)
        g=c.copy(); g.thumbnail((720,960),Image.LANCZOS); g.save(os.path.join(IMG,e['arte']+'-g.jpg'),quality=80,optimize=True,progressive=True)
        print('ok',e['arte'])
