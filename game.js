/* =====================================================================
   ONE NIGHT AT PICKLE PETE'S  —  engine (keyframe-static model)
   Original IP. Single-file engine; assets wired via assets/manifest.json.
   Missing assets fall back to generated placeholders so the game always runs.
   ===================================================================== */
'use strict';

const W = 1280, H = 720;
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const loadingEl = document.getElementById('loading');

/* ----------------------------- utilities --------------------------- */
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const rand = (a, b) => a + Math.random() * (b - a);
const chance = p => Math.random() < p;
const now = () => performance.now() / 1000;

/* ============================ AUDIO ENGINE ========================== */
/* WebAudio. Loads real files; synthesizes placeholders when missing.
   Supports stereo panning (Granny positional whispers).               */
class AudioEngine {
  constructor() {
    this.ctx = null;
    this.master = null;
    this.buffers = {};      // key -> AudioBuffer (real or synth)
    this.defs = {};         // key -> manifest def
    this.active = {};       // key -> {src, gain} for loops
    this.ready = false;
  }
  init() {
    if (this.ctx) return;
    const AC = window.AudioContext || window.webkitAudioContext;
    this.ctx = new AC();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0.9;
    this.master.connect(this.ctx.destination);
  }
  async load(defs) {
    this.defs = defs;
    const jobs = Object.entries(defs).map(async ([key, d]) => {
      try {
        const res = await fetch('assets/' + d.file);
        if (!res.ok) throw 0;
        const arr = await res.arrayBuffer();
        this.buffers[key] = await this.ctx.decodeAudioData(arr);
      } catch (e) {
        this.buffers[key] = this._synth(d.synth || 'beep', d);
      }
    });
    await Promise.all(jobs);
    this.ready = true;
  }
  resume() { if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume(); }

  play(key, opts = {}) {
    if (!this.ready || !this.buffers[key]) return null;
    const d = this.defs[key] || {};
    const src = this.ctx.createBufferSource();
    src.buffer = this.buffers[key];
    src.loop = !!d.loop;
    const g = this.ctx.createGain();
    g.gain.value = (opts.gain != null ? opts.gain : (d.gain != null ? d.gain : 1));
    let node = src;
    const panVal = opts.pan != null ? opts.pan : d.pan;
    if (panVal != null && this.ctx.createStereoPanner) {
      const p = this.ctx.createStereoPanner();
      p.pan.value = clamp(panVal, -1, 1);
      src.connect(p); p.connect(g);
    } else {
      src.connect(g);
    }
    g.connect(this.master);
    src.start();
    if (d.loop) { this.active[key] = { src, g }; }
    return { src, g };
  }
  stop(key) {
    const a = this.active[key];
    if (a) { try { a.src.stop(); } catch (e) {} delete this.active[key]; }
  }
  stopAll() { Object.keys(this.active).forEach(k => this.stop(k)); }

  /* -- placeholder synthesis: short procedural buffers per category -- */
  _synth(kind, d) {
    const sr = this.ctx.sampleRate;
    const dur = d.loop ? 2.0 : ({
      scream: 0.7, chime: 1.2, bell: 1.5, jingle: 1.4, sting: 1.0,
      slam: 0.25, whir: 0.4, whisper: 1.3, step: 0.18, click: 0.06,
      beep: 0.15, hiss: 0.5, squelch: 0.3, static: 1.0
    }[kind] || 0.4);
    const len = Math.floor(sr * dur);
    const buf = this.ctx.createBuffer(1, len, sr);
    const x = buf.getChannelData(0);
    const env = i => { const t = i / len; return Math.min(1, t * 20) * Math.pow(1 - t, 1.2); };
    for (let i = 0; i < len; i++) {
      const t = i / sr; let s = 0;
      switch (kind) {
        case 'scream': s = (Math.sin(2*Math.PI*(220+Math.sin(t*30)*120)*t) + (Math.random()*2-1)*0.6) * env(i); break;
        case 'whisper': s = (Math.random()*2-1) * 0.5 * (0.5+0.5*Math.sin(t*8)) * env(i); break;
        case 'static': s = (Math.random()*2-1) * 0.5; break;
        case 'hum': s = (Math.sin(2*Math.PI*60*t)*0.3 + (Math.random()*2-1)*0.05); break;
        case 'drone': s = (Math.sin(2*Math.PI*55*t)+Math.sin(2*Math.PI*82.4*t))*0.18; break;
        case 'heart': { const b = (t % 1); s = (b<0.12||(b>0.25&&b<0.34)) ? Math.sin(2*Math.PI*50*t)*0.6 : 0; break; }
        case 'slam': s = (Math.random()*2-1) * Math.pow(1-i/len, 4); break;
        case 'grind': s = ((Math.random()*2-1)*0.4 + Math.sin(2*Math.PI*90*t)*0.2) * env(i); break;
        case 'whir': s = Math.sin(2*Math.PI*(300+t*200)*t)*0.3*env(i); break;
        case 'click': s = (Math.random()*2-1)*Math.pow(1-i/len,8); break;
        case 'beep': s = Math.sin(2*Math.PI*880*t)*env(i); break;
        case 'hiss': s = (Math.random()*2-1)*0.4*env(i); break;
        case 'squelch': s = Math.sin(2*Math.PI*(120-t*80)*t)*0.5*env(i) + (Math.random()*2-1)*0.1; break;
        case 'step': s = (Math.random()*2-1)*0.5*Math.pow(1-i/len,3); break;
        case 'chime': s = Math.sin(2*Math.PI*523.25*t)*Math.exp(-t*3)*0.6; break;
        case 'bell': s = (Math.sin(2*Math.PI*659*t)+Math.sin(2*Math.PI*988*t))*Math.exp(-t*2)*0.4; break;
        case 'jingle': { const notes=[523,659,784,1046]; const n=notes[Math.floor(t/0.35)%notes.length]; s=Math.sin(2*Math.PI*n*t)*Math.exp(-(t%0.35)*5)*0.5; break; }
        case 'sting': s = Math.sin(2*Math.PI*(200-t*120)*t)*0.5*Math.pow(1-i/len,1.5) + (Math.random()*2-1)*0.1*env(i); break;
        case 'music': { const notes=[392,440,466,392]; const n=notes[Math.floor(t/0.5)%notes.length]; s=Math.sin(2*Math.PI*n*t)*0.18 + Math.sin(2*Math.PI*n*1.5*t)*0.06; break; }
        default: s = Math.sin(2*Math.PI*440*t)*env(i);
      }
      x[i] = clamp(s, -1, 1);
    }
    // smooth loop edges for looping buffers
    if (d.loop) { const f=Math.min(1000,len>>3); for(let i=0;i<f;i++){const k=i/f;x[i]*=k;x[len-1-i]*=k;} }
    return buf;
  }
}

