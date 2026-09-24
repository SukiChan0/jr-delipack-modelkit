// SPDX-License-Identifier: GPL-3.0-or-later
// Minimal dependency-free WebGL viewer for THIS tool's mesh.json, not a general importer.
'use strict';
(()=>{
 const $=id=>document.getElementById(id),c=$('view'),message=s=>{$('viewStatus').textContent=s;};
 const gl=c.getContext('webgl',{antialias:true,alpha:false});let items=[],center=[0,0,0],extent=1,pointer=null;
 if(!gl){message('WebGL unavailable. Generated OBJ/GLB files and numeric recipe remain usable.');return;}
 // Positive pitch looks down into an open bowl: world +Z must be nearer, not farther.
 const vs=`attribute vec3 p;attribute vec3 n;uniform vec3 center;uniform float scale;uniform float yaw;uniform float pitch;uniform float aspect;varying vec3 normal;void main(){float a=cos(yaw),b=sin(yaw),d=cos(pitch),e=sin(pitch);vec3 q=(p-center)*scale;vec3 v=vec3(a*q.x-b*q.y,d*(b*q.x+a*q.y)-e*q.z,e*(b*q.x+a*q.y)+d*q.z);gl_Position=vec4(v.x/aspect,v.z,v.y*0.2,1.0);normal=vec3(a*n.x-b*n.y,d*(b*n.x+a*n.y)-e*n.z,e*(b*n.x+a*n.y)+d*n.z);}`;
 // Match the linear RGB convention used by GLB baseColorFactor on the sRGB display.
 const fs=`precision mediump float;varying vec3 normal;uniform vec3 color;void main(){float light=0.30+0.70*max(dot(normalize(normal),normalize(vec3(-0.3,-0.6,0.8))),0.0);vec3 linearColor=max(color*light,vec3(0.0));vec3 displayColor=mix(12.92*linearColor,1.055*pow(linearColor,vec3(1.0/2.4))-0.055,step(vec3(0.0031308),linearColor));gl_FragColor=vec4(displayColor,1.0);}`;
 function shader(type,src){const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(s));return s;}
 let program;try{program=gl.createProgram();const a=shader(gl.VERTEX_SHADER,vs),b=shader(gl.FRAGMENT_SHADER,fs);gl.attachShader(program,a);gl.attachShader(program,b);gl.linkProgram(program);gl.deleteShader(a);gl.deleteShader(b);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw new Error('Shader linking failed');}catch(e){message('Viewer initialization failed: '+e.message);return;}
 const loc={};for(const k of ['center','scale','yaw','pitch','aspect','color'])loc[k]=gl.getUniformLocation(program,k);
 const pa=gl.getAttribLocation(program,'p'),na=gl.getAttribLocation(program,'n');
 function dispose(list){for(const it of list)for(const b of [it.p,it.n,it.i])gl.deleteBuffer(b);}
 function buffer(target,array){const b=gl.createBuffer();gl.bindBuffer(target,b);gl.bufferData(target,array,gl.STATIC_DRAW);return b;}
 function validate(data){
   if(data.schema_version!==1||data.units!=='mm'||!Array.isArray(data.parts)||data.parts.length<1||data.parts.length>8)throw new Error('Not a supported mesh.json.');
   let total=0;const ids=new Set();
   for(const m of data.parts){
     if(typeof m.id!=='string'||!/^[A-Za-z][A-Za-z0-9_-]{0,47}$/.test(m.id)||ids.has(m.id))throw new Error('Invalid or repeated part ID');ids.add(m.id);
     if(!Array.isArray(m.vertices_mm)||m.vertices_mm.length>65535||m.vertices_mm.length<4||!Array.isArray(m.normals)||m.normals.length!==m.vertices_mm.length||!Array.isArray(m.faces)||m.faces.length>140000)throw new Error('Mesh exceeds prototype budget or normals are missing');
     total+=m.vertices_mm.length;if(total>150000)throw new Error('Total vertex budget exceeded');
     const triple=(v,max)=>Array.isArray(v)&&v.length===3&&v.every(x=>typeof x==='number'&&Number.isFinite(x)&&Math.abs(x)<=max);
     if(!triple(m.position_mm,10000)||!triple(m.color,1)||m.color.some(x=>x<0))throw new Error('Invalid transform/color');
     for(const p of m.vertices_mm)if(!triple(p,2000))throw new Error('Invalid vertex');
     for(const p of m.normals)if(!triple(p,1.001)||Math.hypot(...p)<0.9)throw new Error('Invalid normal');
     for(const f of m.faces)if(!Array.isArray(f)||f.length!==3||f.some(i=>!Number.isInteger(i)||i<0||i>=m.vertices_mm.length))throw new Error('Invalid face');
   }return data.parts;
 }
 function load(parts){const next=[];try{
  const low=[Infinity,Infinity,Infinity],high=[-Infinity,-Infinity,-Infinity];
  for(const m of parts){const pts=m.vertices_mm.map(v=>v.map((x,k)=>x+m.position_mm[k]));
   for(const v of pts)for(let k=0;k<3;k++){low[k]=Math.min(low[k],v[k]);high[k]=Math.max(high[k],v[k]);}
   next.push({id:m.id,color:m.color,p:buffer(gl.ARRAY_BUFFER,new Float32Array(pts.flat())),n:buffer(gl.ARRAY_BUFFER,new Float32Array(m.normals.flat())),i:buffer(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(m.faces.flat())),count:m.faces.length*3});}
  dispose(items);items=next;center=low.map((v,k)=>(v+high[k])/2);extent=Math.max(...low.map((v,k)=>high[k]-v),1);
  $('part').replaceChildren(new Option('All parts','all'));for(const m of parts)$('part').add(new Option(m.id,m.id));
  message(`Loaded ${parts.length} parts; opaque preview only. Dimensions are inputs, not photo-measurement verification.`);render();
 }catch(e){dispose(next);throw e;}}
 function render(){if(document.hidden||gl.isContextLost())return;
   const box=c.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,1.5),w=Math.max(1,Math.round(box.width*dpr)),h=Math.max(1,Math.round(box.width*2/3*dpr));if(c.width!==w||c.height!==h){c.width=w;c.height=h;}
   gl.viewport(0,0,w,h);gl.clearColor(.91,.94,.92,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);gl.useProgram(program);
   gl.uniform3fv(loc.center,center);gl.uniform1f(loc.scale,1.65/extent*Number($('zoom').value));gl.uniform1f(loc.yaw,Number($('yaw').value)*Math.PI/180);gl.uniform1f(loc.pitch,Number($('pitch').value)*Math.PI/180);gl.uniform1f(loc.aspect,w/h);
   for(const it of items){if($('part').value!=='all'&&$('part').value!==it.id)continue;gl.bindBuffer(gl.ARRAY_BUFFER,it.p);gl.enableVertexAttribArray(pa);gl.vertexAttribPointer(pa,3,gl.FLOAT,false,0,0);gl.bindBuffer(gl.ARRAY_BUFFER,it.n);gl.enableVertexAttribArray(na);gl.vertexAttribPointer(na,3,gl.FLOAT,false,0,0);gl.uniform3fv(loc.color,it.color);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,it.i);gl.drawElements(gl.TRIANGLES,it.count,gl.UNSIGNED_SHORT,0);}
 }
 $('mesh').addEventListener('change',async e=>{const f=e.target.files[0];if(!f)return;try{if(f.size>20*1024*1024)throw new Error('File exceeds 20 MB');load(validate(JSON.parse(await f.text())));}catch(e){message('Load failed: '+e.message);}});
 for(const id of ['yaw','pitch','zoom','part'])$(id).addEventListener('input',render);
 $('reset').onclick=()=>{$('yaw').value=-30;$('pitch').value=55;$('zoom').value=1;render();};
 c.onpointerdown=e=>{pointer={id:e.pointerId,x:e.clientX,y:e.clientY};c.setPointerCapture(e.pointerId);};
 c.onpointermove=e=>{if(!pointer||pointer.id!==e.pointerId)return;$('yaw').value=Number($('yaw').value)+(e.clientX-pointer.x)*.6;$('pitch').value=Math.max(-85,Math.min(85,Number($('pitch').value)+(e.clientY-pointer.y)*.6));pointer.x=e.clientX;pointer.y=e.clientY;render();};
 for(const event of ['pointerup','pointercancel','lostpointercapture'])c.addEventListener(event,()=>{pointer=null;});
 c.addEventListener('webglcontextlost',e=>{e.preventDefault();pointer=null;message('WebGL context lost. Keep the recipe; reload this page to restore the viewer.');});
 document.addEventListener('visibilitychange',()=>{pointer=null;render();});window.addEventListener('resize',render);window.addEventListener('pageshow',render);render();
})();
