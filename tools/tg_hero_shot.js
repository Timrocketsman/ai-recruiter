const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const p=await b.newPage({viewport:{width:728,height:1000},deviceScaleFactor:2});
for(const s of process.argv.slice(2)){
 await p.goto('http://127.0.0.1:8765/journal/'+s+'/',{waitUntil:'load'});await p.waitForTimeout(600);
 const box=await p.evaluate(()=>{
  const h=document.querySelector('header.hero');
  for(const e of document.querySelectorAll('body *')){if(e.contains(h)||h.contains(e))continue;const cs=getComputedStyle(e);if(cs.position==='fixed'||cs.position==='sticky')e.style.display='none';}
  for(const e of document.querySelectorAll('html,body,main,article,header,.hero')){e.style.filter='none';e.style.opacity='1';e.style.backdropFilter='none';}
  document.querySelectorAll('[class*=banner],[class*=consent],[class*=popup],[class*=modal],[id*=cookie]').forEach(e=>{if(!e.contains(h))e.style.display='none'});const by=h.querySelector('.byline')||h;
  let top=h.getBoundingClientRect().top;const prev=h.previousElementSibling;if(prev)top=Math.min(top,prev.getBoundingClientRect().top);
  const bottom=by.getBoundingClientRect().bottom;return {y:Math.max(0,top-40+window.scrollY),h:bottom-top+40};});
 await p.screenshot({path:'media/telegram/'+s+'.png',clip:{x:0,y:box.y,width:728,height:Math.round(box.h)}});
 console.log(s,JSON.stringify(box));}
await b.close()})();
