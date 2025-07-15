/* ---------- 常量段长参数 (vh) ---------- */
const LEN_HERO = 0.1;  // 首屏拉长
      LEN_B1   = 0.8;  // 黑幕 1
      LEN_H    = 2.2;  // 第二屏横滑
      LEN_B2   = 0.8;  // 黑幕 2
      LEN_MID  = 1.8;  // ★ 新 GIF 屏停留
      LEN_B3   = 0.8;  // 黑幕 3
      LEN_T3   = 1.8;  // 第三屏停留
      LEN_F    = 0.8;  // after 淡入
      SMOOTH   = 0.5;
/* -------------------------------------- */

/* ---------- 元素缓存 ---------- */
const heroEl   = document.getElementById('screen0');
const black1El = document.getElementById('black');
const secHEl   = document.getElementById('screen1');
const black2El = document.getElementById('black2');
const midEl    = document.getElementById('screen2Mid');  // ★
const black3El = document.getElementById('black3');      // ★
const thirdEl  = document.getElementById('screen3');
const afterEl  = document.getElementById('screen2');
const boxEl    = document.getElementById('scroller');

const video2El = document.getElementById('bgVideo');   // 二屏循环
const video3El = document.getElementById('bgVideo3');  // 三屏滚动驱动
const line3El  = document.getElementById('heroLine');
const midLineEl= document.getElementById('midLine');   // ★
/* ----------------------------- */

/* ---------- 绝对分段坐标 ---------- */
let vh=0,totalX=0,easedY=0;
let endHero,endB1,endH,endB2,endMid,endB3,endT3,endFade;
/* -------------------------------- */

function layout(){
  vh = innerHeight;
  requestAnimationFrame(()=>{
    totalX  = boxEl.scrollWidth - innerWidth;

    endHero = LEN_HERO*vh;
    endB1   = endHero + LEN_B1*vh;
    endH    = endB1   + LEN_H  *vh;
    endB2   = endH    + LEN_B2 *vh;
    endMid  = endB2   + LEN_MID*vh;   // ★
    endB3   = endMid  + LEN_B3 *vh;   // ★
    endT3   = endB3   + LEN_T3 *vh;
    endFade = endT3   + LEN_F  *vh;

    document.body.style.height = `${(endFade/vh+1)*vh}px`;
  });
}

/* ---------- 黑幕转场阈值 ---------- */
const CUT1 = 0.49, CUT2 = 0.51;
/* --------------------------------- */

/* ---------- 二屏循环视频控制 ---------- */
let playing2=false;
function playV2(){ if(!playing2){ video2El.play(); playing2=true } }
function stopV2(reset=true){ if(playing2){ video2El.pause(); playing2=false; if(reset) video2El.currentTime=0 } }
/* ------------------------------------- */

/* ---------- 三屏视频 duration ---------- */
let v3Dur = 1;
video3El.addEventListener('loadedmetadata',()=> v3Dur = video3El.duration);
/* -------------------------------------- */

