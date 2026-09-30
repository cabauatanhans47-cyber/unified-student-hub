import {unzipSync,strFromU8} from 'fflate';
export const allowedExtensions=['pdf','pptx','ppt','docx','doc','txt','md','csv','xlsx','xls','png','jpg','jpeg','webp'];
export const extension=name=>name.split('.').at(-1).toLowerCase();
export async function textPreview(file){
 const ext=extension(file.name);
 if(['txt','md','csv'].includes(ext)){if(file.size>2*1024*1024)return 'Text preview limited to files up to 2 MB. Download the original to open it.';return await file.text();}
 if(!['docx','pptx','xlsx'].includes(ext))return '';
 if(file.size>10*1024*1024)return 'Office text preview limited to files up to 10 MB. Download the original to open it.';
 let total=0;const entries=unzipSync(new Uint8Array(await file.arrayBuffer()),{filter:e=>{const wanted=ext==='pptx'?/^ppt\/slides\/slide\d+\.xml$/.test(e.name):ext==='docx'?e.name==='word/document.xml':/^xl\/(sharedStrings|worksheets\/sheet\d+)\.xml$/.test(e.name);if(!wanted)return false;total+=e.originalSize;if(total>15*1024*1024)throw new Error('This document is too large to preview safely. The original is still saved.');return true;}});
 const xml=s=>new DOMParser().parseFromString(strFromU8(s),'application/xml');
 const names=Object.keys(entries).sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));
 if(ext==='xlsx'){
  const shared=entries['xl/sharedStrings.xml']?Array.from(xml(entries['xl/sharedStrings.xml']).getElementsByTagName('si')).map(n=>Array.from(n.getElementsByTagName('t')).map(x=>x.textContent).join('')):[];
  return names.filter(n=>n.includes('/worksheets/')).map((name,i)=>'Sheet '+(i+1)+'\n'+Array.from(xml(entries[name]).getElementsByTagName('row')).map(row=>Array.from(row.getElementsByTagName('c')).map(cell=>{const val=cell.getElementsByTagName('v')[0]?.textContent||cell.getElementsByTagName('t')[0]?.textContent||'';return cell.getAttribute('t')==='s'?shared[+val]||'':val;}).join(' | ')).join('\n')).join('\n\n');
 }
 return names.map((name,i)=>{const doc=xml(entries[name]);const paragraphs=Array.from(doc.getElementsByTagNameNS('*','p'));return (ext==='pptx'?'Slide '+(i+1)+'\n':'')+paragraphs.map(p=>Array.from(p.getElementsByTagNameNS('*','t')).map(t=>t.textContent).join('')).join('\n');}).join('\n\n');
}
