// Documentation only: compose existing exported slide pixels and explicit labels.
// Requires sharp in the host, not in the portable skill's runtime dependencies.
import fs from 'node:fs/promises';
import path from 'node:path';
import {loadPackage} from '../scripts/runtime.mjs';
const {default:sharp}=await loadPackage('sharp');
const root=path.resolve(import.meta.dirname,'..');
const out=path.join(root,'docs/assets');
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;');
const svg=(w,h,body)=>Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="100%" height="100%" fill="#EEEFEA"/><g font-family="Arial, Hiragino Sans GB, sans-serif" fill="#252621">${body}</g></svg>`);
const txt=(x,y,t,size=22)=>`<text x="${x}" y="${y}" font-size="${size}">${esc(t)}</text>`;
async function grid(files,destination,columns=2,cell=760){
 const gap=20,rows=Math.ceil(files.length/columns),cw=cell,ch=Math.round(cell*9/16);
 const layers=[];
 for(let i=0;i<files.length;i++)layers.push({input:await sharp(files[i]).resize(cw,ch).toBuffer(),left:gap+(i%columns)*(cw+gap),top:gap+Math.floor(i/columns)*(ch+gap)});
 await sharp({create:{width:gap+columns*(cw+gap),height:gap+rows*(ch+gap),channels:3,background:'#EEEFEA'}}).composite(layers).jpeg({quality:89}).toFile(destination);
}
for(const name of ['launch','yellow','operations']){
 const w=path.join(root,'examples',name),state=JSON.parse(await fs.readFile(path.join(w,'.ppt-beautify/state.json')));
 const pages=Object.keys(state.render.pages).sort((a,b)=>Number(a.match(/page-(\d+)/)[1])-Number(b.match(/page-(\d+)/)[1])).map(p=>path.join(w,p));
 const dir=path.join(w,'previews');await fs.mkdir(dir,{recursive:true});
 for(const old of await fs.readdir(dir))if(/^page-\d+\.jpg$/.test(old))await fs.unlink(path.join(dir,old));
 const publicPages=[];
 for(let i=0;i<pages.length;i++){const dest=path.join(dir,`page-${String(i+1).padStart(2,'0')}.jpg`);await sharp(pages[i]).jpeg({quality:91}).toFile(dest);publicPages.push(dest);}
 await grid(publicPages,path.join(w,'contact-sheet.jpg'));
 const selected=name==='launch'?[0,2,3,5,6,8]:name==='yellow'?[0,1,2,4]:[0,1,2,3,4,5];
 await grid(selected.map(i=>publicPages[i]),path.join(out,`${name}-showcase.jpg`));
}
for(const [kind,before,after,title,zh,left,right] of [
 ['table','launch/v3-page-10.jpg','launch/page-07.jpg','A comparison table, edited for the decision','按比较任务重排表格，信息仍可编辑','v3 / Equal columns + repeated shared values','v4 / Aligned differences + shared note'],
 ['color','launch/v3-page-09.jpg','launch/page-06.jpg','Use accent to identify the focal evidence','强调色对应焦点，而不是自动给全部数据上色','v3 / One accent across all bars','v4 / Largest response highlighted'],
 ['text','yellow/v3-page-06.jpg','yellow/page-05.jpg','Let a paragraph remain a paragraph','根据正文与照片构图，不强制每句配粗体标签','v3 / Uniform labelled blocks','v4 / One editorial reading sequence']]){
 const old=path.join(root,'examples/evolution/before',before),[name,file]=after.split('/'),next=path.join(root,'examples',name,'previews',file);
 const base=svg(1600,680,txt(40,55,title,34)+txt(40,97,zh,24)+txt(40,149,left,21)+txt(820,149,right,21)+txt(40,647,'Same source & image assets. Actual exported slides. / 同一原文与配图，实际导出页面。',20));
 await sharp(base).composite([{input:await sharp(old).resize(740,416).toBuffer(),left:40,top:177},{input:await sharp(next).resize(740,416).toBuffer(),left:820,top:177}]).jpeg({quality:93}).toFile(path.join(out,`evolution-${kind}.jpg`));
}
await sharp(path.join(out,'composition-workflow.svg')).png().toFile(path.join(out,'composition-workflow.png'));
console.log('Updated current-export previews, montages, version comparisons and workflow PNG.');
