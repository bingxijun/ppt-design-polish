// Compose actual exported pixels into documentation; no slide artwork is repainted.
import fs from 'node:fs/promises';import path from 'node:path';
import {loadPackage} from '../scripts/runtime.mjs';const {default:sharp}=await loadPackage('sharp');
const root=path.resolve(import.meta.dirname,'..'),w=path.join(root,'examples/studio'),out=path.join(root,'docs/assets');
const state=JSON.parse(await fs.readFile(path.join(w,'.ppt-beautify/state.json')));
const pages=Object.keys(state.render.pages).sort((a,b)=>Number(a.match(/page-(\d+)/)[1])-Number(b.match(/page-(\d+)/)[1]));
await fs.mkdir(path.join(w,'previews'),{recursive:true});
for(let i=0;i<pages.length;i++)await sharp(path.join(w,pages[i])).jpeg({quality:91}).toFile(path.join(w,`previews/page-${String(i+1).padStart(2,'0')}.jpg`));
async function grid(files,dest){const layers=[];for(let i=0;i<files.length;i++)layers.push({input:await sharp(files[i]).resize(760,428).toBuffer(),left:20+(i%2)*780,top:20+Math.floor(i/2)*448});await sharp({create:{width:1580,height:20+Math.ceil(files.length/2)*448,channels:3,background:'#E9E3D8'}}).composite(layers).jpeg({quality:91}).toFile(dest);}
const previews=pages.map((_,i)=>path.join(w,`previews/page-${String(i+1).padStart(2,'0')}.jpg`));
await grid(previews,path.join(w,'contact-sheet.jpg'));await grid([previews[0],previews[1],previews[2],previews[4]],path.join(out,'studio-showcase.jpg'));
const text=(x,y,t,size=23)=>`<text x="${x}" y="${y}" font-size="${size}">${t}</text>`;
let labels=text(40,53,'Three proof pages, two compositions each / 三种页面，各自打样比较',32)+text(40,96,'Same frozen source and content contracts. Host selection; independent reader review pending.',20)+text(40,132,'同一原文与内容约束。选稿来自本次制作复查，独立读者评审待完成。',22);
const layers=[];
for(let i=0;i<3;i++){let yy=175+i*485;labels+=text(40,yy,['Body / 正文','Data / 数据','Dense table / 排期表'][i],22)+text(820,yy,'Alternative composition / 构图候选',22);for(let j=0;j<2;j++){let f=path.join(w,`evidence/candidates/${['body','data','dense'][i]}/${['a','b'][j]}/page-${String(i+1).padStart(2,'0')}.png`);layers.push({input:await sharp(f).resize(740,416).toBuffer(),left:40+j*780,top:yy+20});}}
const svg=Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1645"><rect width="100%" height="100%" fill="#E9E3D8"/><g font-family="Arial, Hiragino Sans GB, sans-serif" fill="#292521">${labels}</g></svg>`);
await sharp(svg).composite(layers).jpeg({quality:91}).toFile(path.join(out,'studio-proofs.jpg'));
const before=path.join(w,'evidence/rounds/01/page-03.png'),after=previews[2];
const comparison=Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="650"><rect width="100%" height="100%" fill="#E9E3D8"/><g font-family="Arial, Hiragino Sans GB, sans-serif" fill="#292521">${text(40,55,'Visual revision / 实际看图后的返工',34)+text(40,103,'Before: focal bar last; stranded character / 修改前：重点位于末尾，中文孤字',21)+text(820,103,'After: ranked reading; complete phrase / 修改后：焦点先读，语义断行',21)+text(40,613,'Native chart and text remain editable. Both images come from exported PPTX files. / 原生图表与文字可编辑，均为实际导出。',19)}</g></svg>`);
await sharp(comparison).composite([{input:await sharp(before).resize(740,416).toBuffer(),left:40,top:145},{input:await sharp(after).resize(740,416).toBuffer(),left:820,top:145}]).jpeg({quality:93}).toFile(path.join(out,'studio-revision.jpg'));
await sharp(path.join(out,'studio-workflow.svg')).png().toFile(path.join(out,'studio-workflow.png'));
console.log('Updated studio previews, proof comparison, actual revision and bilingual workflow.');
