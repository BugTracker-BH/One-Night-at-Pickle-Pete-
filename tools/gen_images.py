#!/usr/bin/env python3
"""Generate all image + sprite-sheet assets for One Night at Pickle Pete's.
Original vector-style art via Pillow, brine palette, VHS post-processing."""
import os, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

IMG = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img')
os.makedirs(IMG, exist_ok=True)

# ----- palette -----
INK   = (8, 14, 8)
MURK  = (20, 33, 15)
OLIVE = (58, 95, 46)
GREEN = (143, 174, 75)
LIME  = (182, 194, 90)
ACID  = (216, 212, 74)
HI    = (207, 227, 154)
DARK  = (7, 16, 10)
RED   = (190, 50, 40)
GOLD  = (224, 196, 96)
WHITE = (236, 240, 220)

def font(sz):
    try: return ImageFont.truetype("DejaVuSans-Bold.ttf", sz)
    except Exception:
        try: return ImageFont.load_default(sz)
        except Exception: return ImageFont.load_default()

def new(w, h, bg=None, alpha=False):
    if alpha: return Image.new('RGBA', (w, h), (0, 0, 0, 0))
    return Image.new('RGB', (w, h), bg if bg else DARK)

def post(img, vig=0.55, grain=0.04, green=0.0, scan=False):
    rgba = img.convert('RGBA')
    arr = np.asarray(rgba).astype(np.float32)
    h, w = arr.shape[:2]
    rgb = arr[..., :3]; a = arr[..., 3:4]
    if vig > 0:
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.sqrt(((xx - w/2)/(w/2))**2 + ((yy - h/2)/(h/2))**2)
        mask = np.clip(1 - vig*(d**2), 0.15, 1)[..., None]
        rgb *= mask
    if green > 0:
        rgb[..., 1] *= (1+green); rgb[..., 0] *= (1-green*0.3); rgb[..., 2] *= (1-green*0.4)
    if scan:
        rgb[::3, :, :] *= 0.78
    if grain > 0:
        rgb += np.random.uniform(-1, 1, (h, w, 3)) * grain * 255
    rgb = np.clip(rgb, 0, 255)
    out = np.concatenate([rgb, a], axis=2).astype('uint8')
    return Image.fromarray(out, 'RGBA')

def save(img, name): img.convert('RGBA').save(os.path.join(IMG, name + '.png')); print('img', name, img.size)

def save_strip(frames, name):
    fw, fh = frames[0].size; sheet = Image.new('RGBA', (fw*len(frames), fh), (0,0,0,0))
    for i, f in enumerate(frames): sheet.paste(f.convert('RGBA'), (i*fw, 0))
    sheet.save(os.path.join(IMG, name + '.png')); print('strip', name, len(frames), 'x', (fw, fh))

