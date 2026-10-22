// Documentation uses actual final-export pixels. No presentation artwork is repainted.
import fs from 'node:fs/promises'; import path from 'node:path';
import {loadPackage} from '../scripts/runtime.mjs'; const {default:sharp}=await loadPackage('sharp');
const root=path.resolve(import.meta.dirname,'..'),w=path.join(root,'examples/visual-defaults'),out=path.join(root,'docs/assets');
const state=JSON.parse(await fs.readFile(path.join(w,'.ppt-beautify/state.json')));
const pages=Object.keys(state.render.pages).sort((a,b)=>Number(a.match(/page-(\d+)/)[1])-Number(b.match(/page-(\d+)/)[1]));
await fs.mkdir(path.join(w,'previews'),{recursive:true});
for(let i=0;i<pages.length;i++)await sharp(path.join(w,pages[i])).jpeg({quality:92}).toFile(path.join(w,`previews/page-${String(i+1).padStart(2,'0')}.jpg`));
const previews=pages.map((_,i)=>path.join(w,`previews/page-${String(i+1).padStart(2,'0')}.jpg`));
async function grid(indices,dest){const layers=[];for(let i=0;i<indices.length;i++)layers.push({input:await sharp(previews[indices[i]-1]).resize(760,428).toBuffer(),left:20+(i%2)*780,top:20+Math.floor(i/2)*448});await sharp({create:{width:1580,height:20+Math.ceil(indices.length/2)*448,channels:3,background:'#E7E7E0'}}).composite(layers).jpeg({quality:92}).toFile(dest);}
await grid([1,2,3,4,5,6,7,8,9],path.join(w,'contact-sheet.jpg'));
await grid([1,2,4,6],path.join(out,'visual-defaults-showcase.jpg'));
await grid([3,4,5,6,7,8],path.join(out,'visual-forms.jpg'));
const blocks=[['READ','理解材料','Facts, units, conditions','事实、单位、条件'],['MATCH','选择表达','Chart or relationship','数据图形、内容关系'],['SOURCE','准备素材','Image briefs + icons','构图提示、配图、图标'],['COMPOSE','自动编排','Type, space, hierarchy','字体、留白、主次'],['REVIEW','导出后复查','Inspect actual pages','逐页看图并修改']];
let art='<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="430"><rect width="1600" height="430" fill="#F4F3EE"/><g font-family="Arial, Hiragino Sans GB, sans-serif" fill="#202623"><text x="55" y="60" font-size="31" font-weight="bold">Content becomes a visual treatment / 内容自动转为视觉构成</text><text x="55" y="103" font-size="20" fill="#5B5F5C">One user request; the agent handles chart choice, typography, imagery and matched symbols.</text><text x="55" y="137" font-size="20" fill="#5B5F5C">用户给材料，agent 处理图形选择、字体层级、配图与统一图标。</text>';
for(let i=0;i<blocks.length;i++){const x=55+i*310;art+=`<text x="${x}" y="218" font-size="16" fill="#B0772A">0${i+1} / ${blocks[i][0]}</text><text x="${x}" y="264" font-size="29" font-weight="bold">${blocks[i][1]}</text><text x="${x}" y="316" font-size="18">${blocks[i][2]}</text><text x="${x}" y="350" font-size="20" fill="#5B5F5C">${blocks[i][3]}</text>`;if(i<4)art+=`<path d="M${x+242} 249h40m-8-6 8 6-8 6" stroke="#AEB3AA" stroke-width="1.5" fill="none"/>`;}
art+='</g></svg>';await fs.writeFile(path.join(out,'visual-defaults-workflow.svg'),art);await sharp(Buffer.from(art)).png().toFile(path.join(out,'visual-defaults-workflow.png'));
console.log('Wrote actual-page previews, six visual forms and bilingual workflow.');
