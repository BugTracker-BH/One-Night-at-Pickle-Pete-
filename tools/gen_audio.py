#!/usr/bin/env python3
"""Generate all audio assets for One Night at Pickle Pete's as 16-bit mono WAV.
Everything is synthesized from scratch (original)."""
import numpy as np, wave, os, math

SR = 44100
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'audio')
os.makedirs(OUT, exist_ok=True)

def save(name, sig):
    sig = np.asarray(sig, dtype=np.float32)
    m = np.max(np.abs(sig)) or 1.0
    sig = (sig / m) * 0.92
    pcm = (sig * 32767).astype('<i2')
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print('audio', name, f'{len(sig)/SR:.2f}s')

def t(dur): return np.linspace(0, dur, int(SR*dur), endpoint=False)
def sine(f, dur, ph=0): return np.sin(2*np.pi*f*t(dur)+ph)
def saw(f, dur):
    x = t(dur); return 2*(x*f - np.floor(0.5+x*f))
def noise(dur): return np.random.uniform(-1, 1, int(SR*dur))
def env_exp(dur, k=4):
    x = np.linspace(0, 1, int(SR*dur)); return np.exp(-k*x)
def env_adsr(dur, a=0.01, d=0.1, s=0.7, r=0.1):
    n=int(SR*dur); out=np.ones(n)*s
    na,nd,nr=int(SR*a),int(SR*d),int(SR*r)
    if na: out[:na]=np.linspace(0,1,na)
    if nd: out[na:na+nd]=np.linspace(1,s,nd)
    if nr: out[-nr:]=np.linspace(out[-nr] if n>nr else s,0,nr)
    return out[:n]
def lp(sig, a=0.05):  # simple one-pole low-pass
    out=np.copy(sig)
    for i in range(1,len(sig)): out[i]=out[i-1]+a*(sig[i]-out[i-1])
    return out
def reverb(sig, decay=0.3, delays=(0.031,0.047,0.067)):
    out=np.copy(sig)
    for dl in delays:
        d=int(SR*dl); e=np.zeros(len(sig)+d); e[d:]=sig*decay; out=out+e[:len(sig)]
    return out
def pad(sig, dur):
    n=int(SR*dur); 
    return np.concatenate([sig, np.zeros(max(0,n-len(sig)))])[:n] if n>len(sig) else sig[:n]

# semitone -> freq from A4
def nt(semis_from_a4): return 440.0*2**(semis_from_a4/12)

# ----------------------------------------------------------------- MUSIC
def menu_theme():
    # eerie music-box waltz in 3/4, minor, detuned, original melody
    bpm=84; beat=60/bpm
    # melody (semitones from A4), -1 = rest ; A minor-ish creepy line
    mel=[0,7,3, 0,7,3, -2,5,2, -2,5,2, 3,10,7, 3,10,7, -5,2,-1, 5,3,0]
    out=np.zeros(0)
    for i,s in enumerate(mel):
        dur=beat*(1.0 if i%3==0 else 0.5)
        if s==-1: seg=np.zeros(int(SR*dur)); 
        else:
            f=nt(s); base=sine(f,dur)*0.6+sine(f*2.0,dur)*0.2+sine(f*1.005,dur)*0.3
            base+=sine(f*0.5,dur)*0.15
            seg=base*env_exp(dur,5)*(0.7+0.3*math.sin(i))
        out=np.concatenate([out,seg])
    out=reverb(out,0.25)
    # soft detuned pad underneath
    padline=sine(nt(-12),len(out)/SR)*0.08+sine(nt(-12)*1.01,len(out)/SR)*0.06
    out=out[:len(padline)]+padline[:len(out)]
    save('menu_theme', out)

def ambience_loop():
    dur=8.0; x=t(dur)
    hum=(np.sin(2*np.pi*60*x)*0.18+np.sin(2*np.pi*120*x)*0.06)
    flick=np.sin(2*np.pi*0.7*x)*0.02
    air=lp(noise(dur),0.002)*0.10
    out=hum*(0.9+flick)+air
    # occasional brine drips
    for dt_ in [1.3,3.1,5.6,7.0]:
        i=int(SR*dt_); d=sine(900,0.05)*env_exp(0.05,40); out[i:i+len(d)]+=d*0.25
    # loop crossfade
    f=int(SR*0.4); out[:f]*=np.linspace(0,1,f); out[-f:]*=np.linspace(1,0,f)
    save('ambience_loop', out)

