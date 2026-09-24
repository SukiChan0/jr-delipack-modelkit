// SPDX-License-Identifier: GPL-3.0-or-later
'use strict';
const el=id=>document.getElementById(id), canvas=el('trace'),ctx=canvas.getContext('2d');
let background=null, axis=[], trace=[], calibrating=false, currentURL=null;
const status=s=>{el('traceStatus').textContent=s;};
function draw(){
  ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#f6f7f2';ctx.fillRect(0,0,canvas.width,canvas.height);
  if(background)ctx.drawImage(background,0,0,canvas.width,canvas.height);
  ctx.lineWidth=2;
  if(axis.length){ctx.strokeStyle='#1d886e';ctx.beginPath();ctx.moveTo(...axis[0]);if(axis.length===2)ctx.lineTo(...axis[1]);ctx.stroke();}
  for(const p of axis){ctx.fillStyle='#1d886e';ctx.beginPath();ctx.arc(...p,5,0,Math.PI*2);ctx.fill();}
  if(trace.length){ctx.strokeStyle='#bd6925';ctx.beginPath();ctx.moveTo(...trace[0]);for(const p of trace.slice(1))ctx.lineTo(...p);ctx.stroke();}
  trace.forEach((p,i)=>{ctx.fillStyle='#a14915';ctx.beginPath();ctx.arc(...p,3,0,Math.PI*2);ctx.fill();ctx.fillText(String(i+1),p[0]+5,p[1]-5);});
}
function clearAll(){axis=[];trace=[];calibrating=false;draw();}
el('photo').addEventListener('change',async e=>{
 const f=e.target.files[0];if(!f)return;
 if(!['image/png','image/jpeg','image/webp'].includes(f.type)||f.size>10*1024*1024){status('Use PNG/JPEG/WebP under 10 MB. SVG uploads are not supported.');return;}
 const url=URL.createObjectURL(f);const img=new Image();
 img.onload=()=>{if(img.naturalWidth*img.naturalHeight>20_000_000){URL.revokeObjectURL(url);status('Image exceeds 20 megapixels. Resize a COPY first.');return;}
  if(currentURL)URL.revokeObjectURL(currentURL);currentURL=url;
  // Letterbox into a fixed canvas without anisotropic scaling.
  const bg=document.createElement('canvas');bg.width=900;bg.height=560;const b=bg.getContext('2d');b.fillStyle='#f7f7f4';b.fillRect(0,0,900,560);
  const s=Math.min(900/img.naturalWidth,560/img.naturalHeight);b.drawImage(img,(900-img.naturalWidth*s)/2,(560-img.naturalHeight*s)/2,img.naturalWidth*s,img.naturalHeight*s);
  background=bg;clearAll();status('Reference loaded locally. Set bottom and top axis points. Photos are NOT included in exported JSON.');};
 img.onerror=()=>{URL.revokeObjectURL(url);status('Cannot decode this image.');};img.src=url;
});
el('synthetic').onclick=()=>{
 const b=document.createElement('canvas');b.width=900;b.height=560;const c=b.getContext('2d');c.fillStyle='#fafaf4';c.fillRect(0,0,900,560);
 c.strokeStyle='#54686b';c.lineWidth=3;c.beginPath();[[180,460],[460,460],[580,220],[573.3,220],[456.8,453],[180,453]].forEach((p,i)=>i?c.lineTo(...p):c.moveTo(...p));c.closePath();c.stroke();
 c.setLineDash([6,5]);c.beginPath();c.moveTo(180,480);c.lineTo(180,180);c.stroke();c.setLineDash([]);c.fillStyle='#19312b';c.font='16px system-ui';c.fillText('Invented section: axis bottom (180,460), top (180,220)',180,130);c.fillText('Calibration height: 48 mm. Not a photo or commercial SKU.',180,156);
 background=b;clearAll();el('height').value='48';status('Example sketch loaded. Set axis at (180,460), then (180,220), or use the numeric example recipe.');
};
el('calibrate').onclick=()=>{axis=[];trace=[];calibrating=true;draw();status('Click bottom origin on the axis, then a top reference on the same axis. This clears the old trace.');};
canvas.addEventListener('click',e=>{const box=canvas.getBoundingClientRect(),p=[(e.clientX-box.left)*canvas.width/box.width,(e.clientY-box.top)*canvas.height/box.height];
 if(calibrating){axis.push(p);if(axis.length===2){if(Math.hypot(axis[1][0]-axis[0][0],axis[1][1]-axis[0][1])<30){axis=[];status('Calibration segment too short. Choose points at least 30 canvas pixels apart.');}else{calibrating=false;status('Calibration set. Trace the full material half-section. Inner wall must be supplied, not guessed.');}}else status('Now click the top reference on the same axis.');}
 else if(axis.length!==2){status('Set the two axis calibration points first.');return;}
 else {if(trace.length>=256){status('Maximum 256 trace points.');return;}trace.push(p);status(`${trace.length} points. Complete outside AND inside material boundary; export closes the polygon.`);}draw();});
el('undo').onclick=()=>{trace.pop();draw();};el('clear').onclick=()=>{trace=[];draw();};
el('export').onclick=()=>{
 try{
  const h=Number(el('height').value),id=el('partId').value.trim();
  if(!Number.isFinite(h)||h<1||h>1000)throw new Error('Calibration height must be 1..1000 mm.');
  if(!/^[A-Za-z][A-Za-z0-9_-]{0,47}$/.test(id))throw new Error('Use a short ASCII part ID.');
  if(axis.length!==2||trace.length<3)throw new Error('Set calibration and at least three material points.');
  const [o,t]=axis,dx=t[0]-o[0],dy=t[1]-o[1],L=Math.hypot(dx,dy),ux=dx/L,uy=dy/L,side=Number(el('side').value);
  const points=trace.map(p=>{let r=((p[0]-o[0])*(-uy)+(p[1]-o[1])*ux)*h/L*side;let z=((p[0]-o[0])*ux+(p[1]-o[1])*uy)*h/L;
    // Only a small, explicitly documented screen tolerance snaps to the axis/floor.
    const snap=h/L*2;if(Math.abs(r)<snap)r=0;if(Math.abs(z)<snap)z=0;
    if(r<0||z<0||r>1000||z>1000)throw new Error('Point outside supported non-negative R/Z range. Check traced side and axis.');return [Number(r.toFixed(4)),Number(z.toFixed(4))];});
  const recipe={schema_version:1,units:'mm',segments:96,notes:'Manual reference trace. Calibration uses uniform image scale; perspective and hidden surfaces are NOT solved. Two canvas pixels snap to axis/floor. Run Python validation.',parts:[{id,source_status:'MANUAL_TRACE_UNVERIFIED',section_rz_mm:points,position_mm:[0,0,0],color:[0.18,0.23,0.25]}]};
  const url=URL.createObjectURL(new Blob([JSON.stringify(recipe,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='traced_recipe.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status('Recipe exported. Run Python build to validate geometry; export alone is NOT validation.');
 }catch(e){status(e.message);}
};
window.addEventListener('pagehide',()=>{if(currentURL){URL.revokeObjectURL(currentURL);currentURL=null;}});draw();