/* ============================ ASSET MANAGER ========================= */
/* Loads images and sprite-sheet strips; generates labeled placeholders
   for any file that fails to load.                                     */
class Assets {
  constructor() { this.img = {}; this.strip = {}; this.manifest = null; }

  async loadAll(audio) {
    this.manifest = await fetch('assets/manifest.json').then(r => r.json());
    const imgJobs = Object.entries(this.manifest.images).map(([k, d]) => this._loadImage(k, d, false));
    const stripJobs = Object.entries(this.manifest.strips).map(([k, d]) => this._loadImage(k, d, true));
    await Promise.all([...imgJobs, ...stripJobs]);
    await audio.load(this.manifest.audio);
  }
  _loadImage(key, d, isStrip) {
    return new Promise(resolve => {
      const im = new Image();
      im.onload = () => {
        if (isStrip) {
          const fw = Math.floor(im.width / d.frames);
          this.strip[key] = { img: im, frames: d.frames, fps: d.fps, loop: d.loop, fw, fh: im.height, placeholder: false };
        } else { this.img[key] = { img: im, placeholder: false }; }
        resolve();
      };
      im.onerror = () => {
        if (isStrip) this.strip[key] = this._phStrip(key, d);
        else this.img[key] = { img: this._phImage(key, d), placeholder: true };
        resolve();
      };
      im.src = 'assets/' + d.file;
    });
  }
  _phImage(key, d) {
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const g = c.getContext('2d');
    const col = d.color || '#333';
    if (col.length > 7 || col.endsWith('00')) { g.clearRect(0,0,W,H); } // transparent-ish
    g.fillStyle = col; g.fillRect(0, 0, W, H);
    g.strokeStyle = 'rgba(143,174,75,0.5)'; g.lineWidth = 4; g.strokeRect(8,8,W-16,H-16);
    g.fillStyle = 'rgba(255,255,255,0.65)'; g.font = 'bold 34px Courier New'; g.textAlign = 'center';
    g.fillText('[' + key + ']', W/2, H/2);
    g.font = '18px Courier New'; g.fillText('placeholder', W/2, H/2 + 34);
    return c;
  }
  _phStrip(key, d) {
    const fw = 320, fh = 180, n = d.frames;
    const c = document.createElement('canvas'); c.width = fw * n; c.height = fh;
    const g = c.getContext('2d');
    for (let i = 0; i < n; i++) {
      const x = i * fw; const t = i / Math.max(1, n - 1);
      g.fillStyle = d.color || '#444'; g.fillRect(x, 0, fw, fh);
      g.fillStyle = `rgba(255,255,255,${0.15 + 0.6 * t})`; g.fillRect(x + 10, 10, fw - 20, fh - 20);
      g.fillStyle = '#000'; g.font = 'bold 22px Courier New'; g.textAlign = 'center';
      g.fillText(key, x + fw/2, fh/2 - 6); g.font = '16px Courier New';
      g.fillText('f' + (i+1) + '/' + n, x + fw/2, fh/2 + 18);
    }
    return { img: c, frames: n, fps: d.fps, loop: d.loop, fw, fh, placeholder: true };
  }
  drawImage(key, x=0, y=0, w=W, h=H) {
    const a = this.img[key]; if (!a) return;
    ctx.drawImage(a.img, x, y, w, h);
  }
  // draw a strip frame stretched to dest rect
  drawStripFrame(key, frame, x=0, y=0, w=W, h=H) {
    const s = this.strip[key]; if (!s) return;
    const f = clamp(frame|0, 0, s.frames - 1);
    ctx.drawImage(s.img, f * s.fw, 0, s.fw, s.fh, x, y, w, h);
  }
}

