/*!
 * browser_check.js — 用 CDP 驱动本机 Edge/Chrome 打开 web/index.html 做真实浏览器验证。
 * 不依赖 puppeteer：Node 22+ 自带全局 WebSocket/fetch。
 *
 *   node _verify/browser_check.js [端口] [URL]
 *
 * 做四件事：
 *   1. 加载页面，收集 Runtime.exceptionThrown / console.error / Log.error
 *   2. 检查全局：YSB 模块、navigator.bluetooth、crypto.subtle
 *   3. canvas 生成 800x480 PNG -> DataTransfer -> drop 事件，跑完整真实编码管线
 *   4. 点自检按钮、切换预览视图，再抓一轮错误；最后读回界面各字段
 */
const PORT = parseInt(process.argv[2] || '9333', 10);
const URL = process.argv[3] || ('file:///' + require('path').resolve(__dirname, '..', 'web', 'index.html')
  .replace(/\\/g, '/'));
const NL = String.fromCharCode(10);

async function httpJson(p) {
  const r = await fetch('http://127.0.0.1:' + PORT + p);
  return r.json();
}
function cdp(ws) {
  let id = 0; const pending = new Map(); const events = [];
  ws.addEventListener('message', function (ev) {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const pr = pending.get(msg.id); pending.delete(msg.id);
      if (msg.error) pr.reject(new Error(JSON.stringify(msg.error))); else pr.resolve(msg.result);
    } else if (msg.method) events.push(msg);
  });
  return {
    events: events,
    call: function (method, params) {
      return new Promise(function (resolve, reject) {
        const i = ++id; pending.set(i, { resolve: resolve, reject: reject });
        ws.send(JSON.stringify({ id: i, method: method, params: params || {} }));
        setTimeout(function () { if (pending.has(i)) { pending.delete(i); reject(new Error('timeout ' + method)); } }, 30000);
      });
    }
  };
}
function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

