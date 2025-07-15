/* ========= 全局参数 ========= */
const REFRESH_MS = 30 * 60 * 1000;   // 30 分钟自动刷新
/* ========= 全局 ========= */
const PAGE_SIZE = 15;
let currentPage = 1;
/* ============================ */

let lastBatch = new Set();

/* ---------- 构建卡片 ---------- */
function addCard(a){
  const el = document.createElement("article");
  el.className = "card hidden";
  el.innerHTML = `
    <a class="thumb" href="${a.url}" target="_blank" rel="noopener">
      <img src="${a.img}" alt="${a.title}" loading="lazy">
      <span class="ripple"></span>
    </a>
    <div class="content">
      <h2 class="title"><a href="${a.url}" target="_blank" rel="noopener">${a.title}</a></h2>
      <p class="meta">${a.provider} · ${a.time}</p>
      <p class="summary">${a.summary}</p>
    </div>`;
  document.getElementById("news-grid").appendChild(el);
}

/* ---------- IntersectionObserver ---------- */
function observeReveal(){
  const io = new IntersectionObserver((es,ob)=>{
    es.forEach(e=>{
      if(e.isIntersecting){e.target.classList.add("show");ob.unobserve(e.target);}
    });
  },{threshold:.15});
  document.querySelectorAll(".card.hidden").forEach(el=>io.observe(el));
}

/* ---------- 获取并渲染 ---------- */
async function fetchAndRender(){
  const res  = await fetch("/news/api?t="+Date.now());
  const data = await res.json();
  let fresh  = data.articles.filter(a=>!lastBatch.has(a.url));
  if(fresh.length===0){fresh = shuffle([...data.articles]).slice(0,15);}
  lastBatch = new Set(fresh.map(a=>a.url));
  const grid = document.getElementById("news-grid");
  grid.innerHTML=""; fresh.forEach(addCard); observeReveal();
}
function shuffle(arr){
  for(let i=arr.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[arr[i],arr[j]]=[arr[j],arr[i]];}return arr;
}

/* ---------- 主题切换 ---------- */
(function(){
  const btn=document.getElementById("theme-toggle"),body=document.body,L="light";
  if(localStorage.getItem("theme")===L){body.classList.add(L);swap();}
  btn.onclick=()=>{body.classList.toggle(L);localStorage.setItem("theme",body.classList.contains(L)?L:"");swap();}
  function swap(){btn.querySelector("use").setAttribute("href",body.classList.contains(L)?"#moon":"#sun");}
})();

/* ---- 请求并渲染指定页 ---- */
async function loadPage(page = 1){
  const url = `/news/api?page=${page}&size=${PAGE_SIZE}&t=${Date.now()}`;
  const res  = await fetch(url);
  const data = await res.json();
  const grid = document.getElementById("news-grid");
  grid.innerHTML = "";
  data.articles.forEach(addCard);
  observeReveal();
}

/* ---- 换一批按钮 ---- */
(function(){
  const btn = document.getElementById("change-batch");
  btn.onclick = ()=>{
    btn.classList.add("spin");
    currentPage = currentPage >= 3 ? 1 : currentPage + 1;   // 例如循环 1-6 页
    loadPage(currentPage).finally(()=>btn.classList.remove("spin"));
  };
})();

/* ---- 首屏渲染 & 自动刷新 ---- */
loadPage(1);
setInterval(()=>{currentPage = 1; loadPage(1)}, 30*60*1000);  // 每 30 分重置
/* ---------- 汉堡菜单 ---------- */
(function(){
  const b=document.getElementById("hamburger"),s=document.getElementById("sidebar"),g=document.getElementById("glass");
  const open=()=>{b.classList.add("is-active");s.classList.add("active");document.body.style.overflow="hidden";}
  const close=()=>{b.classList.remove("is-active");s.classList.remove("active");document.body.style.overflow="";}
  b.onclick=()=>s.classList.contains("active")?close():open();g.onclick=close;document.onkeydown=e=>e.key==="Escape"&&close();
})();