def tension_loop():
    dur=8.0; x=t(dur)
    drone=(np.sin(2*np.pi*55*x)+np.sin(2*np.pi*58*x)+np.sin(2*np.pi*82.4*x))*0.12
    rise=np.linspace(0.4,1.0,len(x))
    # ticking clock
    tick=np.zeros(len(x))
    for k in range(int(dur*2)):
        i=int(SR*k*0.5); c=noise(0.01)*env_exp(0.01,60); tick[i:i+len(c)]+=c*0.3
    # heartbeat
    hb=np.zeros(len(x))
    for k in range(int(dur/0.9)):
        i=int(SR*k*0.9)
        for off in (0,0.18):
            j=i+int(SR*off); b=sine(50,0.12)*env_exp(0.12,18); hb[j:j+len(b)]+=b*0.5
    out=drone*rise+tick+hb*rise
    f=int(SR*0.4); out[:f]*=np.linspace(0,1,f); out[-f:]*=np.linspace(1,0,f)
    save('tension_loop', out)

# ----------------------------------------------------------------- VOICE
def whisper(name, seed):
    np.random.seed(seed); dur=1.3
    n=lp(noise(dur),0.08)  # breathy
    x=t(dur)
    # formant-ish wobble to suggest "come closer dearie"
    mod=(0.5+0.5*np.sin(2*np.pi*3.5*x))*(0.5+0.5*np.sin(2*np.pi*1.3*x+seed))
    syl=np.clip(np.sin(2*np.pi*1.6*x-0.5),0,1)  # syllable gating
    out=n*mod*syl*0.8
    out+=lp(noise(dur),0.02)*0.1
    out*=env_adsr(dur,0.1,0.2,0.8,0.3)
    save(name, out)

# ----------------------------------------------------------------- SFX
def shutter_slam():
    dur=0.45
    thud=sine(70,dur)*env_exp(dur,16)
    clang=(sine(430,dur)+sine(660,dur)*0.6+sine(910,dur)*0.4)*env_exp(dur,22)
    hit=noise(0.06)*env_exp(0.06,30)
    out=pad(np.concatenate([hit, np.zeros(0)]),dur)*0.0
    out=thud*0.8+clang*0.5
    out[:len(hit)]+=hit*0.7
    save('shutter_slam', out)

def shutter_open():
    dur=0.6; g=lp(noise(dur),0.02)*0.5
    metal=saw(120,dur)*0.15*env_adsr(dur,0.02,0.1,0.6,0.2)
    out=(g+metal)*env_adsr(dur,0.01,0.05,0.8,0.2)
    save('shutter_open', out)

def whir(name, up=True):
    dur=0.4; x=t(dur); f0,f1=(250,520) if up else (520,250)
    f=np.linspace(f0,f1,len(x)); ph=np.cumsum(2*np.pi*f/SR)
    out=np.sin(ph)*0.35*env_adsr(dur,0.02,0.05,0.8,0.1)
    out+=lp(noise(dur),0.05)*0.05
    save(name, out)

def cam_switch():
    dur=0.25; st=noise(dur)*env_exp(dur,10)*0.6
    pop=sine(140,0.04)*env_exp(0.04,30)
    out=st; out[:len(pop)]+=pop*0.6
    save('cam_switch', out)

def static_loop():
    dur=2.0; out=lp(noise(dur),0.4)*0.5
    f=int(SR*0.1); out[:f]*=np.linspace(0,1,f); out[-f:]*=np.linspace(1,0,f)
    save('static_loop', out)

def click(name, f=0.0):
    dur=0.06; out=noise(dur)*env_exp(dur,50)*0.6+sine(180,dur)*env_exp(dur,40)*0.3
    save(name, out)

def beep():
    dur=0.18; out=sine(1000,dur)*env_adsr(dur,0.005,0.02,0.8,0.05)*0.7
    save('battery_low_beep', out)

