from pathlib import Path
import json, hashlib, base64, re, sys
p=Path(sys.argv[1]); v='0.7.0'
if json.loads((p/'release.json').read_text())['version']!='0.6.2':
 raise ValueError('Expected original release 0.6.2')
def edit(name, pairs):
 f=p/name;s=f.read_text()
 for a,b in pairs:
  if s.count(a)!=1: raise ValueError((name,a,s.count(a)))
  s=s.replace(a,b,1)
 f.write_text(s)
(p/'css/adventure.css').write_text(Path(__file__).with_name('adventure.css').read_text())
edit('index.html',[('</head>','<link rel="stylesheet" href="css/adventure.css"></head>')])
edit('js/core.js',[("effects: true, music:","effects: true, motion: true, music:"),("    effects: value => typeof value === 'boolean',","    effects: value => typeof value === 'boolean',\n    motion: value => typeof value === 'boolean',")])
edit('js/app.js',[
("let installingPiper=false, pendingUpdate=null;","let installingPiper=false, pendingUpdate=null, installDismissed=false, lastRenderedPage='', registration=null;"),
(" rootElement.dataset.theme=theme();"," rootElement.dataset.theme=theme();\n rootElement.dataset.motion=C.current().preferences.motion===false?'off':'on';"),
("function home(){","""function installStrip(){return installed||installDismissed||!window.isSecureContext||location.protocol==='file:'?'':`<section class="az-install" aria-label="Установка приложения"><div><b>Азбука на твоём устройстве</b><small>${offlineMessage()}</small></div><button class="btn btn-primary" data-action="install-app">Установить приложение</button><button class="az-close" data-action="dismiss-install" aria-label="Скрыть предложение установки">×</button></section>`;}
function countPractice(l){const n=Number(l.topic);if(!['digit','count'].includes(l.type)||!Number.isInteger(n)||n<0||n>20)return '';return `<section class="az-count"><h3>Посчитай яблоки</h3><p>${n?'Нажимай на каждое яблоко один раз.':'Здесь нет яблок. Это число ноль.'}</p><div class="az-apples">${Array.from({length:n},(_,i)=>`<button type="button" class="az-apple" data-action="count-practice" aria-label="Яблоко ${i+1}" aria-pressed="false">🍎<span></span></button>`).join('')}</div><output aria-live="polite">0 / ${n}</output><button type="button" class="btn btn-soft" data-action="count-reset">Ещё раз</button></section>`;}
function home(){"""),
('<div class="home-screen"><section class="hero">','<div class="home-screen">${installStrip()}<section class="hero">'),
('+lessonTeach(l)+`<div class="answer-actions">','+lessonTeach(l)+countPractice(l)+`<div class="answer-actions">'),
("  ['contrast','Контраст',[[false,'Обычный'],[true,'Повышенный']]],","  ['contrast','Контраст',[[false,'Обычный'],[true,'Повышенный']]],\n  ['motion','Анимации',[[true,'Включены'],[false,'Выключены']]],"),
("key==='contrast'?value==='true':value","['contrast','motion'].includes(key)?value==='true':value"),
('<button class="btn btn-soft" data-action="offline-check">Проверить готовность</button>','<button class="btn btn-soft" data-action="offline-check">Проверить готовность</button><button class="btn btn-soft" data-action="check-update">Проверить обновления</button>'),
(" document.title='Азбука приключений — '"," if(lastRenderedPage!==page){root.querySelector('#main')?.classList.add('az-enter');lastRenderedPage=page;}\n document.title='Азбука приключений — '"),
(" checkpoint();render();\n}\nfunction nextStep()"," checkpoint();render();\n root.querySelector('.feedback')?.classList.add(correct?'az-correct':'az-retry');\n}\nfunction nextStep()"),
(" if(status)status.textContent=offlineMessage();"," if(status)status.textContent=offlineMessage();\n const strip=root.querySelector('.az-install small');if(strip)strip.textContent=offlineMessage();"),
(" case 'apply-update':",""" case 'count-practice': {
  if(el.getAttribute('aria-pressed')==='true')break;
  const lab=el.closest('.az-count');if(!lab)break;
  el.setAttribute('aria-pressed','true');const n=lab.querySelectorAll('.az-apple[aria-pressed=true]').length;
  el.querySelector('span').textContent=n;lab.querySelector('output').textContent=n+' / '+lab.querySelectorAll('.az-apple').length;speak(String(n));break;
 }
 case 'count-reset': {
  const lab=el.closest('.az-count');if(!lab)break;const buttons=lab.querySelectorAll('.az-apple');
  buttons.forEach(b=>{b.setAttribute('aria-pressed','false');b.querySelector('span').textContent='';});lab.querySelector('output').textContent='0 / '+buttons.length;break;
 }
 case 'dismiss-install':installDismissed=true;el.closest('.az-install')?.remove();break;
 case 'check-update':
  if(!registration){toast('Обновление доступно только в защищённом браузере.');break;}
  try{await registration.update();toast(registration.waiting?'Обновление готово к применению.':registration.installing?'Загружается обновление.':'Новых обновлений пока нет.');}catch{toast('Не удалось проверить обновления. Проверьте интернет.');}break;
 case 'apply-update':"""),
("if(page==='parent')render();});\nif('serviceWorker'", "if(page==='parent'||page==='home')render();});\nif('serviceWorker'"),
(".then(reg=>{\n  checkOffline();", ".then(reg=>{\n  registration=reg;\n  checkOffline();"),
("const ix=Number(el.dataset.index);const id=el.dataset.id;", "const ix=Number(el.dataset.index);const id=el.dataset.id;\n if(el.matches('.task-speaker,.btn-sound')||action.includes('sound')){el.classList.remove('az-speak');void el.offsetWidth;el.classList.add('az-speak');}")])
release=json.loads((p/'release.json').read_text());release['version']=v;(p/'release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n')
manifest=json.loads((p/'manifest.webmanifest').read_text());manifest['id']='./index.html';(p/'manifest.webmanifest').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':'))+'\n')
for name in ['README_RU.txt','README.txt']:
 f=p/name;s=f.read_text().replace('v0.6.2','v0.7.0');f.write_text(s+'\n0.7.0: обновлён интерфейс, отключаемая анимация, дополнительный счёт предметов, установка и ручная проверка обновлений. Курс письма и прогресс сохранены.\n')
sw=p/'sw.js';s=sw.read_text();match=re.search(r'const manifest=(\[.*?\]);',s);entries=json.loads(match[1]);entries.append({'url':'css/adventure.css'});
for e in entries:
 data=(p/('index.html' if e['url']=='./' else e['url'])).read_bytes();h=hashlib.sha256(data);e['revision']=h.hexdigest()[:24]
 if e['url']!='./':e['integrity']='sha256-'+base64.b64encode(h.digest()).decode()
sw.write_text(s[:match.start(1)]+json.dumps(entries,separators=(',',':'))+s[match.end(1):])