/* ============================ ANIMATION ============================= */
/* Plays a sprite-sheet strip frame-by-frame at its declared fps.       */
class StripPlayer {
  constructor(assets) { this.A = assets; this.key = null; this.t = 0; this.done = true; this.onEnd = null; }
  play(key, onEnd) {
    this.key = key; this.t = 0; this.done = false; this.onEnd = onEnd || null;
  }
  stop() { this.key = null; this.done = true; }
  update(dt) {
    if (this.done || !this.key) return;
    const s = this.A.strip[this.key]; if (!s) { this.done = true; return; }
    this.t += dt;
    const total = s.frames / s.fps;
    if (!s.loop && this.t >= total) { this.done = true; if (this.onEnd) this.onEnd(); }
  }
  curFrame() {
    const s = this.A.strip[this.key]; if (!s) return 0;
    let f = Math.floor(this.t * s.fps);
    if (s.loop) f %= s.frames; else f = clamp(f, 0, s.frames - 1);
    return f;
  }
  draw(x, y, w, h) { if (this.key) this.A.drawStripFrame(this.key, this.curFrame(), x, y, w, h); }
}

/* ============================ INPUT ================================= */
const Input = {
  keys: {}, mouse: { x: 0, y: 0, down: false, clicked: false },
  init() {
    addEventListener('keydown', e => { this.keys[e.code] = true; });
    addEventListener('keyup', e => { this.keys[e.code] = false; });
    canvas.addEventListener('mousemove', e => this._pos(e));
    canvas.addEventListener('mousedown', e => { this._pos(e); this.mouse.down = true; this.mouse.clicked = true; });
    addEventListener('mouseup', () => { this.mouse.down = false; });
    canvas.addEventListener('contextmenu', e => e.preventDefault());
    // touch
    canvas.addEventListener('touchstart', e => { this._pos(e.touches[0]); this.mouse.down = true; this.mouse.clicked = true; e.preventDefault(); }, {passive:false});
    canvas.addEventListener('touchmove', e => { this._pos(e.touches[0]); e.preventDefault(); }, {passive:false});
    canvas.addEventListener('touchend', () => { this.mouse.down = false; });
  },
  _pos(e) {
    const r = canvas.getBoundingClientRect();
    this.mouse.x = (e.clientX - r.left) * (W / r.width);
    this.mouse.y = (e.clientY - r.top) * (H / r.height);
  },
  pressed(code) { if (this.keys['_once_' + code]) return false; if (this.keys[code]) { this.keys['_once_' + code] = true; return true; } return false; },
  release(code) { if (!this.keys[code]) this.keys['_once_' + code] = false; },
  endFrame() { this.mouse.clicked = false; }
};
function hit(mx, my, x, y, w, h) { return mx >= x && mx <= x + w && my >= y && my <= y + h; }

/* ============================ GAME CONFIG =========================== */
const CAMERAS = ['cam_storage','cam_vats','cam_aisle','cam_backdoor','cam_lefthall','cam_righthall'];
const CAM_LABEL = { cam_storage:'CAM 1 STORAGE', cam_vats:'CAM 2 BRINE VATS', cam_aisle:'CAM 3 AISLE', cam_backdoor:'CAM 4 BACK DOOR', cam_lefthall:'CAM 5 LEFT HALL', cam_righthall:'CAM 6 RIGHT HALL' };
const HOUR_SECONDS = 60;           // real seconds per in-game hour
const START_HOUR = 12;             // 12 AM
const END_HOUR = 6;                // 6 AM (win)
const MAX_BATTERY = 100;

/* ============================ ANTAGONISTS =========================== */
/* Each is a small state machine. aiLevel scales with the hour.         */

class Pete {
  // Stalks: storage -> aisle -> lefthall -> LEFT WINDOW. Hates light.
  constructor(g){ this.g=g; this.path=['cam_storage','cam_aisle','cam_lefthall','LEFTWIN']; this.reset(); }
  reset(){ this.idx=0; this.moveT=rand(4,7); this.atWindowT=0; this.aiLevel=4; }
  get room(){ return this.path[this.idx]; }
  setLevel(h){ this.aiLevel = 4 + (h - START_HOUR + (h<START_HOUR?12:0)); } // ramps each hour
  update(dt,g){
    if (this.room==='LEFTWIN'){
      // at window: must close left shutter
      if (g.shutterLeft.closed){ this.idx=0; this.moveT=rand(5,8); this.atWindowT=0; g.audio.play('footstep_left'); return; }
      this.atWindowT += dt;
      if (this.atWindowT>6) g.trigger('js_pete','pete');
      return;
    }
    this.moveT -= dt;
    if (this.moveT<=0){
      this.moveT = rand(4.5,7.5) * clamp(1 - this.aiLevel*0.02, 0.4, 1);
      // light deterrent: if player is viewing Pete's room with flashlight on, send back
      if (g.tabletUp && g.currentCam===this.room && g.flashlight && this.idx>0){
        this.idx--; g.audio.play('footstep_right'); return;
      }
      if (chance(this.aiLevel/20)) { this.idx++; g.audio.play('footstep_left'); }
    }
  }
  drawOnCam(g){ if (this.room===g.currentCam) g.A.drawImage('pete_'+this.room.replace('cam_',''), 0,0,W,H); }
  atLeftWindow(){ return this.room==='LEFTWIN'; }
}