def pump_lever():
    dur=0.6
    yank=saw(90,0.12)*env_exp(0.12,12)*0.4
    hiss=lp(noise(dur),0.05)*np.concatenate([np.zeros(int(SR*0.12)), env_exp(dur-0.12,6)])*0.5
    squelch=sine(120,dur)*env_exp(dur,5)*0.2
    out=pad(yank,dur)+hiss+squelch
    save('pump_lever', out)

def footstep(name):
    dur=0.18; out=(lp(noise(dur),0.1)*0.5+sine(90,dur)*0.3)*env_exp(dur,22)
    save(name, out)

def heartbeat_loop():
    dur=1.0; out=np.zeros(int(SR*dur))
    for off in (0.0,0.22):
        i=int(SR*off); b=sine(48,0.14)*env_exp(0.14,16); out[i:i+len(b)]+=b
    save('heartbeat_loop', out*0.8)

def pickle_squelch():
    dur=0.3; x=t(dur)
    f=np.linspace(160,60,len(x)); ph=np.cumsum(2*np.pi*f/SR)
    out=np.sin(ph)*env_exp(dur,7)*0.6+lp(noise(dur),0.05)*env_exp(dur,10)*0.2
    save('pickle_squelch', out)

def clock_chime():
    dur=1.4; out=(sine(523.25,dur)*0.5+sine(1046.5,dur)*0.2+sine(1568,dur)*0.1)*env_exp(dur,3)
    out=reverb(out,0.3); save('clock_chime', out)

def bell_6am():
    dur=1.8
    out=(sine(659,dur)*0.5+sine(988,dur)*0.3+sine(1318,dur)*0.15)*env_exp(dur,2.2)
    out=reverb(out,0.35); save('bell_6am', out)

def win_jingle():
    notes=[523,659,784,1046,1318]; out=np.zeros(0)
    for i,f in enumerate(notes):
        d=0.18; seg=(sine(f,d)*0.5+sine(f*2,d)*0.15)*env_exp(d,6); out=np.concatenate([out,seg])
    out=np.concatenate([out,(sine(1046,0.5)*0.5)*env_exp(0.5,4)])
    out=reverb(out,0.25); save('win_jingle', out)

def game_over_sting():
    dur=1.2; x=t(dur)
    f=np.linspace(220,70,len(x)); ph=np.cumsum(2*np.pi*f/SR)
    out=np.sin(ph)*0.4*env_exp(dur,2)
    out+=np.sin(ph*1.5)*0.2*env_exp(dur,2)
    out+=lp(noise(dur),0.05)*0.1*env_exp(dur,3)
    save('game_over_sting', out)

def scream(name, base, rough, seed):
    np.random.seed(seed); dur=0.8; x=t(dur)
    vib=base*(1+0.12*np.sin(2*np.pi*22*x))*(1+np.linspace(0,0.4,len(x)))
    ph=np.cumsum(2*np.pi*vib/SR)
    tone=np.sin(ph)+0.5*np.sin(2*ph)+0.3*np.sin(3*ph)
    grit=noise(dur)*rough
    env=env_adsr(dur,0.02,0.1,0.85,0.25)
    out=(tone*0.6+grit)*env
    out=np.clip(out*1.6,-1,1)  # distortion/clip for nastiness
    save(name, out)

if __name__ == '__main__':
    menu_theme(); ambience_loop(); tension_loop()
    whisper('granny_whisper_left', 11); whisper('granny_whisper_right', 29)
    shutter_slam(); shutter_open(); whir('tablet_up', True); whir('tablet_down', False)
    cam_switch(); static_loop(); click('flashlight_toggle'); beep()
    pump_lever(); footstep('footstep_left'); footstep('footstep_right')
    heartbeat_loop(); click('button_click'); pickle_squelch()
    clock_chime(); bell_6am(); win_jingle(); game_over_sting()
    scream('js_pete', 180, 0.5, 1); scream('js_granny', 520, 0.45, 2)
    scream('js_twins', 700, 0.4, 3); scream('js_dill', 240, 0.7, 4)
    print('AUDIO DONE')