/* ============ 主动画 ============ */
function update(y){
  /* ① 首屏 */
  if(y < endHero){
    heroEl.classList.add('active');
    [black1El,secHEl,black2El,midEl,black3El,thirdEl,afterEl].forEach(el=>el.classList.remove('active'));
    heroEl.style.opacity = 1;
    [black1El,secHEl,black2El,midEl,black3El,thirdEl,afterEl].forEach(el=>el.style.opacity=0);
    boxEl.style.transform='translateX(0)';
    stopV2(); video3El.currentTime = 0;
    return;
  }

  /* ② 黑幕 1 */
  if(y < endB1){
    heroEl.classList.remove('active'); black1El.classList.add('active');
    const t=(y-endHero)/(LEN_B1*vh);
    if(t<CUT1){
      heroEl .style.opacity = 1 - t/CUT1;
      black1El.style.opacity = t/CUT1;
    }else if(t<CUT2){
      heroEl .style.opacity = 0;
      black1El.style.opacity = 1;
    }else{
      const p=(t-CUT2)/(1-CUT2);
      black1El.style.opacity = 1 - p;
      secHEl  .style.opacity = p;
    }
    stopV2(); video3El.currentTime = 0;
    return;
  }

  /* ③ 第二屏横滑 */
  if(y < endH){ 
    /* 先清空其它 screen 的 active，以防挡点击 */
  [
        heroEl, black1El, black2El,
        midEl,  black3El, thirdEl, afterEl
      ].forEach(el => el.classList.remove('active'));
    
      /* 然后只给第二屏加 active */
      secHEl.classList.add('active');
    const p=(y-endB1)/(LEN_H*vh); 
    boxEl.style.transform=`translateX(${-totalX*p}px)`;
    heroEl.style.opacity=0; black1El.style.opacity=0;
    [black2El,midEl,black3El,thirdEl,afterEl].forEach(el=>el.style.opacity=0);
    playV2(); video3El.currentTime = 0;
    return;
  }

  /* ④ 黑幕 2 */
  if(y < endB2){
    secHEl.classList.remove('active'); black2El.classList.add('active');
    const t=(y-endH)/(LEN_B2*vh);
    if(t<CUT1){
      const p=t/CUT1;
      secHEl .style.opacity = 1 - p;
      black2El.style.opacity = p;
    }else if(t<CUT2){
      secHEl .style.opacity = 0;
      black2El.style.opacity = 1;
    }else{
      const p=(t-CUT2)/(1-CUT2);
      black2El.style.opacity = 1 - p;
      midEl   .style.opacity = p;
    }
    stopV2(false); video3El.currentTime = 0;
    return;
  }

  /* ⑤ GIF 中间屏 */
  if(y < endMid){
    black2El.classList.remove('active'); midEl.classList.add('active');
    midEl.style.opacity = 1;
    /* 文本从下往上匀速浮现（右侧） */
    const p=(y-endB2)/(LEN_MID*vh);    // 0→1
    const startY = 10;  // vh
    const endY   = -120; // vh
    const curY   = startY + (endY-startY)*p;
    midLineEl.style.transform = `translateY(${curY}vh)`;
    /* 其他元素隐藏 */
    [black3El,thirdEl,afterEl].forEach(el=>el.style.opacity=0);
    return;
  }

  /* ⑥ 黑幕 3 */
  if(y < endB3){
    midEl.classList.remove('active'); black3El.classList.add('active');
    const t=(y-endMid)/(LEN_B3*vh);
    if(t<CUT1){
      const p=t/CUT1;
      midEl  .style.opacity = 1 - p;
      black3El.style.opacity = p;
    }else if(t<CUT2){
      midEl  .style.opacity = 0;
      black3El.style.opacity = 1;
    }else{
      const p=(t-CUT2)/(1-CUT2);
      black3El.style.opacity = 1 - p;
      thirdEl .style.opacity = p;
    }
    video3El.currentTime = 0;
    return;
  }

  /* ⑦ + ⑧ 统一：第三屏播放 & 淡出 */
  if (y < endFade) {
    /* --- 视频插值 --- */
    const pAll   = (y - endB3) / (endFade - endB3);   // 0 → 1
    const target = pAll * v3Dur;
    const diff   = target - video3El.currentTime;
    if (Math.abs(diff) > 0.4){
      const ALPHA = Math.min(1, 0.25 + Math.abs(diff) * 2);
      video3El.currentTime += diff * ALPHA;
    }else{
      video3El.currentTime = target;
    }

    /* --- 文字位移 --- */
    const startY = 40;
    const endY   = -120;
    const yNow   = startY + (endY - startY) * pAll;
    line3El.style.transform = `translateY(${yNow}vh)`;

    /* --- 可见性 --- */
    thirdEl.classList.add('active');
    boxEl.style.transform = `translateX(${-totalX}px)`;
    if (y < endT3) {     // 停留段
      thirdEl.style.opacity = 1; afterEl.style.opacity = 0;
      black3El.classList.remove('active');
    } else {             // 淡出段
      const f = (y - endT3) / (LEN_F*vh);
      thirdEl.style.opacity = 1 - f; afterEl.style.opacity = f;
      afterEl.classList.add('active');
    }
    return;
  }

  /* ⑨ after 完整 */
  afterEl.classList.add('active');
  [thirdEl].forEach(el=>el.classList.remove('active'));
  afterEl.style.opacity = 1;
  video3El.currentTime  = v3Dur;
}
/* ============ */

function animate(){easedY+=(scrollY-easedY)*SMOOTH;update(easedY);requestAnimationFrame(animate)}
addEventListener('load',()=>{layout();animate()});
addEventListener('resize',layout);

/* 首屏视差（保持原逻辑） */
if(matchMedia('(pointer:fine)').matches){
  document.body.classList.add('has-parallax');
  heroEl.addEventListener('mousemove',e=>{
    const x=((e.clientX/innerWidth)-.5)*10,
          y=((e.clientY/innerHeight)-.5)*10;
    heroEl.style.backgroundPosition=`calc(50% + ${x}px) calc(50% + ${y}px)`;
  });
}
/* ────────── 侧栏切换 ────────── */
const menuBtn  = document.getElementById('hamburger');
const sidebar  = document.getElementById('sidebar');
const glass    = document.getElementById('glass');    // 半透明遮罩

function toggleMenu(open) {
  const show = open ?? !sidebar.classList.contains('active');
  sidebar.classList.toggle('active', show);
  menuBtn.classList.toggle('is-active', show);
}

menuBtn.addEventListener('click', () => toggleMenu());
glass && glass.addEventListener('click', () => toggleMenu(false)); // 点幕布关闭

/* ───────── 方案A：偷偷播1帧做预缓冲（带重试） ───────── */
function preloadV3(attempt = 1) {
    // 如果已经缓冲过或超过最大尝试次数，则直接返回
    if (preloadV3.done || attempt > 3) return;
    
    video3El.muted = true;           // 静音 → 允许自动播放
    video3El.play()
      .then(() => {
        // ✅ 成功：缓冲已触发
        video3El.pause();
        video3El.currentTime = 0;
        preloadV3.done = true;       // 标记完成，后续不再重复
        // console.log('preloadV3 success on attempt', attempt);
      })
      .catch(() => {
        /* 某些浏览器第一次会拒绝；轻量回退：150 ms 后再试 */
        setTimeout(() => preloadV3(attempt + 1), 150 * attempt);
        // console.warn('preloadV3 retry', attempt);
      });
  }
  
  /* 触发预缓冲 */
  black2El.addEventListener('transitionend', preloadV3);
  /* 如果用户一下滚到底（跳过黑幕2）则在第三屏再兜底一次 */
  thirdEl.addEventListener('mouseenter', preloadV3);
  
  