class Granny {
  // AUDIO ONLY. Picks a side, whispers from that speaker, then attacks it.
  constructor(g){ this.g=g; this.reset(); }
  reset(){ this.state='idle'; this.timer=rand(12,20); this.side=null; this.warn=0; this.aiLevel=3; }
  setLevel(h){ this.aiLevel = 3 + (h - START_HOUR + (h<START_HOUR?12:0)); }
  update(dt,g){
    this.timer-=dt;
    if (this.state==='idle' && this.timer<=0){
      this.side = chance(0.5)?'left':'right';
      this.state='whisper'; this.warn = clamp(5 - this.aiLevel*0.15, 2.2, 5);
      g.audio.play(this.side==='left'?'granny_whisper_left':'granny_whisper_right');
      this.whisperT=0;
    } else if (this.state==='whisper'){
      this.warn-=dt; this.whisperT=(this.whisperT||0)+dt;
      if (this.whisperT>1.3){ this.whisperT=0; g.audio.play(this.side==='left'?'granny_whisper_left':'granny_whisper_right'); }
      if (this.warn<=0){ this.state='attack'; this.attackT=1.2; }
    } else if (this.state==='attack'){
      const sh = this.side==='left'?g.shutterLeft:g.shutterRight;
      if (sh.closed){ this._retreat(g); return; }
      this.attackT-=dt;
      if (this.attackT<=0) g.trigger('js_granny','granny');
    }
  }
  _retreat(g){ this.state='idle'; this.timer=rand(10,18); this.side=null; }
}

class SourTwins {
  // Drain battery 3x when active; approach via right side; pump lever repels.
  constructor(g){ this.g=g; this.reset(); }
  reset(){ this.path=['cam_backdoor','cam_aisle','cam_righthall','RIGHTWIN']; this.idx=-1; this.moveT=rand(10,16); this.aiLevel=3; this.attackT=0; }
  get room(){ return this.idx<0?null:this.path[this.idx]; }
  get active(){ return this.idx>=0; }
  setLevel(h){ this.aiLevel = 3 + (h - START_HOUR + (h<START_HOUR?12:0)); }
  update(dt,g){
    if (this.idx<0){ this.moveT-=dt; if (this.moveT<=0){ this.idx=0; g.audio.play('pickle_squelch'); } return; }
    if (this.room==='RIGHTWIN'){
      if (g.shutterRight.closed){ this.idx=-1; this.moveT=rand(12,18); return; }
      this.attackT+=dt; if (this.attackT>5) g.trigger('js_twins','twins');
      return;
    }
    this.moveT-=dt;
    if (this.moveT<=0){
      this.moveT=rand(5,8)*clamp(1-this.aiLevel*0.02,0.4,1);
      // flashlight ON near them slows; pump handled via repel()
      if (chance(this.aiLevel/22)) { this.idx++; g.audio.play('pickle_squelch'); }
    }
  }
  repel(g){ if (this.idx>=0){ this.idx=-1; this.moveT=rand(14,20); this.attackT=0; g.audio.play('pump_lever'); return true; } return false; }
  drawOnCam(g){ const r=this.room; if (r && r!=='RIGHTWIN' && r===g.currentCam) g.A.drawImage('sourtwins_'+r.replace('cam_',''),0,0,W,H); }
}

class DillLord {
  // Hijacks the camera feed with static; player must REBOOT (hold R / button).
  constructor(g){ this.g=g; this.reset(); }
  reset(){ this.state='idle'; this.timer=rand(20,30); this.hijackT=0; this.reboot=0; this.aiLevel=2; }
  setLevel(h){ this.aiLevel = 2 + Math.floor((h - START_HOUR + (h<START_HOUR?12:0))/1.5); }
  get hijacking(){ return this.state==='hijack'; }
  update(dt,g){
    this.timer-=dt;
    if (this.state==='idle' && this.timer<=0 && chance(0.6)){
      this.state='hijack'; this.hijackT = clamp(8 - this.aiLevel*0.4, 4, 8); this.reboot=0;
      g.audio.play('static_loop');
    } else if (this.state==='hijack'){
      this.hijackT-=dt;
      // hold R or reboot button to clear
      if (g.rebootHeld){ this.reboot += dt; if (this.reboot>2.0){ this._clear(g); return; } }
      else this.reboot = Math.max(0, this.reboot - dt*0.5);
      if (this.hijackT<=0) g.trigger('js_dill','dill');
    }
  }
  _clear(g){ this.state='idle'; this.timer=rand(22,34); g.audio.stop('static_loop'); g.audio.play('cam_switch'); }
}

/* ============================ MAIN GAME ============================= */
class Game {
  constructor(){
    this.A = new Assets();
    this.audio = new AudioEngine();
    this.strip = null;        // StripPlayer (set after assets)
    this.state = 'BOOT';      // BOOT, MENU, INTRO, PLAY, JUMPSCARE, GAMEOVER, WIN
    this.last = now();
  }
  async boot(){
    this.audio.init();
    await this.A.loadAll(this.audio);
    this.strip = new StripPlayer(this.A);
    loadingEl.style.display = 'none';
    this.state = 'MENU';
    this.audio.play('menu_theme');
    requestAnimationFrame(() => this.loop());
  }

