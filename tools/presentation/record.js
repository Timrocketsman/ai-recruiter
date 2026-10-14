const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const ctx=await b.newContext({viewport:{width:1920,height:1080},recordVideo:{dir:'vid',size:{width:1920,height:1080}}});
const p=await ctx.newPage();await p.goto('file://'+process.cwd()+'/index.html');
await p.waitForFunction(()=>document.body.dataset.done==="1",null,{timeout:180000});await p.waitForTimeout(1500);
const path=await p.video().path();await ctx.close();await b.close();console.log(path);})();
