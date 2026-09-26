# Fondo astral de Pléyade: nebulosas azules y de oro rosa, estrellas y una galaxia espiral.
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter
DEST = Path(__file__).resolve().parents[2] / 'front' / 'public' / 'marca'
rng=np.random.default_rng(1763)
W,H=1920,1400
def fbm(w,h,oct=6,base=3,pers=.55):
    out=np.zeros((h,w)); amp=1; tot=0
    for o in range(oct):
        n=base*2**o
        g=rng.random((max(2,int(n*h/w))+1, n+1))
        im=Image.fromarray((g*255).astype(np.uint8)).resize((w,h), Image.BICUBIC)
        out+=amp*np.asarray(im,float)/255; tot+=amp; amp*=pers
    return out/tot
def hexrgb(h): return np.array([int(h[i:i+2],16) for i in (1,3,5)],float)/255
noche=hexrgb('#060b24'); azul=hexrgb('#1a4fb5'); azulc=hexrgb('#4f86e0'); rosa=hexrgb('#e7a98c'); rosab=hexrgb('#f3c9b4')
y,x=np.mgrid[0:H,0:W]/np.array([H,W])[:,None,None]
img=np.ones((H,W,3))*noche
# Nebulosa azul: franja diagonal irregular.
n1=fbm(W,H); n2=fbm(W,H,base=5)
banda=np.exp(-((y-0.55+0.35*(x-0.5))/0.33)**2)
d_azul=np.clip((n1-0.36)*2.6,0,1)**1.4*banda
img+= d_azul[...,None]*(azul*1.25) + (np.clip((n2-0.5)*3,0,1)**1.6*banda)[...,None]*azulc*0.8
# Brillo lechoso en el centro de la franja.
img+= (np.clip((fbm(W,H,base=6)-0.5)*3,0,1)**2*banda**3)[...,None]*hexrgb('#cfdcff')*0.35
# Nubes de oro rosa en las esquinas (como en el logo), sin mezclarlas con el azul fuerte.
esq=np.maximum(np.exp(-(((x-0.0)/0.42)**2+((y-0.95)/0.4)**2)), np.exp(-(((x-1.0)/0.38)**2+((y-0.1)/0.38)**2)))
d_rosa=np.clip((fbm(W,H,base=4)-0.4)*2.6,0,1)**1.5*esq
img=img*(1-0.6*d_rosa[...,None]) + d_rosa[...,None]*rosa*0.85 + (d_rosa**3)[...,None]*rosab*0.5
# Polvo oscuro.
img*= (0.75+0.25*fbm(W,H,base=8))[...,None]
# Galaxia espiral arriba a la izquierda.
cx,cy,R=0.12*W,0.17*H,230
gal=np.zeros((H,W))
for brazo in (0,np.pi):
    t=rng.random(16000)*4.2
    r=R*0.08*np.exp(0.45*t)*(1+0.12*rng.standard_normal(16000))
    a=t+brazo+0.25*rng.standard_normal(16000)
    px=(cx+r*np.cos(a)).astype(int); py=(cy+0.55*r*np.sin(a)).astype(int)
    ok=(px>=0)&(px<W)&(py>=0)&(py<H); np.add.at(gal,(py[ok],px[ok]),1)
gal=np.asarray(Image.fromarray(np.clip(gal*40,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)),float)/255
nucleo=np.exp(-(((x*W-cx)/30)**2+((y*H-cy)/18)**2))
img+= gal[...,None]*rosab*0.7 + nucleo[...,None]*rosab*0.9
# Estrellas: muchas diminutas, algunas con halo, pocas doradas.
est=np.zeros((H,W,3))
N=5200; sx=rng.integers(0,W,N); sy=rng.integers(0,H,N); b=rng.power(0.35,N)
col=np.where((rng.random(N)<0.12)[:,None], hexrgb('#f3c768'), np.where((rng.random(N)<0.3)[:,None], hexrgb('#cfe0ff'), np.ones(3)))
np.add.at(est,(sy,sx),col*b[:,None]*1.2)
halo=np.asarray(Image.fromarray(np.clip(est*255,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)),float)/255
img+= est + halo*1.6
# Unas pocas estrellas grandes con destello en cruz.
for _ in range(14):
    px,py=rng.integers(40,W-40),rng.integers(40,H-40); L=rng.integers(10,34); c=hexrgb('#f3c768') if rng.random()<.4 else np.ones(3)
    xs=np.arange(-L,L+1); f=np.exp(-np.abs(xs)/(L/4))
    img[py,px+xs]+=f[:,None]*c*0.9; img[py+xs,px]+=f[:,None]*c*0.9
    img+= (np.exp(-(((x*W-px)/3)**2+((y*H-py)/3)**2)))[...,None]*c
# Fundido abajo al azul noche de la marca (#0a1030) para enlazar con la trama de estrellas.
fin=hexrgb('#0a1030'); t=np.clip((y-0.72)/0.28,0,1)[...,None]**1.5
img=img*(1-t)+fin*t
out=Image.fromarray((np.clip(img,0,1)**(1/1.05)*255).astype(np.uint8))
out.save(DEST / 'galaxia.webp', quality=74, method=6)
out.resize((960,700), Image.LANCZOS).save(DEST / 'galaxia-960.webp', quality=74, method=6)
# Trama de estrellas repetible para páginas largas (sobre #0a1030).
T=512; tr=np.ones((T,T,3))*fin
n=260; tx=rng.integers(0,T,n); ty=rng.integers(0,T,n); tb=rng.power(0.3,n)
for i in range(n): tr[ty[i],tx[i]]=np.clip(fin+tb[i]*np.array([1,1,1])*1.1,0,1)
Image.fromarray((tr*255).astype(np.uint8)).save(DEST / 'estrellas.webp', quality=85, method=6)
