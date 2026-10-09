const {chromium}=require('playwright');
const map={funnel:'avtomatizatsiya-voronki-prodazh',agents:'ii-agenty-v-telegram',channel:'avtomatizatsiya-telegram-kanala',seo:'seo-s-pomoschyu-neyroseti',si:'ii-teper-si-ukaz-trampa'};
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p=await b.newPage({viewport:{width:1200,height:630}});p.on('console',m=>m.type()==='error'&&console.log(m.text()));p.on('pageerror',e=>console.log('ERR',e.message));
const only=process.argv[2];
for(const [k,slug] of Object.entries(map)){if(only&&only!==k)continue;await p.goto('http://127.0.0.1:8777/scene.html?k='+k);await p.waitForFunction(()=>document.title==='done',null,{timeout:180000});
await (await p.$('#w')).screenshot({path:`/home/user/ai-recruiter/media/covers/${slug}.jpg`,type:'jpeg',quality:88});console.log('ok',k)}
await b.close()})();
