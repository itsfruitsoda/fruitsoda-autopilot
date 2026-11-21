import numpy as np, cv2, math, subprocess, os, json, wave
from PIL import Image, ImageDraw, ImageFont
W,H,FPS=1080,1920,30
FD=os.environ.get('FS_FONTS','/usr/share/fonts/truetype/google-fonts/')
NAVY=(31,42,68);PINK=(255,61,129);YEL=(255,196,0);TEAL=(0,168,150);BLUE=(0,150,255);RED=(230,57,70);CREAM=(255,246,235);WHITE=(255,255,255);BLACK=(0,0,0)
_f={}
def font(sz,w='Bold'):
    k=(sz,w)
    if k not in _f: _f[k]=ImageFont.truetype(FD+f'Poppins-{w}.ttf',sz)
    return _f[k]
def clamp(x,a=0,b=1): return max(a,min(b,x))
def ease(x): x=clamp(x); return x*x*(3-2*x)
def back(x):
    x=clamp(x); c1=1.70158; c3=c1+1
    return 1+c3*(x-1)**3+c1*(x-1)**2
def lerp(a,b,t): return a+(b-a)*t
def mix(c1,c2,t): return tuple(int(lerp(a,b,clamp(t))) for a,b in zip(c1,c2))

class Cv:
    def __init__(s,bg):
        s.img=bg.copy(); s.texts=[]
    def circ(s,c,r,col,th=-1,a=1.0):
        c=(int(c[0]),int(c[1])); r=max(1,int(r))
        if a>=1: cv2.circle(s.img,c,r,col,th,cv2.LINE_AA)
        else:
            o=s.img.copy(); cv2.circle(o,c,r,col,th,cv2.LINE_AA); s.img=cv2.addWeighted(o,a,s.img,1-a,0)
    def ell(s,c,ax,col,th=-1,ang=0,a=1.0,st=0,en=360):
        c=(int(c[0]),int(c[1])); ax=(max(1,int(ax[0])),max(1,int(ax[1])))
        if a>=1: cv2.ellipse(s.img,c,ax,ang,st,en,col,th,cv2.LINE_AA)
        else:
            o=s.img.copy(); cv2.ellipse(o,c,ax,ang,st,en,col,th,cv2.LINE_AA); s.img=cv2.addWeighted(o,a,s.img,1-a,0)
    def line(s,p,q,col,th):
        cv2.line(s.img,(int(p[0]),int(p[1])),(int(q[0]),int(q[1])),col,max(1,int(th)),cv2.LINE_AA)
    def poly(s,pts,col,a=1.0,th=-1):
        p=np.array(pts,np.int32)
        o=s.img if a>=1 else s.img.copy()
        if th<0: cv2.fillPoly(o,[p],col,cv2.LINE_AA)
        else: cv2.polylines(o,[p],True,col,th,cv2.LINE_AA)
        if a<1: s.img=cv2.addWeighted(o,a,s.img,1-a,0)
    def rrect(s,x0,y0,x1,y1,r,col,th=-1,a=1.0):
        o=s.img if a>=1 else s.img.copy()
        r=int(min(r,(x1-x0)/2,(y1-y0)/2)); x0,y0,x1,y1=int(x0),int(y0),int(x1),int(y1)
        if th<0:
            cv2.rectangle(o,(x0+r,y0),(x1-r,y1),col,-1,cv2.LINE_AA); cv2.rectangle(o,(x0,y0+r),(x1,y1-r),col,-1,cv2.LINE_AA)
            for cx,cy in((x0+r,y0+r),(x1-r,y0+r),(x0+r,y1-r),(x1-r,y1-r)): cv2.circle(o,(cx,cy),r,col,-1,cv2.LINE_AA)
        else:
            cv2.line(o,(x0+r,y0),(x1-r,y0),col,th,cv2.LINE_AA);cv2.line(o,(x0+r,y1),(x1-r,y1),col,th,cv2.LINE_AA)
            cv2.line(o,(x0,y0+r),(x0,y1-r),col,th,cv2.LINE_AA);cv2.line(o,(x1,y0+r),(x1,y1-r),col,th,cv2.LINE_AA)
            for (cx,cy,a0) in((x0+r,y0+r,180),(x1-r,y0+r,270),(x0+r,y1-r,90),(x1-r,y1-r,0)): cv2.ellipse(o,(cx,cy),(r,r),0,a0,a0+90,col,th,cv2.LINE_AA)
        if a<1: s.img=cv2.addWeighted(o,a,s.img,1-a,0)
    def text(s,t,xy,sz,col=WHITE,anchor='mm',stroke=0,sc=BLACK,w='Bold',a=1.0):
        s.texts.append((t,xy,sz,col,anchor,stroke,sc,w,a))
    def done(s):
        if not s.texts: return s.img
        im=Image.fromarray(s.img); 
        for t,xy,sz,col,anc,stk,sc,w,a in s.texts:
            if a<1:
                lay=Image.new('RGBA',im.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
                d.text(xy,t,font=font(sz,w),fill=col+(int(255*a),),anchor=anc,stroke_width=stk,stroke_fill=sc+(int(255*a),))
                im=Image.alpha_composite(im.convert('RGBA'),lay).convert('RGB')
            else:
                ImageDraw.Draw(im).text(xy,t,font=font(sz,w),fill=col,anchor=anc,stroke_width=stk,stroke_fill=sc)
        return np.asarray(im)

def gradient(c1,c2):
    t=np.linspace(0,1,H)[:,None,None]
    g=(np.array(c1)[None,None,:]*(1-t)+np.array(c2)[None,None,:]*t)
    return np.repeat(g,W,axis=1).astype(np.uint8)