  startNight(){
    this.audio.stopAll();
    this.hour = START_HOUR; this.hourT = 0;
    this.battery = MAX_BATTERY;
    this.flashlight = false;
    this.tabletUp = false; this.tabletAnimT = 0; this.tabletDir = 0;
    this.currentCam = 'cam_storage';
    this.camSwitchT = 0;
    this.rebootHeld = false;
    this.shutterLeft = this._mkShutter('left');
    this.shutterRight = this._mkShutter('right');
    this.leverT = 0;
    this.pete = new Pete(this); this.pete.reset();
    this.granny = new Granny(this); this.granny.reset();
    this.twins = new SourTwins(this); this.twins.reset();
    this.dill = new DillLord(this); this.dill.reset();
    this._applyHour();
    this.audio.play('ambience_loop');
    this.audio.play('heartbeat_loop', { gain: 0.0 });
    this.deathBy = null;
    this.state = 'INTRO'; this.introT = 0;
    this.strip.play('night_card');
  }
  _mkShutter(side){ return { side, closed:false, anim:0, dir:0 }; }
  _applyHour(){
    [this.pete,this.granny,this.twins,this.dill].forEach(a=>a.setLevel(this.hour));
    if (this.hour>=4 || this.hour===START_HOUR+0) { /* tension later */ }
  }

  trigger(jsKey, who){
    if (this.state!=='PLAY') return;
    this.state='JUMPSCARE'; this.deathBy=who;
    this.audio.stopAll();
    this.audio.play(jsKey);   // jsKey doubles as the scream audio key (e.g. js_pete)
    this.strip.play(jsKey, () => { this.state='GAMEOVER'; this.goT=0; this.strip.play('gameover'); this.audio.play('game_over_sting'); });
  }

  win(){
    this.state='WIN'; this.winT=0; this.audio.stopAll();
    this.audio.play('bell_6am'); this.audio.play('win_jingle');
    this.strip.play('win_6am');
  }

  /* ----------------------------- update ---------------------------- */
  update(dt){
    Input.release('Space'); Input.release('KeyF'); Input.release('KeyA'); Input.release('KeyD'); Input.release('KeyE'); Input.release('Enter');
    this.strip.update(dt);

    if (this.state==='MENU'){
      this.titleT=(this.titleT||0)+dt;
      if (Input.mouse.clicked || Input.pressed('Enter') || Input.pressed('Space')){ this.audio.resume(); this.startNight(); }
      return;
    }
    if (this.state==='INTRO'){
      this.introT+=dt;
      if (this.introT>2.6){ this.state='PLAY'; this.audio.play('clock_chime'); }
      return;
    }
    if (this.state==='JUMPSCARE'){ return; }
    if (this.state==='GAMEOVER'){
      this.goT=(this.goT||0)+dt;
      if (this.goT>2.5 && (Input.mouse.clicked || Input.pressed('Enter'))){ this.state='MENU'; this.audio.stopAll(); this.audio.play('menu_theme'); }
      return;
    }
    if (this.state==='WIN'){
      this.winT+=dt;
      if (this.winT>5 && (Input.mouse.clicked || Input.pressed('Enter'))){ this.state='MENU'; this.audio.stopAll(); this.audio.play('menu_theme'); }
      return;
    }

    /* ---------------------- PLAY state ---------------------- */
    // clock
    this.hourT += dt;
    if (this.hourT >= HOUR_SECONDS){
      this.hourT -= HOUR_SECONDS;
      this.hour = (this.hour % 12) + 1; // 12 -> 1 -> 2 ...
      this.audio.play('clock_chime');
      this._applyHour();
      if (this.hour === END_HOUR){ this.win(); return; }
    }

    this._handleInput(dt);
    this._updateShutter(this.shutterLeft, dt);
    this._updateShutter(this.shutterRight, dt);

    // tablet flip animation
    if (this.tabletDir!==0){
      this.tabletAnimT += dt * this.tabletDir;
      if (this.tabletAnimT>=1){ this.tabletAnimT=1; this.tabletDir=0; this.tabletUp=true; }
      if (this.tabletAnimT<=0){ this.tabletAnimT=0; this.tabletDir=0; this.tabletUp=false; }
    }
    if (this.camSwitchT>0) this.camSwitchT -= dt;
    if (this.leverT>0) this.leverT -= dt;

    // battery drain
    let drain = 0.6;                          // base idle drain per sec
    if (this.flashlight) drain += 2.2;
    if (this.tabletUp) drain += 2.0;
    if (this.shutterLeft.closed) drain += 1.4;
    if (this.shutterRight.closed) drain += 1.4;
    if (this.rebootHeld) drain += 1.5;
    if (this.twins.active) drain *= 3.0;       // Sour Twins triple drain
    this.battery = clamp(this.battery - drain*dt, 0, MAX_BATTERY);
    if (this.battery<=0) { this._powerOut(dt); }
    if (this.battery<20 && !this._lowBeepT){ this._lowBeepT=0; }
    if (this.battery<20){ this._lowBeepT-=dt; if (this._lowBeepT<=0){ this._lowBeepT=1.2; this.audio.play('battery_low_beep'); } }

    // antagonists
    this.rebootHeld = (this.tabletUp && this.dill.hijacking && (Input.keys['KeyR'] || this._rebootBtnDown));
    this.pete.update(dt,this);
    this.granny.update(dt,this);
    this.twins.update(dt,this);
    this.dill.update(dt,this);

    // dynamic heartbeat by danger
    const danger = (this.pete.atLeftWindow()?1:0) + (this.granny.state==='attack'?1:0) + (this.twins.room==='RIGHTWIN'?1:0) + (this.dill.hijacking?1:0);
    if (this.audio.active['heartbeat_loop']) this.audio.active['heartbeat_loop'].g.gain.value = clamp(danger*0.35,0,0.7);
  }