# ============================ CHARACTER ============================
def pickle(d, cx, cy, w, h, expr='happy', body=GREEN, crown=False, eye=1.0, openmaw=0.0):
    """Draw a parametric pickle character centered at (cx,cy)."""
    x0, y0, x1, y1 = int(cx-w/2), int(cy-h/2), int(cx+w/2), int(cy+h/2)
    ow = max(3, int(w*0.04))
    # shadow
    d.ellipse([x0+ow, y1-int(h*0.06), x1-ow, y1+int(h*0.05)], fill=(0,0,0,90))
    # body
    d.ellipse([x0, y0, x1, y1], fill=body, outline=INK, width=ow)
    # belly highlight
    d.ellipse([x0+int(w*0.18), y0+int(h*0.10), x0+int(w*0.55), y0+int(h*0.6)], fill=(LIME[0],LIME[1],LIME[2],120))
    # warts
    rng = np.random.RandomState(7)
    for _ in range(int(w*h/2600)):
        wx = int(rng.uniform(x0+w*0.15, x1-w*0.15)); wy = int(rng.uniform(y0+h*0.12, y1-h*0.12))
        r = int(rng.uniform(w*0.02, w*0.05)); d.ellipse([wx-r, wy-r, wx+r, wy+r], fill=OLIVE)
    # eyes
    ey = y0 + int(h*0.30); ex = int(w*0.17); er = int(w*0.11*eye)
    for s in (-1, 1):
        cxe = cx + s*ex
        d.ellipse([cxe-er, ey-er, cxe+er, ey+er], fill=WHITE, outline=INK, width=max(2,ow//2))
        pr = int(er*0.5)
        pdx = int(er*0.25)*(1 if expr in ('angry','maw') else 0)
        d.ellipse([cxe-pr+pdx, ey-pr, cxe+pr+pdx, ey+pr], fill=INK)
        if expr in ('angry','maw'):  # brows
            d.line([cxe-er, ey-er-2, cxe+er, ey-int(er*0.2)], fill=INK, width=max(3,ow))
    # mouth
    my = y0 + int(h*0.56); mw = int(w*0.42)
    if openmaw > 0.02:
        mh = int(h*0.30*openmaw)
        d.ellipse([cx-mw, my-int(mh*0.3), cx+mw, my+mh], fill=(20,5,5), outline=INK, width=ow)
        # teeth
        tn = 6; tw = (2*mw)//tn
        for i in range(tn):
            tx = cx-mw + i*tw
            d.polygon([(tx,my-int(mh*0.2)),(tx+tw,my-int(mh*0.2)),(tx+tw//2,my+int(mh*0.25))], fill=WHITE)
            d.polygon([(tx,my+mh),(tx+tw,my+mh),(tx+tw//2,my+int(mh*0.55))], fill=WHITE)
    else:
        # grin arc with teeth
        d.arc([cx-mw, my-int(h*0.12), cx+mw, my+int(h*0.18)], 10, 170, fill=INK, width=ow+2)
        if expr in ('happy','grin'):
            tn=5; tw=(2*mw)//tn
            for i in range(tn):
                tx=cx-mw+int(w*0.04)+i*tw
                d.rectangle([tx, my+int(h*0.01), tx+tw-4, my+int(h*0.07)], fill=WHITE, outline=INK)
    # stubby arms
    d.line([x0+ow, cy, x0-int(w*0.12), cy+int(h*0.12)], fill=body, width=ow*2)
    d.line([x1-ow, cy, x1+int(w*0.12), cy+int(h*0.12)], fill=body, width=ow*2)
    if crown:
        cw=int(w*0.5); cyk=y0-int(h*0.02)
        pts=[(cx-cw//2,cyk),(cx-cw//4,cyk-int(h*0.12)),(cx,cyk),(cx+cw//4,cyk-int(h*0.12)),(cx+cw//2,cyk)]
        d.polygon(pts, fill=GOLD, outline=INK)
        for px,_ in [(cx-cw//2,0),(cx,0),(cx+cw//2,0)]:
            d.ellipse([px-4,cyk-int(h*0.13),px+4,cyk-int(h*0.13)+8], fill=RED)

# ============================ ROOMS ============================
def room(w, h, kind):
    img = new(w, h, MURK); d = ImageDraw.Draw(img, 'RGBA')
    # floor
    d.rectangle([0, int(h*0.68), w, h], fill=INK)
    d.line([0, int(h*0.68), w, int(h*0.68)], fill=OLIVE, width=3)
    if kind == 'storage':
        for sx in range(60, w-60, 220):
            d.rectangle([sx, int(h*0.2), sx+180, int(h*0.66)], fill=(35,52,26), outline=INK, width=4)
            for ry in range(int(h*0.26), int(h*0.62), 60):
                d.line([sx, ry, sx+180, ry], fill=INK, width=3)
                for jx in range(sx+18, sx+170, 40):
                    d.ellipse([jx, ry-34, jx+28, ry-2], fill=OLIVE, outline=INK, width=2)
                    d.rectangle([jx+4, ry-40, jx+24, ry-32], fill=GREEN)
    elif kind == 'vats':
        for vx in range(120, w-120, 320):
            d.rounded_rectangle([vx, int(h*0.18), vx+220, int(h*0.66)], 30, fill=(40,58,30), outline=INK, width=5)
            d.ellipse([vx, int(h*0.14), vx+220, int(h*0.26)], fill=OLIVE, outline=INK, width=4)
            for b in range(8):
                bx=vx+30+np.random.randint(0,160); by=int(h*0.16)+np.random.randint(0,12)
                d.ellipse([bx,by,bx+10,by+10], fill=LIME)
            d.line([vx+110, int(h*0.02), vx+110, int(h*0.18)], fill=(60,60,60), width=14)
    elif kind == 'aisle':
        for s in (-1, 1):
            base = w//2 + s*int(w*0.05)
            for k in range(5):
                t=k/5; x_in=int(w/2 + s*(t*w*0.5+w*0.05)); yt=int(h*0.25+t*h*0.1); yb=int(h*0.66-t*h*0.05)
                d.rectangle([min(base,x_in),yt,max(base,x_in),yb], outline=INK, width=2)
        d.polygon([(w//2-30,int(h*0.66)),(w//2+30,int(h*0.66)),(w//2+120,h),(w//2-120,h)], fill=(28,42,20))
    elif kind == 'backdoor':
        d.rectangle([int(w*0.32), int(h*0.16), int(w*0.62), int(h*0.7)], fill=(28,40,20), outline=INK, width=6)
        d.rectangle([int(w*0.48), int(h*0.16), int(w*0.62), int(h*0.7)], fill=(2,4,2))  # ajar darkness
        for tx in (int(w*0.7), int(w*0.78)):
            d.rounded_rectangle([tx, int(h*0.46), tx+60, int(h*0.66)], 8, fill=(34,50,26), outline=INK, width=3)
    else:  # halls
        d.polygon([(0,0),(int(w*0.32),int(h*0.22)),(int(w*0.32),int(h*0.78)),(0,h)], fill=(30,46,22))
        d.polygon([(w,0),(int(w*0.68),int(h*0.22)),(int(w*0.68),int(h*0.78)),(w,h)], fill=(30,46,22))
        d.rectangle([int(w*0.32),int(h*0.22),int(w*0.68),int(h*0.78)], fill=(12,20,9), outline=INK, width=4)
        d.ellipse([int(w*0.46),int(h*0.18),int(w*0.54),int(h*0.24)], fill=ACID)  # bulb
    return post(img, vig=0.6, grain=0.06, green=0.22, scan=True)

# ============================ OFFICE ============================
def office(light=1.0):
    w, h = 1280, 720; img = new(w, h, (16,26,13)); d = ImageDraw.Draw(img, 'RGBA')
    # back wall shelves with jars
    d.rectangle([0, 0, w, int(h*0.62)], fill=(22,34,16))
    for ry in range(110, 360, 110):
        d.rectangle([330, ry, 950, ry+14], fill=(38,54,28), outline=INK, width=2)
        for jx in range(345, 940, 56):
            d.ellipse([jx, ry-44, jx+40, ry-2], fill=OLIVE, outline=INK, width=2)
            d.rectangle([jx+8, ry-52, jx+32, ry-42], fill=GREEN)
    # hanging light + cone
    d.line([w//2, 0, w//2, 120], fill=(40,40,40), width=6)
    d.ellipse([w//2-40, 110, w//2+40, 160], fill=ACID, outline=INK, width=3)
    cone = Image.new('RGBA', (w, h), (0,0,0,0)); cd = ImageDraw.Draw(cone)
    cd.polygon([(w//2-40,150),(w//2+40,150),(w//2+360,520),(w//2-360,520)], fill=(255,240,170,int(60*light)))
    img = Image.alpha_composite(img.convert('RGBA'), cone)
    d = ImageDraw.Draw(img, 'RGBA')
    # counter foreground
    d.rectangle([0, int(h*0.72), w, h], fill=(24,18,10))
    d.rounded_rectangle([0, int(h*0.66), w, int(h*0.78)], 16, fill=(40,30,16), outline=INK, width=4)
    # cash register
    d.rounded_rectangle([540, int(h*0.6), 740, int(h*0.72)], 10, fill=(30,44,22), outline=INK, width=4)
    d.rectangle([560, int(h*0.62), 720, int(h*0.66)], fill=ACID)
    # window frames hint (engine overdraws actual windows)
    for x0 in (0, w-300):
        d.rectangle([x0, 80, x0+300, 600], outline=INK, width=8)
    return post(img, vig=0.5, grain=0.04)

# ============================ WINDOWS ============================
def window(occupant=None):
    w, h = 300, 520; img = new(w, h, (10,16,8)); d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0,0,w,h], fill=(6,10,5))
    d.rectangle([16,16,w-16,h-16], fill=(12,20,9), outline=(40,40,40), width=10)  # frame + dark glass
    # brine drips on sill
    for dx in range(30, w-30, 36):
        d.ellipse([dx, h-40, dx+12, h-18], fill=(40,70,30,160))
    if occupant == 'pete':
        pickle(d, w//2, h//2+10, 200, 320, expr='grin', body=GREEN)
    elif occupant == 'twins':
        pickle(d, w//2-60, h//2+30, 120, 200, expr='angry', body=LIME)
        pickle(d, w//2+60, h//2+50, 120, 200, expr='angry', body=LIME)
    # glass glare
    d.line([40, 40, 120, 160], fill=(255,255,255,30), width=8)
    return post(img, vig=0.6, grain=0.05)

# ============================ CHARACTER OVERLAYS (on cam) ============================
CAM_RECT = (40, 40, 1200, 520)  # x,y,w,h within 1280x720 where cam feed is drawn
def overlay_char(kind, room_key, frame=0):
    img = new(1280, 720, None, alpha=True); d = ImageDraw.Draw(img, 'RGBA')
    rx, ry, rw, rh = CAM_RECT
    cx = rx + int(rw*0.5); cy = ry + int(rh*0.62)
    bob = int(6*math.sin(frame))
    if kind == 'pete':
        pickle(d, cx, cy+bob, 240, 380, expr='grin', body=GREEN)
    elif kind == 'twins':
        pickle(d, cx-110, cy+bob, 150, 240, expr='angry', body=LIME)
        pickle(d, cx+110, cy-bob, 150, 240, expr='angry', body=LIME)
    return img  # keep crisp/transparent (no vignette)

# ============================ UI ============================
def tablet_frame():
    w, h = 1280, 720; img = new(w, h, None, alpha=True); d = ImageDraw.Draw(img, 'RGBA')
    # outer dark bezel with transparent viewport (matches CAM_RECT-ish)
    d.rectangle([0,0,w,h], fill=(10,16,9,235))
    d.rectangle([28, 28, w-28, h-150], fill=(0,0,0,0))  # clear viewport
    d.rectangle([28, 28, w-28, h-150], outline=(60,80,40,255), width=6)
    # bottom button bar plate
    d.rounded_rectangle([20, h-140, w-20, h-16], 14, fill=(16,26,13,235), outline=(60,80,40,255), width=4)
    # screws
    for sx,sy in [(14,14),(w-14,14),(14,h-14),(w-14,h-14)]:
        d.ellipse([sx-8,sy-8,sx+8,sy+8], fill=(40,50,30,255), outline=INK)
    return img

def scanlines():
    w, h = 1200, 520; img = new(w, h, None, alpha=True); arr = np.zeros((h, w, 4), np.uint8)
    arr[::3, :, 3] = 70  # dark scanlines
    img = Image.fromarray(arr, 'RGBA')
    d = ImageDraw.Draw(img, 'RGBA')
    # vignette ring
    for i in range(40):
        a = int(4*i/40*255/40)
        d.rectangle([i,i,w-i,h-i], outline=(0,0,0,a))
    return img

def logo():
    w, h = 800, 240; img = new(w, h, None, alpha=True); d = ImageDraw.Draw(img, 'RGBA')
    f1 = font(54); f2 = font(70)
    def shadow_text(x,y,txt,fnt,col):
        d.text((x+3,y+3), txt, font=fnt, fill=(0,0,0,200), anchor='mm')
        d.text((x,y), txt, font=fnt, fill=col, anchor='mm')
    shadow_text(w//2, 60, "ONE NIGHT AT", f1, HI)
    shadow_text(w//2-40, 150, "PICKLE PETE'S", f2, ACID)
    pickle(d, w-90, 150, 120, 180, expr='grin', body=GREEN)
    return img

def cam_map():
    w, h = 360, 240; img = new(w, h, (12,20,9), alpha=False); d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([10,10,w-10,h-10], outline=GREEN, width=2)
    rooms=[(40,40,'1'),(150,40,'2'),(260,40,'3'),(40,150,'5'),(150,150,'4'),(260,150,'6')]
    for x,y,lab in rooms:
        d.rectangle([x,y,x+70,y+60], outline=GREEN, width=2); d.text((x+30,y+25), lab, font=font(22), fill=ACID)
    out = post(img, vig=0.2, grain=0.02)
    out.putalpha(180); return out

def dilllord_pose():
    w, h = 400, 360; img = new(w, h, None, alpha=True); d = ImageDraw.Draw(img, 'RGBA')
    pickle(d, w//2, h//2+20, 220, 300, expr='angry', body=(107,143,58), crown=True, openmaw=0.2)
    # glitch slices
    arr = np.asarray(img).copy()
    for _ in range(8):
        yy = np.random.randint(0, h-12); sh = np.random.randint(-30, 30)
        arr[yy:yy+12] = np.roll(arr[yy:yy+12], sh, axis=1)
    return Image.fromarray(arr, 'RGBA')

# ============================ STRIPS ============================
def strip_office_idle():
    frames=[]
    for i in range(4):
        light = 0.7+0.3*abs(math.sin(i*0.9))
        frames.append(office(light))
    save_strip(frames, 'office_idle')

def strip_shutter(side):
    frames=[]
    for i in range(6):
        w,h=300,520; img=new(w,h,None,alpha=True); d=ImageDraw.Draw(img,'RGBA')
        prog=i/5; yb=int(prog*h)
        d.rectangle([0,0,w,yb], fill=(46,46,46))
        for sy in range(0,yb,26):  # corrugation
            d.line([0,sy,w,sy], fill=(28,28,28), width=10)
        d.rectangle([0,max(0,yb-12),w,yb], fill=(70,70,70))
        d.rectangle([0,0,w,yb], outline=INK, width=4)
        frames.append(img)
    save_strip(frames, 'shutter_'+side)

def strip_tablet_flip():
    frames=[]; w,h=640,360
    for i in range(8):
        img=new(w,h,(4,7,5)); d=ImageDraw.Draw(img,'RGBA')
        prog=i/7; top=int((1-prog)*h)
        d.rectangle([0,top,w,h], fill=(12,20,9), outline=(60,80,40), width=4)
        iy0, iy1 = top+16, h-40
        if iy1 > iy0:
            d.rectangle([20,iy0,w-20,iy1], fill=(8,30,8))
            d.text((w//2,(iy0+iy1)//2), "BOOTING…", font=font(24), fill=GREEN, anchor='mm')
        frames.append(post(img, vig=0.3, grain=0.05))
    save_strip(frames, 'tablet_flip_up')

def strip_cam_switch():
    frames=[]; w,h=600,260
    for i in range(4):
        img=new(w,h,(20,20,20)); arr=np.random.randint(0,90,(h,w,3),np.uint8); arr[...,1]+=30
        img=Image.fromarray(arr,'RGB'); d=ImageDraw.Draw(img)
        d.rectangle([0,(i*60)%h,w,(i*60)%h+20], fill=(180,180,160))
        frames.append(post(img,vig=0.3,grain=0.1))
    save_strip(frames,'cam_switch')

def strip_dill_static():
    frames=[]; w,h=600,260
    for i in range(6):
        arr=np.random.randint(0,120,(h,w,3),np.uint8); arr[...,1]=np.clip(arr[...,1]+40,0,255)
        img=Image.fromarray(arr,'RGB'); d=ImageDraw.Draw(img,'RGBA')
        # face bleeding through
        a=int(120+80*math.sin(i)); pickle(d, w//2, h//2, 160, 220, expr='angry', body=(90,120,50), crown=True, openmaw=0.3)
        for _ in range(6):
            yy=np.random.randint(0,h-8); arr2=np.asarray(img).copy(); 
        frames.append(post(img,vig=0.2,grain=0.12))
    save_strip(frames,'dill_static_loop')

def strip_pump_lever():
    frames=[]; w,h=200,300
    for i in range(5):
        img=new(w,h,None,alpha=True); d=ImageDraw.Draw(img,'RGBA')
        ang=-0.6+1.2*(i/4)
        x2=int(w/2+math.sin(ang)*70); y2=int(h*0.7-math.cos(ang)*120)
        d.rounded_rectangle([w//2-20,int(h*0.66),w//2+20,h-10],8,fill=(50,40,20),outline=INK,width=3)
        d.line([w//2,int(h*0.7),x2,y2], fill=(90,70,30), width=16)
        d.ellipse([x2-14,y2-14,x2+14,y2+14], fill=RED, outline=INK, width=3)
        frames.append(img)
    save_strip(frames,'pump_lever')

def strip_battery():
    frames=[]; w,h=240,100
    for i in range(6):
        lvl=(5-i)/5; img=new(w,h,None,alpha=True); d=ImageDraw.Draw(img,'RGBA')
        d.rectangle([6,20,w-20,h-20], outline=GREEN, width=4); d.rectangle([w-20,40,w-8,h-40], fill=GREEN)
        col = GREEN if lvl>0.4 else (ACID if lvl>0.2 else RED)
        d.rectangle([12,26,12+int((w-38)*lvl),h-26], fill=col)
        frames.append(img)
    save_strip(frames,'battery')

def strip_low_battery():
    frames=[]; w,h=320,180
    for i in range(4):
        a=int(40+50*abs(math.sin(i)))
        img=new(w,h,None,alpha=True); d=ImageDraw.Draw(img,'RGBA')
        d.rectangle([0,0,w,h], fill=(170,0,0,a))
        frames.append(img)
    save_strip(frames,'low_battery_overlay')

def strip_title_bg():
    frames=[]; w,h=640,360
    for i in range(6):
        img=new(w,h,(8,14,9)); d=ImageDraw.Draw(img,'RGBA')
        d.rectangle([0,int(h*0.7),w,h], fill=(14,22,10))  # ground
        d.rectangle([w//2-180,80,w//2+180,int(h*0.7)], fill=(20,30,14), outline=INK, width=4)  # storefront
        bri = 0.5+0.5*abs(math.sin(i*1.1))
        sign=(int(ACID[0]*bri),int(ACID[1]*bri),int(ACID[2]*bri))
        d.text((w//2,120), "PICKLE PETE'S", font=font(34), fill=sign, anchor='mm')
        d.rectangle([w//2-60,160,w//2+60,260], fill=(4,6,3))  # dark window
        if i%2==0:
            d.ellipse([w//2-30,200,w//2-14,216], fill=ACID); d.ellipse([w//2+14,200,w//2+30,216], fill=ACID)  # eyes
        frames.append(post(img,vig=0.6,grain=0.05))
    save_strip(frames,'title_bg')

def strip_night_card():
    frames=[]; w,h=640,360
    for i in range(6):
        img=new(w,h,(0,0,0)); d=ImageDraw.Draw(img,'RGBA')
        d.ellipse([w//2-90,40,w//2+90,220], outline=(40,60,28), width=4)
        d.line([w//2,130,w//2,70], fill=GREEN, width=4); d.line([w//2,130,w//2+40,150], fill=GREEN, width=4)
        frames.append(post(img,vig=0.7,grain=0.03))
    save_strip(frames,'night_card')

def strip_win():
    frames=[]; w,h=640,360
    for i in range(24):
        t=i/23; img=new(w,h,(10,16,9)); d=ImageDraw.Draw(img,'RGBA')
        # sunrise gradient
        for y in range(h):
            f=y/h; r=int(lerp(20,255,t*(1-f))); g=int(lerp(30,210,t*(1-f))); b=int(lerp(15,120,t*(1-f)))
            d.line([0,y,w,y], fill=(r,g,b))
        d.ellipse([w//2-60,int(h*0.5-t*120),w//2+60,int(h*0.5-t*120)+120], fill=(255,int(230),150))
        # pete slumping away
        pickle(d, int(w*0.2 - t*60), int(h*0.7), 80, 130, expr='happy', body=OLIVE)
        frames.append(post(img,vig=0.4,grain=0.03))
    save_strip(frames,'win_6am')

def strip_gameover():
    frames=[]; w,h=640,360
    for i in range(12):
        t=i/11
        arr=(np.random.randint(0,120,(h,w,3))*(1-t)).astype(np.uint8)
        img=Image.fromarray(arr,'RGB'); d=ImageDraw.Draw(img,'RGBA')
        d.rectangle([0,0,w,h], fill=(20,6,6,int(200*t)))
        if t>0.4: d.text((w//2,h//2),"SHIFT OVER",font=font(46),fill=(190,50,40),anchor='mm')
        # crack
        if t>0.5:
            for _ in range(4):
                x=np.random.randint(0,w); d.line([x,0,x+np.random.randint(-60,60),h], fill=(0,0,0), width=2)
        frames.append(post(img,vig=0.5,grain=0.08))
    save_strip(frames,'gameover')

def lerp(a,b,t): return a+(b-a)*t

def strip_jumpscare(name, kind):
    n = 24 if kind=='dill' else 18; frames=[]; w,h=640,360
    for i in range(n):
        t=i/(n-1); img=new(w,h,(0,0,0)); d=ImageDraw.Draw(img,'RGBA')
        if i%2==0 and t>0.2: d.rectangle([0,0,w,h], fill=(120,0,0))  # red flash
        scale=lerp(0.3,1.25,t); cw=int(w*0.4*scale*2); ch=int(h*0.5*scale*2)
        maw=min(1.0, t*1.6)
        jit_x=int((np.random.rand()-0.5)*20*t); jit_y=int((np.random.rand()-0.5)*20*t)
        cx,cy=w//2+jit_x, int(h*0.55)+jit_y
        if kind=='pete':   pickle(d,cx,cy,cw,ch,expr='maw',body=GREEN,openmaw=maw)
        elif kind=='granny':pickle(d,cx,cy,cw,ch,expr='maw',body=(150,165,80),openmaw=maw)
        elif kind=='twins':
            pickle(d,cx-int(cw*0.4),cy,int(cw*0.7),int(ch*0.8),expr='maw',body=LIME,openmaw=maw)
            pickle(d,cx+int(cw*0.4),cy,int(cw*0.7),int(ch*0.8),expr='maw',body=LIME,openmaw=maw)
        else:              pickle(d,cx,cy,cw,ch,expr='maw',body=(107,143,58),crown=True,openmaw=maw)
        out=post(img,vig=0.3,grain=0.1)
        if kind=='dill':  # glitch slices
            a=np.asarray(out).copy()
            for _ in range(10):
                yy=np.random.randint(0,h-10); a[yy:yy+10]=np.roll(a[yy:yy+10], np.random.randint(-40,40), axis=1)
            out=Image.fromarray(a,'RGBA')
        frames.append(out)
    save_strip(frames, name)

# ============================ MAIN ============================
if __name__ == '__main__':
    # office
    save(office(1.0), 'office_base'); strip_office_idle()
    # windows
    save(window(None), 'window_left_open'); save(window(None), 'window_right_open')
    save(window('pete'), 'window_left_full'); save(window('twins'), 'window_right_full')
    # cameras
    for key,kind in [('cam_storage','storage'),('cam_vats','vats'),('cam_aisle','aisle'),
                     ('cam_backdoor','backdoor'),('cam_lefthall','hall'),('cam_righthall','hall')]:
        save(room(1200,520,kind), key)
    # character overlays on cam
    for r in ['storage','vats','aisle','lefthall']: save(overlay_char('pete', r), 'pete_'+r)
    for r in ['vats','aisle','backdoor','righthall']: save(overlay_char('twins', r), 'sourtwins_'+r)
    save(dilllord_pose(), 'dilllord_pose')
    # UI
    save(tablet_frame(), 'tablet_frame'); save(scanlines(), 'scanlines_overlay')
    save(cam_map(), 'cam_map'); save(logo(), 'logo')
    save(new(64,64,None,alpha=True), 'hour_chime_overlay')
    # strips
    strip_shutter('left'); strip_shutter('right'); strip_tablet_flip()
    strip_cam_switch(); strip_dill_static(); strip_pump_lever()
    strip_battery(); strip_low_battery(); strip_title_bg(); strip_night_card()
    strip_win(); strip_gameover()
    strip_jumpscare('js_pete','pete'); strip_jumpscare('js_granny','granny')
    strip_jumpscare('js_twins','twins'); strip_jumpscare('js_dill','dill')
    print('IMAGES DONE')
