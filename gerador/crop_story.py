from PIL import Image
A='/mnt/user-data/attachments/46927a59-7be5-53b4-b750-22397d727fdd/'
# stories (9:16): a arte ocupa a metade de baixo; (ficheiro, slug, centro x, topo y, base y) em frações
J=[('4759834b','commander',.50,.46,1.0),('cd7a083a','modern',.65,.44,.86),('4f76556a','duelist',.60,.45,.98),
 ('2bc779b6','pirate',.60,.455,.83),('c468fd61','mtg-sc',.30,.45,.95),('5c360207','nexus-night',.30,.44,.92),
 ('f4679d8d','tamer',.68,.46,.98),('f24a8e74','pilot-lounge',.35,.48,.98),('3fedd117','op-sc',.45,.44,.80),
 ('83b29333','nightcity',.42,.45,.95),('a0759e78','pilot-party',.66,.46,.98),('fa825c3f','delta',.50,.45,.97),
 ('a3cb4183','assemble',.45,.47,1.0),('541d99c1','nexus-afternoon',.70,.43,.82)]
import sys
for f,slug,cx,y0,y1 in J:
    im=Image.open(A+f+'-image.jpg').convert('RGB'); W,H=im.size
    t=int(y0*H); b=int(y1*H); h=b-t; w=int(h*3/4)
    l=int(cx*W-w/2); l=max(0,min(W-w,l))
    if w>W: w=W; h=int(w*4/3); b=t+h
    q=im.crop((l,t,l+w,b)).resize((180,240),Image.LANCZOS)
    q.save(f'st/{slug}-v.jpg',quality=82,optimize=True,progressive=True)
print(W,H)
sheet=Image.new('RGB',(7*190,2*250),'white')
for i,(f,slug,*_) in enumerate(J):
    sheet.paste(Image.open(f'st/{slug}-v.jpg'),((i%7)*190,(i//7)*250))
sheet.save('chk/stories.jpg',quality=82)