(async function () {
  const targets = await httpJson('/json/list');
  const pages = targets.filter(function (t) { return t.type === 'page'; });
  let page = pages.filter(function (t) { return t.url.indexOf('file:') === 0; })[0] || pages[0];
  if (!page) { console.log('没有页面目标：' + JSON.stringify(targets.map(function (t) { return t.url; }))); process.exit(2); }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise(function (res, rej) { ws.addEventListener('open', res); ws.addEventListener('error', rej); });
  const c = cdp(ws);
  await c.call('Runtime.enable');
  await c.call('Log.enable');
  await c.call('Page.enable');
  const errors = [], logs = [];
  function drain() {
    for (const ev of c.events.splice(0)) {
      if (ev.method === 'Runtime.exceptionThrown') {
        const d = ev.params.exceptionDetails;
        errors.push('EXCEPTION ' + ((d.exception && d.exception.description) || d.text) + '  @' + (d.url || '') + ':' + (d.lineNumber + 1));
      } else if (ev.method === 'Runtime.consoleAPICalled') {
        const t = ev.params.args.map(function (a) { return a.value !== undefined ? a.value : (a.description || a.type); }).join(' ');
        logs.push(ev.params.type + ': ' + t);
        if (ev.params.type === 'error') errors.push('CONSOLE.ERROR ' + t);
      } else if (ev.method === 'Log.entryAdded') {
        const e = ev.params.entry;
        logs.push('log.' + e.level + ': ' + e.text);
        if (e.level === 'error') errors.push('LOG.ERROR ' + e.text + ' @' + (e.url || ''));
      }
    }
  }
  await c.call('Page.navigate', { url: URL });
  await sleep(2500);
  drain();
  console.log('== 1. 页面加载 ==');
  console.log('   title: ' + (await c.call('Runtime.evaluate', { expression: 'document.title', returnByValue: true })).result.value);
  const g = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({ysb: typeof YSB, bt: typeof navigator.bluetooth, subtle: !!(window.crypto && window.crypto.subtle), st: YSB ? YSB.selftest().ok : null})' });
  const gi = JSON.parse(g.result.value);
  console.log('   YSB=' + gi.ysb + '  navigator.bluetooth=' + gi.bt + '  crypto.subtle=' + gi.subtle + '  core selftest=' + gi.st);

  console.log('== 2. 真实编码管线（drop 一张 canvas 生成的 PNG）==');
  const dropExpr = [
    '(function(){',
    '  var c=document.createElement("canvas");c.width=800;c.height=480;',
    '  var x=c.getContext("2d");var im=x.createImageData(800,480);',
    '  for(var y=0;y<480;y++)for(var xx=0;xx<800;xx++){var o=(y*800+xx)*4;',
    '    im.data[o]=(xx*255/800)|0;im.data[o+1]=(y*255/480)|0;im.data[o+2]=((xx^y)*2)&255;im.data[o+3]=255;}',
    '  x.putImageData(im,0,0);',
    '  c.toBlob(function(b){',
    '    var dt=new DataTransfer();',
    '    dt.items.add(new File([b],"smoke.png",{type:"image/png"}));',
    '    document.getElementById("drop").dispatchEvent(new DragEvent("drop",{dataTransfer:dt,bubbles:true,cancelable:true}));',
    '  },"image/png");',
    '  return "dispatched";',
    '})()'
  ].join(NL);
  await c.call('Runtime.evaluate', { returnByValue: true, expression: dropExpr });
  await sleep(4500);
  drain();
  const st = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({raw:document.getElementById("e-raw").textContent,' +
    'comp:document.getElementById("e-comp").textContent,ratio:document.getElementById("e-ratio").textContent,' +
    'rt:document.getElementById("e-rt").textContent,init:document.getElementById("f-init").textContent,' +
    'info:document.getElementById("f-info").textContent,chunks:document.getElementById("f-chunks").textContent,' +
    'hash:document.getElementById("e-hash").textContent.slice(0,20),time:document.getElementById("e-time").textContent,' +
    'hist:document.getElementById("hist").rows.length,loglines:document.getElementById("log").childNodes.length,' +
    'view:document.getElementById("view-info").textContent,nameA:document.getElementById("name-a").textContent})' });
  const info = JSON.parse(st.result.value);
  console.log('   源图: ' + info.nameA);
  console.log('   pic_data: ' + info.raw);
  console.log('   压缩: ' + info.comp);
  console.log('   占上限: ' + info.ratio);
  console.log('   往返: ' + info.rt + '   sha256: ' + info.hash);
  console.log('   INIT: ' + info.init);
  console.log('   PIC_INFO: ' + info.info);
  console.log('   分块: ' + info.chunks);
  console.log('   耗时: ' + info.time);
  console.log('   直方图行数: ' + info.hist + '（期望 8 = 表头+7 色）  日志行数: ' + info.loglines);
  console.log('   预览: ' + info.view);

  console.log('== 3. 实时联动与预设 ==');
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    '(function(){var s=document.getElementById("p-dither");s.value="fs";' +
    's.dispatchEvent(new Event("input",{bubbles:true}));return 1})()' });
  await sleep(2500);
  drain();
  const c1 = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.getElementById("e-comp").textContent' });
  console.log('   切 fs 后: ' + c1.result.value);
  if (c1.result.value === info.comp) errors.push('实时联动无效：参数改动后结果没变');
  // 超限自救：fs 超限后点「关抖动重算」，应回到 none 且体积降回限内
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.getElementById("over-fix").click();1' });
  await sleep(2500);
  drain();
  const fx = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({d:document.getElementById("p-dither").value,c:document.getElementById("e-comp").textContent})' });
  const jf = JSON.parse(fx.result.value);
  console.log('   超限自救: 点「关抖动重算」后 dither=' + jf.d + ' -> ' + jf.c);
  if (jf.d !== 'none') errors.push('超限自救未关闭抖动: ' + jf.d);
  if (jf.c !== info.comp) errors.push('超限自救后体积未回到初值: ' + jf.c + ' != ' + info.comp);
  const lay = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth})' });
  const l = JSON.parse(lay.result.value);
  console.log('   页面宽度 ' + l.sw + ' / 视口 ' + l.cw + (l.sw > l.cw + 2 ? '  <== 横向溢出' : '  无横向溢出'));
  if (l.sw > l.cw + 2) errors.push('布局横向溢出 ' + l.sw + ' > ' + l.cw);
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.getElementById("btn-preset-photo").click();1' });
  await sleep(2200);
  drain();
  const pv = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.getElementById("p-dither").value + "/" + document.getElementById("p-fit").value' });
  console.log('   照片预设: ' + pv.result.value + ' -> ' + (await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("e-comp").textContent' })).result.value);
  if (pv.result.value !== 'fs/fill') errors.push('照片预设未生效: ' + pv.result.value);
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.getElementById("btn-preset-text").click();1' });
  await sleep(2200);
  drain();
  const tv = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.getElementById("p-dither").value + "/" + document.getElementById("p-sharp").value' });
  console.log('   文字预设: ' + tv.result.value + ' -> ' + (await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("e-comp").textContent' })).result.value);
  if (tv.result.value !== 'none/1.6') errors.push('文字预设未生效: ' + tv.result.value);

  console.log('== 4. 按钮与视图 ==');
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.getElementById("btn-selftest").click();var t=document.querySelectorAll(".tab");t[2].click();t[1].click();t[0].click();' +
    'document.getElementById("btn-rawsend").click();"ok"' });
  await sleep(1500);
  drain();
  const st2 = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({loglines:document.getElementById("log").childNodes.length,' +
    'lastlog:document.getElementById("log").textContent.slice(-160)})' });
  const i2 = JSON.parse(st2.result.value);
  console.log('   日志行数: ' + i2.loglines);
  console.log('   末尾日志: ' + i2.lastlog.replace(/\s+/g, ' ').slice(-140));

  console.log('== 5. 第二轮新增功能 ==');
  // 帮助 overlay：? 打开 / Esc 关闭
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.dispatchEvent(new KeyboardEvent("keydown",{key:"?",bubbles:true}));1' });
  await sleep(300);
  drain();
  const h1 = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'getComputedStyle(document.getElementById("help")).display' });
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape",bubbles:true}));1' });
  await sleep(200);
  const h2 = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'getComputedStyle(document.getElementById("help")).display' });
  console.log('   帮助 overlay: ? -> ' + JSON.stringify(h1.result.value) + '，Esc -> ' + JSON.stringify(h2.result.value));
  if (h1.result.value === 'none') errors.push('? 未打开帮助 overlay（computed=' + h1.result.value + '）');
  if (h2.result.value !== 'none') errors.push('Esc 未关闭帮助 overlay（computed=' + h2.result.value + '）');
  // 自检 pill / 版本号 / title 恢复 / 超限自救钮隐藏 / 快捷填帧
  const f5 = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({self:document.getElementById("st-self").textContent,' +
    'ver:document.getElementById("ft-ver").textContent,title:document.title,' +
    'overfix:document.getElementById("over-fix").style.display,' +
    'pvB:document.getElementById("pv-b").style.display})' });
  const j5 = JSON.parse(f5.result.value);
  console.log('   自检 pill: ' + j5.self + '  footer: ' + j5.ver.slice(0, 46));
  console.log('   title: ' + JSON.stringify(j5.title) + '  超限自救钮: ' + JSON.stringify(j5.overfix) + '  B 面钮: ' + JSON.stringify(j5.pvB));
  if (j5.self !== '自检 PASS') errors.push('启动自检 pill 异常: ' + j5.self);
  if (j5.ver.indexOf('v1.2.0') < 0) errors.push('footer 版本号缺失: ' + j5.ver);
  if (j5.title !== 'YSBadge2 · Web BLE 投图台') errors.push('编码后 title 未恢复: ' + j5.title);
  if (j5.overfix !== 'none') errors.push('未超限时自救钮应隐藏: ' + j5.overfix);
  if (j5.pvB !== 'none') errors.push('无 B 面图时 B 面钮应隐藏: ' + j5.pvB);
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.getElementById("q-init").click();document.getElementById("q-update").click();1' });
  await sleep(200);
  const qv = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.getElementById("raw-hex").value' });
  console.log('   快捷填帧: q-init -> q-update 后 raw-hex = ' + JSON.stringify(qv.result.value));
  if (qv.result.value !== '03 00') errors.push('快捷填帧无效: ' + qv.result.value);

  console.log('== 6. 第三轮功能（文字/队列/方案/交换）==');
  // 文字模式
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("src-txt").click();1' });
  await sleep(2500);
  drain();
  const tm = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({mode:document.getElementById("txt-mode").style.display,' +
    'drop:document.getElementById("drop").style.display,' +
    'src:document.getElementById("e-src").textContent,raw:document.getElementById("e-raw").textContent})' });
  const jt = JSON.parse(tm.result.value);
  console.log('   文字模式: txt-mode=' + JSON.stringify(jt.mode) + ' drop=' + JSON.stringify(jt.drop) + ' | ' + jt.src + ' | pic_data ' + jt.raw);
  if (jt.mode !== '') errors.push('文字模式面板未显示');
  if (jt.src.indexOf('文字') < 0) errors.push('e-src 未反映文字模式: ' + jt.src);
  if (jt.raw.indexOf('192,000') < 0) errors.push('文字模式 pic_data 异常: ' + jt.raw);
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    '(function(){var t=document.getElementById("t-text");t.value="Hello"+String.fromCharCode(10)+"YSBadge2";' +
    't.dispatchEvent(new Event("input",{bubbles:true}));return 1})()' });
  await sleep(2500);
  drain();
  const tc = await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("e-comp").textContent' });
  console.log('   改文字后重算: ' + tc.result.value);
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("src-img").click();1' });
  await sleep(2500);
  drain();
  // B 面图 -> 自动 index 7 -> B 面预览 -> 交换 A/B
  const dropB = [
    '(function(){',
    '  var c=document.createElement("canvas");c.width=800;c.height=480;',
    '  var x=c.getContext("2d");x.fillStyle="#102030";x.fillRect(0,0,800,480);',
    '  x.fillStyle="#ffffff";x.font="bold 100px sans-serif";x.textAlign="center";',
    '  x.fillText("B SIDE",400,260);',
    '  c.toBlob(function(b){',
    '    var dt=new DataTransfer();',
    '    dt.items.add(new File([b],"side-b.png",{type:"image/png"}));',
    '    var fa=document.getElementById("file-b");',
    '    Object.defineProperty(fa,"files",{value:dt.files,configurable:true});',
    '    fa.dispatchEvent(new Event("change",{bubbles:true}));',
    '  },"image/png");',
    '  return "b-loaded";',
    '})()'
  ].join(NL);
  await c.call('Runtime.evaluate', { returnByValue: true, expression: dropB });
  await sleep(3000);
  drain();
  const j7 = JSON.parse((await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({idx:document.getElementById("p-index").value,' +
    'pvB:document.getElementById("pv-b").style.display,' +
    'src:document.getElementById("e-src").textContent})' })).result.value);
  console.log('   B 面载入: index=' + j7.idx + ' B面钮=' + JSON.stringify(j7.pvB) + ' | ' + j7.src);
  if (j7.idx !== '7') errors.push('选 B 面图后未自动 index 7: ' + j7.idx);
  if (j7.pvB !== '') errors.push('有 B 面图但 B 面预览钮仍隐藏');
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.querySelectorAll(".tab")[0].click();document.getElementById("pv-b").click();1' });
  await sleep(1200);
  const pvv = await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("view-info").textContent' });
  console.log('   B 面预览: ' + pvv.result.value);
  if (pvv.result.value.indexOf('B 面') < 0) errors.push('切 B 面预览无效: ' + pvv.result.value);
  const nb = await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("name-b").textContent' });
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("btn-swap").click();1' });
  await sleep(2500);
  drain();
  const na = await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("name-a").textContent' });
  console.log('   交换 A/B: name-a 「' + nb.result.value + '」->「' + na.result.value + '」');
  if (na.result.value !== nb.result.value) errors.push('A/B 交换无效');
  // 预览 PNG 导出（headless 下载静默，靠日志确认）
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("btn-exportpng").click();1' });
  await sleep(900);
  drain();
  const ep = await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'document.getElementById("log").textContent.indexOf("已导出预览 PNG")>=0' });
  if (!ep.result.value) errors.push('预览 PNG 导出未记日志');
  // 发送队列
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("btn-enqueue").click();1' });
  await sleep(600);
  const jq = JSON.parse((await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({n:document.getElementById("q-count").textContent,' +
    'items:document.getElementById("q-list").querySelectorAll(".qi").length})' })).result.value);
  console.log('   队列: ' + jq.n + '，列表项 ' + jq.items);
  if (jq.items !== 1) errors.push('加入队列后列表项应为 1，实际 ' + jq.items);
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("btn-qclear").click();1' });
  await sleep(300);
  const jq2 = await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("q-count").textContent' });
  if (jq2.result.value.indexOf('队列 0') < 0) errors.push('清空队列无效: ' + jq2.result.value);
  // 参数方案（prompt 打桩）
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'window.prompt=function(){return "浏览器验证方案"};document.getElementById("prof-save").click();1' });
  await sleep(400);
  const jp = JSON.parse((await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({opts:document.getElementById("prof-sel").options.length,' +
    'val:document.getElementById("prof-sel").value})' })).result.value);
  console.log('   参数方案: options=' + jp.opts + ' 选中「' + jp.val + '」');
  if (jp.opts < 2 || jp.val !== '浏览器验证方案') errors.push('参数方案保存无效: ' + JSON.stringify(jp));
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("prof-del").click();1' });
  await sleep(300);
  const p2 = await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("prof-sel").options.length' });
  if (parseInt(p2.result.value, 10) !== 1) errors.push('参数方案删除无效: ' + p2.result.value);

  console.log('== 8. A/B 设置友好化 ==');
  const ab1 = JSON.parse((await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({need:document.getElementById("b-needimg").style.display,' +
    'share:document.getElementById("a-share").style.display,' +
    'pv:document.getElementById("b-pv").style.display,' +
    'clr:document.getElementById("b-clear").style.display})' })).result.value);
  console.log('   有 B 图: 缺图引导=' + JSON.stringify(ab1.need) + ' A/B共用标记=' + JSON.stringify(ab1.share) +
              ' 预览中=' + JSON.stringify(ab1.pv) + ' 清除钮=' + JSON.stringify(ab1.clr));
  if (ab1.need !== 'none') errors.push('有 B 面图但缺图引导仍显示');
  if (ab1.share !== '') errors.push('index 7 时 A/B 共用标记应显示');
  if (ab1.pv !== '') errors.push('预览 B 面时应显示「预览中」');
  if (ab1.clr !== '') errors.push('有 B 面图时清除钮应显示');
  // 清除 B 面 -> index 回 1，引导/标记/预览钮/清除钮全部隐藏
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("b-clear").click();1' });
  await sleep(2500);
  drain();
  const ab2 = JSON.parse((await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({idx:document.getElementById("p-index").value,' +
    'need:document.getElementById("b-needimg").style.display,' +
    'share:document.getElementById("a-share").style.display,' +
    'clr:document.getElementById("b-clear").style.display,' +
    'pvB:document.getElementById("pv-b").style.display})' })).result.value);
  console.log('   清除 B 面: index=' + ab2.idx + ' 引导=' + JSON.stringify(ab2.need) + ' 标记=' + JSON.stringify(ab2.share) + ' B面钮=' + JSON.stringify(ab2.pvB));
  if (ab2.idx !== '1') errors.push('清除 B 面后 index 应回 1: ' + ab2.idx);
  if (ab2.need !== 'none') errors.push('无 B 面图时缺图引导应隐藏');
  if (ab2.share !== 'none') errors.push('index 1 时 A/B 共用标记应隐藏');
  if (ab2.clr !== 'none') errors.push('无 B 面图时清除钮应隐藏');
  if (ab2.pvB !== 'none') errors.push('无 B 面图时 B 面预览钮应隐藏');
  // 手动 index 7 但无 B 图：引导出现 + B 区自动展开
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    '(function(){document.getElementById("b-side").open=false;' +
    'var s=document.getElementById("p-index");s.value="7";' +
    's.dispatchEvent(new Event("change",{bubbles:true}));return 1})()' });
  await sleep(2500);
  drain();
  const ab3 = JSON.parse((await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({need:document.getElementById("b-needimg").style.display,' +
    'open:document.getElementById("b-side").open})' })).result.value);
  console.log('   index 7 无 B 图: 缺图引导=' + JSON.stringify(ab3.need) + ' B区自动展开=' + ab3.open);
  if (ab3.need !== '') errors.push('index 7 无 B 图时应显示缺图引导');
  if (ab3.open !== true) errors.push('index 7 时 B 面区应自动展开');
  // 「跟 A 面一样」：A 面设 fs，点复制 -> dither2=fs、fill2 跟随 fit
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    '(function(){var s=document.getElementById("p-index");s.value="1";' +
    's.dispatchEvent(new Event("change",{bubbles:true}));' +
    'var d=document.getElementById("p-dither");d.value="fs";' +
    'd.dispatchEvent(new Event("input",{bubbles:true}));return 1})()' });
  await sleep(2500);
  drain();
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("b-same").click();1' });
  await sleep(1200);
  const ab4 = JSON.parse((await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({d2:document.getElementById("p-dither2").value,' +
    'f2:document.getElementById("p-fill2").checked})' })).result.value);
  console.log('   跟 A 面一样: dither2=' + ab4.d2 + ' fill2=' + ab4.f2);
  if (ab4.d2 !== 'fs') errors.push('「跟 A 面一样」未复制抖动: ' + ab4.d2);
  if (ab4.f2 !== false) errors.push('「跟 A 面一样」fill2 应跟随 fit=contain 为 false');
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    '(function(){var d=document.getElementById("p-dither");d.value="none";' +
    'd.dispatchEvent(new Event("input",{bubbles:true}));' +
    'var d2=document.getElementById("p-dither2");d2.value="none";' +
    'd2.dispatchEvent(new Event("input",{bubbles:true}));return 1})()' });
  await sleep(2500);
  drain();

  const cr0 = await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("e-comp").textContent' });
  console.log('   裁剪前基线: ' + cr0.result.value);
  console.log('== 9. 裁剪 UI ==');
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("crop-a-btn").click();1' });
  await sleep(600);
  drain();
  const cr1 = JSON.parse((await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({vis:getComputedStyle(document.getElementById("crop")).display,' +
    'cw:document.getElementById("crop-cv").width,ch:document.getElementById("crop-cv").height,' +
    'pos:getComputedStyle(document.getElementById("crop")).position,' +
    'rect:(function(){var r=document.querySelector("#crop .card").getBoundingClientRect();' +
    'return [Math.round(r.left),Math.round(r.top),Math.round(r.right),Math.round(r.bottom),window.innerWidth,window.innerHeight];})()})' })).result.value);
  console.log('   打开裁剪: overlay=' + cr1.vis + ' position=' + cr1.pos + ' 画布 ' + cr1.cw + 'x' + cr1.ch + ' card 矩形 ' + JSON.stringify(cr1.rect));
  if (cr1.vis !== 'flex') errors.push('裁剪 overlay 应为 flex 弹层，实际 ' + cr1.vis);
  if (cr1.pos !== 'fixed') errors.push('裁剪 overlay 应 fixed 定位，实际 ' + cr1.pos);
  if (cr1.cw < 100) errors.push('裁剪画布尺寸异常: ' + cr1.cw);
  if (cr1.rect[0] < 0 || cr1.rect[1] < 0 || cr1.rect[2] > cr1.rect[4] + 1 || cr1.rect[3] > cr1.rect[5] + 1)
    errors.push('裁剪弹窗不在视口内: ' + JSON.stringify(cr1.rect));
  // 合成拖拽画新框（整图状态下框内拖动=画新框）
  await c.call('Runtime.evaluate', { returnByValue: true, expression:
    '(function(){var cv=document.getElementById("crop-cv");var r=cv.getBoundingClientRect();' +
    'function pe(t,x,y){cv.dispatchEvent(new PointerEvent(t,{clientX:x,clientY:y,bubbles:true,pointerId:1}));}' +
    'pe("pointerdown",r.left+60,r.top+60);pe("pointermove",r.left+300,r.top+180);' +
    'pe("pointerup",r.left+300,r.top+180);return 1})()' });
  await sleep(400);
  const cr2 = await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("crop-dim").textContent' });
  console.log('   拖拽后: ' + cr2.result.value);
  if (cr2.result.value.indexOf('裁剪') < 0) errors.push('裁剪尺寸读数异常: ' + cr2.result.value);
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("crop-ok").click();1' });
  await sleep(2500);
  drain();
  const cr3 = JSON.parse((await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({vis:getComputedStyle(document.getElementById("crop")).display,' +
    'src:document.getElementById("e-src").textContent,comp:document.getElementById("e-comp").textContent,' +
    'badge:document.getElementById("crop-a-btn").textContent})' })).result.value);
  console.log('   应用裁剪: overlay=' + cr3.vis + ' | ' + cr3.src + ' | ' + cr3.comp + ' | 钮「' + cr3.badge + '」');
  if (cr3.vis !== 'none') errors.push('应用后 overlay 未关闭');
  if (cr3.src.indexOf('裁') < 0) errors.push('e-src 未显示裁剪信息: ' + cr3.src);
  if (cr3.comp === cr0.result.value) errors.push('裁剪后体积没变（裁剪可能未生效）');
  if (cr3.badge.indexOf('ok') < 0) errors.push('裁剪按钮未标记激活: ' + cr3.badge);
  // 清除裁剪 -> 恢复
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("crop-a-btn").click();1' });
  await sleep(400);
  await c.call('Runtime.evaluate', { returnByValue: true, expression: 'document.getElementById("crop-clear").click();1' });
  await sleep(2500);
  drain();
  const cr4 = JSON.parse((await c.call('Runtime.evaluate', { returnByValue: true, expression:
    'JSON.stringify({src:document.getElementById("e-src").textContent,' +
    'comp:document.getElementById("e-comp").textContent})' })).result.value);
  console.log('   清除裁剪: ' + cr4.src + ' | ' + cr4.comp);
  if (cr4.src.indexOf('裁') >= 0) errors.push('清除裁剪后 e-src 仍显示裁剪: ' + cr4.src);
  if (cr4.comp !== cr0.result.value) errors.push('清除裁剪后体积未恢复: ' + cr4.comp + ' != ' + cr0.result.value);

  console.log('== 10. 错误汇总 ==');
  if (errors.length) {
    console.log('   发现 ' + errors.length + ' 个错误：');
    errors.slice(0, 20).forEach(function (e) { console.log('   !! ' + e.split(NL)[0]); });
  } else {
    console.log('   无异常、无 console.error');
  }
  const ok = errors.length === 0 && /bit/.test(info.comp) && /OK/.test(info.rt) &&
             info.init.indexOf('00 06 01') >= 0 && info.hist === 8 && gi.st === true;
  console.log('');
  console.log(ok ? '==== 浏览器验证通过 ====' : '==== 浏览器验证失败 ====');
  try { ws.close(); } catch (e) {}
  process.exit(ok ? 0 : 1);
})().catch(function (e) { console.log('驱动失败: ' + e.message); process.exit(3); });
