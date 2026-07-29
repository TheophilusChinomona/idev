# Advanced Browse Patterns — on-demand reference

Load when you need snapshot diff, annotated screenshots, CSS inspection,
page cleanup, or URL content comparison.

## Before/after diff — snapshot state comparison
```
xd://browser { "action": "run", "name": "main",
  "code": "const b=await tab.extract('body'); await tab.click('#btn');"+
    "const a=await tab.extract('body'); {b:b.slice(0,200), a:a.slice(0,200)}" }
```

## Annotated screenshot — red overlay boxes with element labels
```
xd://browser { "action": "run", "name": "main", "code": "
  const o = Object.assign(document.createElement('div'),
    {style:'position:fixed;inset:0;pointer-events:none;z-index:99999'});
  document.body.appendChild(o);
  document.querySelectorAll('button,a,input,select').forEach((e,i) => {
    const r = e.getBoundingClientRect();
    const b = Object.assign(document.createElement('div'),
      {style:'position:absolute;border:2px solid red;background:rgba(255,0,0,0.08)'});
    Object.assign(b.style, {left:r.left+'px',top:r.top+'px',width:r.width+'px',height:r.height+'px'});
    const l = Object.assign(document.createElement('span'), {textContent:'@e'+(i+1)});
    l.style.cssText = 'position:absolute;top:-16px;left:0;background:red;color:#fff;font:10px monospace;padding:1px 3px';
    b.appendChild(l); o.appendChild(b);
  });
  const p = await tab.screenshot({ silent: true }); o.remove(); p
" }
```

## CSS inspection — computed styles
```
xd://browser { "action": "run", "name": "main",
  "code": "tab.evaluate(() => { const el=document.querySelector('.el');"+
    "if(!el)return; const cs=getComputedStyle(el);"+
    "return ['color','background-color','font-size','display','margin','padding',"+
    "'border','opacity'].reduce((o,k)=>{o[k]=cs.getPropertyValue(k);return o;},{}) })" }
```

## Page cleanup — remove sticky banners, cookie notices
```
xd://browser { "action": "run", "name": "main", "code": "
  document.querySelectorAll('div[class*=\"cookie\"],div[class*=\"banner\"],"+
    'div[class*=\"sticky\"],div[class*=\"consent\"],div[id*=\"cookie\"]').forEach(e => e.remove());
  document.querySelectorAll('header,footer').forEach(e => e.style.position='static');
  'cleaned'
" }
```

## URL content diff — compare two pages by extracting text
```
xd://browser { "action": "run", "name": "main",
  "code": "const r1=await(await fetch(url1)).text();"+
    "const r2=await(await fetch(url2)).text();"+
    "{len1:r1.length,len2:r2.length,same:r1===r2}" }
```