  _powerOut(dt){
    // out of power: shutters forced open, flashlight dead — Pete closes in
    this.flashlight=false; this.shutterLeft.closed=false; this.shutterRight.closed=false;
    this._blackoutT=(this._blackoutT||0)+dt;
    if (this._blackoutT>rand(3,3)) { this.pete.idx=this.pete.path.length-1; this.pete.atWindowT=99; this.trigger('js_pete','pete'); }
  }

  _handleInput(dt){
    const m = Input.mouse;
    // keyboard
    if (Input.pressed('KeyF')) this.toggleFlash();
    if (Input.pressed('Space')) this.toggleTablet();
    if (Input.pressed('KeyA')) this.toggleShutter(this.shutterLeft);
    if (Input.pressed('KeyD')) this.toggleShutter(this.shutterRight);
    if (Input.pressed('KeyE')) this.pullLever();
    this._rebootBtnDown = false;

    if (!m.clicked && !m.down) return;
    if (this.tabletUp){
      // camera select strip along bottom
      const n=CAMERAS.length, bw=160, gap=8, total=n*bw+(n-1)*gap, x0=(W-total)/2, y=H-70;
      for (let i=0;i<n;i++){ const x=x0+i*(bw+gap); if (m.clicked && hit(m.x,m.y,x,y,bw,46)) this.switchCam(CAMERAS[i]); }
      // reboot button (only meaningful during hijack)
      if (hit(m.x,m.y,W-220,20,200,50)) { this._rebootBtnDown = true; }
      // lower tablet button
      if (m.clicked && hit(m.x,m.y,20,20,160,50)) this.toggleTablet();
    } else {
      // office: click left/right thirds to shutter, center-bottom flashlight, lever
      if (m.clicked){
        if (hit(m.x,m.y,0,80,300,520)) this.toggleShutter(this.shutterLeft);
        else if (hit(m.x,m.y,W-300,80,300,520)) this.toggleShutter(this.shutterRight);
        else if (hit(m.x,m.y,W/2-90,H-80,180,60)) this.toggleTablet();
        else if (hit(m.x,m.y,W/2-260,H-80,150,60)) this.toggleFlash();
        else if (hit(m.x,m.y,W/2+110,H-80,150,60)) this.pullLever();
      }
    }
  }
  toggleFlash(){ if (this.battery<=0) return; this.flashlight=!this.flashlight; this.audio.play('flashlight_toggle'); }
  toggleTablet(){
    if (this.tabletDir!==0) return;
    if (this.tabletUp){ this.tabletDir=-1; this.audio.play('tablet_down'); this.strip.play('tablet_flip_up'); }
    else { this.tabletDir=1; this.audio.play('tablet_up'); this.strip.play('tablet_flip_up'); }
  }
  switchCam(key){ if (key===this.currentCam) return; this.currentCam=key; this.camSwitchT=0.18; this.strip.play('cam_switch'); this.audio.play('cam_switch'); }
  toggleShutter(sh){ if (this.battery<=0 && !sh.closed) return; sh.dir = sh.closed?-1:1; this.audio.play(sh.closed?'shutter_open':'shutter_slam'); }
  _updateShutter(sh,dt){ if (sh.dir!==0){ sh.anim+=dt*sh.dir*4; if (sh.anim>=1){sh.anim=1;sh.dir=0;sh.closed=true;} if (sh.anim<=0){sh.anim=0;sh.dir=0;sh.closed=false;} } }
  pullLever(){ if (this.leverT>0) return; this.leverT=0.6; this.strip.play('pump_lever'); const r=this.twins.repel(this); if(!r) this.audio.play('pump_lever'); }

