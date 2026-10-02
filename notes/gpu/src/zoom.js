  /* Zoom: every figure gets a button that opens its diagram full screen.
     Wheel or pinch zooms around the pointer, drag pans, double-click fits, Esc closes. */
  (function(){
    const layer=document.createElement('div'); layer.id='zoomlayer';
    layer.innerHTML='<div class="zl-bar"><button type="button" data-z="in">+</button><button type="button" data-z="out">&minus;</button><button type="button" data-z="fit">Fit</button><button type="button" data-z="close">Close (Esc)</button><span class="zl-cap"></span></div><div class="zl-stage"><div class="zl-inner"></div></div>';
    document.body.appendChild(layer);
    const stage=layer.querySelector('.zl-stage'), inner=layer.querySelector('.zl-inner'), cap=layer.querySelector('.zl-cap');
    let s=1,x=0,y=0,w=0,h=0,drag=null;
    const apply=()=>{inner.style.transform='translate('+x+'px,'+y+'px) scale('+s+')';};
    function fit(){
      if(!w||!h) return;
      const W=stage.clientWidth, H=stage.clientHeight;
      s=Math.min(W/w,H/h)*0.94; x=(W-w*s)/2; y=(H-h*s)/2; apply();
    }
    function zoomAt(f,cx,cy){
      const r=stage.getBoundingClientRect(), px=cx-r.left, py=cy-r.top;
      x=px-(px-x)*f; y=py-(py-y)*f; s*=f; apply();
    }
    function zoomMid(f){const r=stage.getBoundingClientRect(); zoomAt(f,r.left+r.width/2,r.top+r.height/2);}
    function open(fig){
      const svg=fig.querySelector('svg'); if(!svg) return;
      const c=svg.cloneNode(true);
      const vb=(svg.getAttribute('viewBox')||'').trim().split(/[\s,]+/).map(Number);
      const r=svg.getBoundingClientRect();
      w=(vb.length===4&&vb[2])?vb[2]:r.width; h=(vb.length===4&&vb[3])?vb[3]:r.height;
      c.setAttribute('width',w); c.setAttribute('height',h);
      c.style.maxWidth='none'; c.style.width=w+'px'; c.style.height=h+'px';
      inner.innerHTML=''; inner.appendChild(c);
      const fc=fig.querySelector('figcaption'); cap.textContent=fc?fc.textContent.replace(/\s+/g,' ').split(/\.\s/)[0]:'';
      layer.classList.add('on'); document.body.style.overflow='hidden';
      requestAnimationFrame(fit);
    }
    function close(){layer.classList.remove('on'); document.body.style.overflow=''; inner.innerHTML='';}
    layer.addEventListener('click',e=>{
      const b=e.target.closest('button'); if(!b) return;
      ({in:()=>zoomMid(1.25),out:()=>zoomMid(0.8),fit:fit,close:close})[b.dataset.z]();
    });
    stage.addEventListener('wheel',e=>{e.preventDefault(); zoomAt(e.deltaY<0?1.12:1/1.12,e.clientX,e.clientY);},{passive:false});
    stage.addEventListener('pointerdown',e=>{drag={px:e.clientX,py:e.clientY,x:x,y:y}; stage.classList.add('drag'); stage.setPointerCapture(e.pointerId);});
    stage.addEventListener('pointermove',e=>{if(!drag) return; x=drag.x+e.clientX-drag.px; y=drag.y+e.clientY-drag.py; apply();});
    stage.addEventListener('pointerup',()=>{drag=null; stage.classList.remove('drag');});
    stage.addEventListener('dblclick',fit);
    window.addEventListener('resize',()=>{if(layer.classList.contains('on')) fit();});
    document.addEventListener('keydown',e=>{
      if(!layer.classList.contains('on')) return;
      if(e.key==='Escape') close(); else if(e.key==='+'||e.key==='=') zoomMid(1.25); else if(e.key==='-') zoomMid(0.8); else if(e.key==='0') fit();
    });
    document.querySelectorAll('figure.dia').forEach(fig=>{
      const b=document.createElement('button'); b.type='button'; b.className='zoombtn';
      b.textContent='⤢ zoom'; b.title='Open full screen: scroll to zoom, drag to pan, Esc to close';
      b.addEventListener('click',()=>open(fig)); fig.appendChild(b);
    });
  })();
