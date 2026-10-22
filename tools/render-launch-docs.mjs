// Composite actual exported pixels, never repaint slide artwork.
import fs from 'node:fs/promises';import path from 'node:path';
import {loadPackage} from '../scripts/runtime.mjs';const {default:sharp}=await loadPackage('sharp');
const root=path.resolve(import.meta.dirname,'..'),w=path.join(root,'examples/launch-studio'),out=path.join(root,'docs/assets');
const state=JSON.parse(await fs.readFile(path.join(w,'.ppt-beautify/state.json')));
const pages=Object.keys(state.render.pages).sort((a,b)=>Number(a.match(/page-(\d+)/)[1])-Number(b.match(/page-(\d+)/)[1]));
await fs.mkdir(path.join(w,'previews'),{recursive:true});
for(let i=0;i<pages.length;i++)await sharp(path.join(w,pages[i])).jpeg({quality:92}).toFile(path.join(w,`previews/page-${String(i+1).padStart(2,'0')}.jpg`));
const preview=(folder,index)=>path.join(root,`examples/${folder}/previews/page-${String(index).padStart(2,'0')}.jpg`);
async function grid(indices,dest){const layers=[];for(let i=0;i<indices.length;i++)layers.push({input:await sharp(preview('launch-studio',indices[i])).resize(760,428).toBuffer(),left:20+(i%2)*780,top:20+Math.floor(i/2)*448});await sharp({create:{width:1580,height:20+Math.ceil(indices.length/2)*448,channels:3,background:'#E7E7E0'}}).composite(layers).jpeg({quality:92}).toFile(dest);}
await grid([1,2,3,4,5,6,7,8,9],path.join(w,'contact-sheet.jpg'));
await grid([1,2,4,8],path.join(out,'launch-studio-showcase.jpg'));
const layers=[];
const label=Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="1580" height="116"><rect width="1580" height="116" fill="#202623"/><g font-family="Arial, Hiragino Sans GB, sans-serif" fill="#F4F3EE"><text x="20" y="42" font-size="25">5.0 / Before · 修改前</text><text x="800" y="42" font-size="25">5.1 / After · 修改后</text><text x="20" y="86" font-size="21">Same source, data and two images / 相同材料、数据、两张配图；只改变自动视觉处理</text></g></svg>');
layers.push({input:label,left:0,top:0});
for(let row=0;row<3;row++)for(let col=0;col<2;col++)layers.push({input:await sharp(preview(col?'launch-studio':'visual-defaults',[2,4,8][row])).resize(760,428).toBuffer(),left:20+col*780,top:136+row*448});
await sharp({create:{width:1580,height:1480,channels:3,background:'#E7E7E0'}}).composite(layers).jpeg({quality:92}).toFile(path.join(out,'v51-same-input-comparison.jpg'));
const diagram=`<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="560"><rect width="1600" height="560" fill="#F4F3EE"/><g font-family="Arial, Hiragino Sans GB, sans-serif" fill="#202623"><text x="60" y="68" font-size="34">A whole-page recipe / 封装整页视觉效果</text><text x="60" y="112" font-size="22" fill="#606660">Source meaning → page appearance → real assets → editable export</text><text x="60" y="148" font-size="22" fill="#606660">内容含义 → 页面样貌 → 实际素材 → 可编辑交付</text><path d="M60 190H1540" stroke="#CBCFC8"/>`;
const blocks=[['01','READ / 理解','Story + grounded data','叙事、数值、限定条件'],['02','DIRECT / 设计','Type + chart + image + labels','字体、图形、配图、标注'],['03','BUILD / 编排','Native text, data and relations','原生文字、数据与关系'],['04','INSPECT / 看图','Revise the actual exported page','检查实际导出并修改']];
let svg=diagram;for(let i=0;i<blocks.length;i++){const x=60+i*380;svg+=`<text x="${x}" y="273" fill="#B0772A" font-size="42">${blocks[i][0]}</text><text x="${x}" y="333" font-size="24">${blocks[i][1]}</text><text x="${x}" y="391" font-size="20">${blocks[i][2]}</text><text x="${x}" y="431" font-size="22" fill="#606660">${blocks[i][3]}</text>`;}svg+='<text x="60" y="511" font-size="20" fill="#606660">Image tools must execute requests. A prompt file is not an image. / 配图必须实际生成或取图，提示词本身不算交付。</text></g></svg>';
await fs.writeFile(path.join(out,'page-recipe-workflow.svg'),svg);await sharp(Buffer.from(svg)).png().toFile(path.join(out,'page-recipe-workflow.png'));
console.log('Actual-page contact sheet, same-input comparison and bilingual recipe diagram written.');