  /* ----------------------------- render ---------------------------- */
  render(){
    ctx.clearRect(0,0,W,H);
    switch(this.state){
      case 'MENU': this._renderMenu(); break;
      case 'INTRO': this._renderOffice(); this._renderIntro(); break;
      case 'PLAY': this.tabletUp && this.tabletDir===0 ? this._renderTablet() : (this.tabletDir!==0 ? this._renderFlip() : this._renderOffice()); this._renderHUD(); break;
      case 'JUMPSCARE': this._renderJumpscare(); break;
      case 'GAMEOVER': this._renderGameover(); break;
      case 'WIN': this._renderWin(); break;
      default: break;
    }
  }
  _renderMenu(){
    this.A.drawStripFrame('title_bg', Math.floor((this.titleT||0)*8)%this.A.strip['title_bg'].frames, 0,0,W,H);
    this.A.drawImage('logo', W/2-400, 90, 800, 240);
    ctx.textAlign='center';
    const blink = (Math.sin((this.titleT||0)*3)>0);
    if (blink){ ctx.font='28px Courier New'; ctx.fillStyle='#8fae4b'; ctx.fillText('CLICK / ENTER TO START SHIFT', W/2, 520); }
    ctx.font='16px Courier New'; ctx.fillStyle='rgba(207,227,154,0.6)';
    ctx.fillText('Survive 12 AM \u2192 6 AM. Watch the windows. Mind the brine.', W/2, 600);
  }
  _renderIntro(){
    this.strip.draw(0,0,W,H);
    ctx.fillStyle='#cfe39a'; ctx.textAlign='center'; ctx.font='bold 90px Courier New';
    const a = clamp(1 - Math.abs(this.introT-1.3)/1.3,0,1); ctx.globalAlpha=a;
    ctx.fillText('12 AM', W/2, H/2); ctx.globalAlpha=1;
  }
  _renderOffice(){
    // animated idle if present else static base
    if (this.A.strip['office_idle']) this.A.drawStripFrame('office_idle', Math.floor((now()*8))%this.A.strip['office_idle'].frames,0,0,W,H);
    else this.A.drawImage('office_base');
    // windows (open base, occupant peek, shutter overlay)
    this._renderWindow('left');
    this._renderWindow('right');
    // flashlight darkness overlay
    if (!this.flashlight){ ctx.fillStyle='rgba(0,0,0,0.55)'; ctx.fillRect(0,0,W,H); }
    else { const grd=ctx.createRadialGradient(W/2,H/2,80,W/2,H/2,640); grd.addColorStop(0,'rgba(255,255,220,0.12)'); grd.addColorStop(1,'rgba(0,0,0,0.45)'); ctx.fillStyle=grd; ctx.fillRect(0,0,W,H); }
    // office buttons
    this._btn(W/2-90,H-80,180,60,'TABLET');
    this._btn(W/2-260,H-80,150,60, this.flashlight?'LIGHT*':'LIGHT');
    this._btn(W/2+110,H-80,150,60,'PUMP');
  }
  _renderWindow(side){
    const sh = side==='left'?this.shutterLeft:this.shutterRight;
    const x = side==='left'?0:W-300, w=300;
    this.A.drawImage('window_'+side+'_open', x, 80, w, 520);
    // occupant peek when present and shutter open
    const petePeek = side==='left' && this.pete.atLeftWindow();
    const grannyPeek = (this.granny.state==='attack' && this.granny.side===side);
    const twinPeek = side==='right' && this.twins.room==='RIGHTWIN';
    if ((petePeek||twinPeek) && sh.anim<0.5){ this.A.drawImage('window_'+side+'_full', x, 80, w, 520); }
    if (grannyPeek && sh.anim<0.5 && this.flashlight){ ctx.fillStyle='rgba(120,150,60,0.4)'; ctx.fillRect(x,80,w,520); }
    // shutter strip drawn by anim progress (frame index from anim 0..1)
    if (sh.anim>0){ const key='shutter_'+side; const s=this.A.strip[key]; const f=Math.floor(sh.anim*(s.frames-1)); this.A.drawStripFrame(key,f,x,80,w,520); }
    // label
    ctx.fillStyle='rgba(0,0,0,0.4)'; ctx.fillRect(x,80,w,26); ctx.fillStyle='#9bbf5a'; ctx.font='16px Courier New'; ctx.textAlign='center';
    ctx.fillText(side.toUpperCase()+' WINDOW'+(sh.closed?' [SEALED]':''), x+w/2, 99);
  }
  _renderFlip(){
    this._renderOffice();
    const f = this.strip.curFrame ? this.strip.curFrame() : 0;
    this.A.drawStripFrame('tablet_flip_up', Math.floor(this.tabletAnimT*(this.A.strip['tablet_flip_up'].frames-1)),0,0,W,H);
  }
  _renderTablet(){
    ctx.fillStyle='#05080a'; ctx.fillRect(0,0,W,H);
    // feed
    if (this.dill.hijacking){
      this.A.drawStripFrame('dill_static_loop', Math.floor(now()*15)%this.A.strip['dill_static_loop'].frames,40,40,W-80,H-160);
      this.A.drawImage('dilllord_pose', W/2-200, 120, 400, 360);
      ctx.fillStyle='#d44'; ctx.font='bold 40px Courier New'; ctx.textAlign='center';
      ctx.fillText('SIGNAL HIJACKED', W/2, 90);
      ctx.font='22px Courier New'; ctx.fillStyle='#fbb';
      ctx.fillText('HOLD [R] / REBOOT BUTTON', W/2, H-120);
      // reboot progress
      const p=clamp(this.dill.reboot/2,0,1); ctx.fillStyle='#222'; ctx.fillRect(W/2-200,H-110,400,16); ctx.fillStyle='#8fae4b'; ctx.fillRect(W/2-200,H-110,400*p,16);
      this._btn(W-220,20,200,50,'REBOOT', this._rebootBtnDown);
    } else if (this.camSwitchT>0){
      this.A.drawStripFrame('cam_switch', Math.floor((0.18-this.camSwitchT)/0.18*3),40,40,W-80,H-160);
    } else {
      this.A.drawImage(this.currentCam, 40,40,W-80,H-160);
      this.pete.drawOnCam(this); this.twins.drawOnCam(this);
      // scanlines
      this.A.drawImage('scanlines_overlay',40,40,W-80,H-160);
      ctx.fillStyle='#9bbf5a'; ctx.font='bold 24px Courier New'; ctx.textAlign='left';
      ctx.fillText(CAM_LABEL[this.currentCam], 60, 78);
      const rec=(Math.floor(now()*2)%2===0); if(rec){ctx.fillStyle='#d44';ctx.beginPath();ctx.arc(W-90,68,9,0,7);ctx.fill();ctx.fillStyle='#fbb';ctx.font='16px Courier New';ctx.fillText('REC',W-70,73);}
    }
    // tablet frame overlay + camera buttons
    this.A.drawImage('tablet_frame',0,0,W,H);
    this._btn(20,20,160,50,'LOWER');
    const n=CAMERAS.length, bw=160, gap=8, total=n*bw+(n-1)*gap, x0=(W-total)/2, y=H-70;
    for (let i=0;i<n;i++){ const x=x0+i*(bw+gap); this._btn(x,y,bw,46, CAM_LABEL[CAMERAS[i]].split(' ')[1]+' '+CAMERAS[i].replace('cam_',''), this.currentCam===CAMERAS[i]); }
  }
  _renderHUD(){
    // clock
    ctx.textAlign='right'; ctx.font='bold 40px Courier New'; ctx.fillStyle='#cfe39a';
    ctx.fillText(this.hour+' AM', W-30, 50);
    // battery
    const bx=30,by=24,bw=200,bh=26; ctx.strokeStyle='#9bbf5a'; ctx.lineWidth=3; ctx.strokeRect(bx,by,bw,bh);
    const col = this.battery>40?'#8fae4b':(this.battery>20?'#d8d44a':'#d44');
    ctx.fillStyle=col; ctx.fillRect(bx+3,by+3,(bw-6)*this.battery/100,bh-6);
    ctx.fillStyle='#cfe39a'; ctx.font='14px Courier New'; ctx.textAlign='left'; ctx.fillText('POWER '+Math.ceil(this.battery)+'%', bx, by+bh+16);
    // low battery overlay
    if (this.battery<20){ const a=0.25+0.2*Math.sin(now()*8); ctx.fillStyle='rgba(170,0,0,'+a+')'; ctx.fillRect(0,0,W,H); }
    // twins drain warning
    if (this.twins.active){ ctx.fillStyle='#d8d44a'; ctx.font='16px Courier New'; ctx.textAlign='center'; ctx.fillText('!! POWER DRAIN — SOUR TWINS ACTIVE — PUMP [E] !!', W/2, 40); }
  }
  _btn(x,y,w,h,label,active){
    ctx.fillStyle=active?'rgba(143,174,75,0.85)':'rgba(20,33,15,0.85)';
    ctx.fillRect(x,y,w,h); ctx.strokeStyle='#8fae4b'; ctx.lineWidth=2; ctx.strokeRect(x,y,w,h);
    ctx.fillStyle=active?'#0c1407':'#cfe39a'; ctx.font='bold 18px Courier New'; ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(label, x+w/2, y+h/2); ctx.textBaseline='alphabetic';
  }
  _renderJumpscare(){
    const key = 'js_'+this.deathBy;
    ctx.fillStyle='#000'; ctx.fillRect(0,0,W,H);
    this.strip.draw(0,0,W,H);
    // shake
    if (chance(0.5)){ /* visual jitter via redraw offset omitted for simplicity */ }
  }
  _renderGameover(){
    this.strip.draw(0,0,W,H);
    ctx.fillStyle='#d44'; ctx.font='bold 80px Courier New'; ctx.textAlign='center'; ctx.fillText('SHIFT OVER', W/2, H/2);
    if (this.goT>2.5){ ctx.fillStyle='#cfe39a'; ctx.font='24px Courier New'; ctx.fillText('click to return', W/2, H/2+70); }
  }
  _renderWin(){
    this.strip.draw(0,0,W,H);
    ctx.fillStyle='#ffe9a8'; ctx.font='bold 90px Courier New'; ctx.textAlign='center'; ctx.fillText('6 AM', W/2, H/2);
    ctx.font='30px Courier New'; ctx.fillStyle='#cfe39a'; ctx.fillText('YOU SURVIVED THE NIGHT', W/2, H/2+70);
    if (this.winT>5){ ctx.font='22px Courier New'; ctx.fillText('click to return', W/2, H/2+120); }
  }

  /* ----------------------------- loop ------------------------------ */
  loop(){
    const t = now(); let dt = t - this.last; this.last = t; if (dt>0.1) dt=0.1;
    this.update(dt);
    this.render();
    Input.endFrame();
    requestAnimationFrame(() => this.loop());
  }
}

/* ============================ BOOTSTRAP ============================= */
Input.init();
const game = new Game();
// first user gesture resumes audio context
function firstGesture(){ game.audio.resume(); removeEventListener('pointerdown', firstGesture); removeEventListener('keydown', firstGesture); }
addEventListener('pointerdown', firstGesture);
addEventListener('keydown', firstGesture);
game.boot().catch(err => { loadingEl.textContent = 'LOAD ERROR: ' + err; console.error(err); });
