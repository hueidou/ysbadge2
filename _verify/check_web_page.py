# -*- coding: utf-8 -*-
"""web/ 页面校验（无浏览器也能跑）：

  1. 语法：抽出 index.html 全部内联 <script>，逐个 node --check
  2. 模块：require web/ysbadge-core.js 并跑其 selftest
  3. 引用：胶水层引用的 id 都存在于 HTML
  4. 冒烟 A（编码管线）：DOM shim 下 loadFile -> encode -> 直方图 -> 视图 -> 按钮
  5. 冒烟 B（BLE 发送）：形状逼真的 fake Web Bluetooth（properties 为布尔字典），
     点「扫描/选择设备」-> 连接 -> 发送，校验 ff02/ff03 上实际写入的字节与分块

    python _verify/check_web_page.py

实现说明：全文不使用带反斜杠的正则，抽取/核对都走字符串操作与字符类，
避免转义层数出错（曾因此把校验器本身写坏）。
"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import sys, os, re, json, subprocess, tempfile

ROOT = _ROOT
HTML = ROOT + r"/web/index.html"
CORE = ROOT + r"/web/ysbadge-core.js"
NL = chr(10)

ID_DEF_RE = re.compile(r'id="([^"]+)"')
ID_USE_RE = re.compile(r"[$][(]'([^']+)'[)]")
IND1_RE = re.compile(r"setPill[(]'([^']+)'")
IND2_RE = re.compile(r"'([a-z0-9-]+)','p-[a-z0-9-]+'")

def extract_scripts(txt):
    out, pos = [], 0
    while True:
        i = txt.find("<script", pos)
        if i < 0:
            break
        gt = txt.find(">", i)
        j = txt.find("</script>", gt)
        if gt < 0 or j < 0:
            break
        if "src=" not in txt[i:gt]:
            out.append(txt[gt + 1:j])
        pos = j + 9
    return out

SMOKE = r"""
const fs = require('fs');
const htmlPath = process.argv[2], outPath = process.argv[3], corePath = process.argv[4];
const txt = fs.readFileSync(htmlPath, 'utf8');
function extractGlue(t) {
  let pos = 0;
  for (;;) {
    const i = t.indexOf('<script', pos);
    if (i < 0) return null;
    const gt = t.indexOf('>', i), j = t.indexOf('</script>', gt);
    if (gt < 0 || j < 0) return null;
    if (t.slice(i, gt).indexOf('src=') < 0) return t.slice(gt + 1, j);
    pos = j + 9;
  }
}
const glue = extractGlue(txt);
if (!glue) { console.error('no inline script'); process.exit(3); }
const report = { errors: [], notes: [] };

function pattern(w, h) {
  const d = new Uint8ClampedArray(w * h * 4);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const o = (y * w + x) * 4;
    d[o] = (x * 255 / w) | 0; d[o+1] = (y * 255 / h) | 0; d[o+2] = ((x ^ y) * 2) & 255; d[o+3] = 255;
  }
  return d;
}
function mkCtx(cv) {
  return {
    canvas: cv, _filter: '',
    set filter(v) { this._filter = v; }, get filter() { return this._filter; },
    setTransform() {}, clearRect() {}, fillRect() {}, drawImage() {},
    getImageData(x, y, w, h) { return { width: w, height: h, data: pattern(w, h) }; },
    putImageData() {}, createImageData(w, h) { return { width: w, height: h, data: new Uint8ClampedArray(w*h*4) }; },
    imageSmoothingEnabled: true, imageSmoothingQuality: 'high'
  };
}
const DEFAULTS = {'p-index':'1','p-fit':'contain','p-dither':'none','p-spread':'128','p-sat':'1',
  'p-contrast':'1','p-bright':'1','p-sharp':'1','p-noise':'0','p-seed':'1','p-chunk':'244','p-pace':'40',
  'p-lenmode':'bits','p-zoom':'62','p-dither2':'none','raw-target':'ff03','raw-hex':'00 06 01'};
const els = {};
function mkEl(id) {
  const e = {
    id: id, className: '', textContent: '', innerHTML: '', disabled: false, checked: false,
    value: (DEFAULTS[id] !== undefined ? DEFAULTS[id] : ''), style: {}, width: 800, height: 480,
    scrollTop: 0, scrollHeight: 0, childNodes: [], firstChild: null, _html: 0,
    classList: { add() {}, remove() {}, contains() { return false; } },
    appendChild(c) { this.childNodes.push(c); },
    removeChild() { this.childNodes.shift(); },
    insertAdjacentHTML(pos, html) { var n = (String(html).match(/<tr>/g) || []).length; this._html += n; this.rows.length += n; },
    getContext() { return mkCtx(this); },
    addEventListener: function (t, f) { (this._ev = this._ev || {})[t] = (this._ev[t] || []).concat([f]); },
    removeEventListener: function () {},
    dispatchEvent: function (ev) { ev.target = ev.target || this; var l = (this._ev && this._ev[ev.type]) || [];
      for (var i = 0; i < l.length; i++) l[i](ev); return true; },
    getAttribute(k) { return this['data-' + k] || ''; },
    rows: { length: 1 }, deleteRow() { if (this.rows.length > 1) this.rows.length--; }
  };
  ['onclick','oninput','onchange','ondragover','ondragleave','ondrop'].forEach(function (k) {
    Object.defineProperty(e, k, { get: function () { return this['_' + k] || null; },
                                  set: function (f) { this['_' + k] = f; }, configurable: true });
  });
  return e;
}
const tabs = [mkEl('tab-quant'), mkEl('tab-src'), mkEl('tab-nib')];
tabs[0]['data-view'] = 'quant'; tabs[1]['data-view'] = 'src'; tabs[2]['data-view'] = 'nib';

// ---- 形状逼真的 fake Web Bluetooth：properties 是布尔字典（真实 API 的形状）----
function mkChar(name, props) {
  return {
    uuid: name, properties: props, writes: [],
    startNotifications: async function () { this._n = true; },
    stopNotifications: async function () { this._n = false; },
    addEventListener: function () {},
    writeValueWithResponse: async function (v) { this.writes.push(Array.from(v)); },
    writeValueWithoutResponse: async function (v) { this.writes.push(Array.from(v)); }
  };
}
const chPic = mkChar('ff02', { write: true, writeWithoutResponse: true, notify: false, read: false });
const chCmd = mkChar('ff03', { write: true, writeWithoutResponse: false, notify: false, read: false });
const chNot = mkChar('ff04', { write: false, writeWithoutResponse: false, notify: true, read: true });
const fakeSvc = {
  getCharacteristic: async function (u) {
    if (u.indexOf('ff02') >= 0) return chPic;
    if (u.indexOf('ff03') >= 0) return chCmd;
    return chNot;
  }
};
const fakeServer = { getPrimaryService: async function () { return fakeSvc; } };
const fakeDev = {
  id: 'fake-dev-1', name: 'YSBadge2',
  gatt: { connected: false, connect: async function () { this.connected = true; return fakeServer; },
          disconnect: function () { this.connected = false; } },
  addEventListener: function () {}
};

// Node 21+ 的 navigator/performance 是只读全局，必须 defineProperty 覆盖
function defGlobal(name, val) {
  try { Object.defineProperty(globalThis, name, { value: val, configurable: true, writable: true }); }
  catch (e) { globalThis[name] = val; }
}
defGlobal('document', {
  getElementById: function (id) { return els[id] || (els[id] = mkEl(id)); },
  createElement: function (t) { return mkEl('cv:' + t); },
  querySelectorAll: function () { return tabs; },
  addEventListener: function () {}
});
defGlobal('window', { addEventListener() {}, crypto: { subtle: { digest: async function () { return new ArrayBuffer(32); } } } });
defGlobal('localStorage', { getItem() { return null; }, setItem() {} });
defGlobal('performance', { now: function () { return Date.now(); } });
defGlobal('navigator', { bluetooth: {
  requestDevice: async function () { return fakeDev; },
  getDevices: async function () { return []; }
} });
defGlobal('createImageBitmap', async function () { return { width: 800, height: 480 }; });
global.YSB = require(corePath);

try { (0, eval)(glue); report.notes.push('胶水加载 + wire() 完成'); }
catch (e) { report.errors.push('胶水加载/wire(): ' + e.message); }
function fire(id) {
  try { const h = els[id] && els[id]._onclick; if (h) { const r = h({}); if (r && r.catch) r.catch(function (e2) { report.errors.push(id + ': ' + e2.message); }); } }
  catch (e) { report.errors.push(id + ' 点击: ' + e.message); }
}
(async function () {
  const wait = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  try {
    const fa = els['file-a'];
    if (fa && fa._onchange) { const r = fa._onchange({ target: { files: [{ name: 'smoke.png' }] } }); if (r && r.catch) r.catch(function (e) { report.errors.push('loadFile: ' + e.message); }); }
    await wait(1200);
    fire('btn-scan');
    await wait(900);
    if (!els['st-conn'] || els['st-conn'].textContent.indexOf('已连接') < 0)
      report.errors.push('fake GATT 连接后状态不是「已连接」');
    fire('btn-send');
    await wait(7000);
    const hex = function (a) { return a.map(function (b) { return ('0' + b.toString(16)).slice(-2); }).join(' '); };
    if (chCmd.writes.length < 2) report.errors.push('ff03 写入不足 2 帧，实际 ' + chCmd.writes.length);
    else {
      report.notes.push('ff03[0] INIT ' + hex(chCmd.writes[0]));
      report.notes.push('ff03[1] PIC_INFO ' + hex(chCmd.writes[1]));
      if (hex(chCmd.writes[0]) !== '00 06 01') report.errors.push('INIT 帧错: ' + hex(chCmd.writes[0]));
      const info = chCmd.writes[1];
      if (info[0] !== 1 || info[1] !== 1) report.errors.push('PIC_INFO 头错: ' + hex(info));
      const decl = info[2] | (info[3] << 8) | (info[4] << 16) | (info[5] << 24);
      if (decl !== 63298) report.errors.push('PIC_INFO len 应为 63298 比特，实际 ' + decl);
    }
    if (!chPic.writes.length) report.errors.push('ff02 没有写入任何数据块');
    else {
      const total = chPic.writes.reduce(function (s, w) { return s + w.length; }, 0);
      const sizes = {}; chPic.writes.forEach(function (w) { sizes[w.length] = (sizes[w.length] || 0) + 1; });
      report.notes.push('ff02 写入 ' + chPic.writes.length + ' 块共 ' + total + ' B，分块分布 ' + JSON.stringify(sizes));
      if (total !== 7913) report.errors.push('ff02 总字节应为 7913，实际 ' + total);
      const bad = chPic.writes.filter(function (w) { return w.length > 244; });
      if (bad.length) report.errors.push('有 ' + bad.length + ' 块超过 244 B');
    }
    if (!els['log'] || els['log'].childNodes.length < 5) report.errors.push('日志过少');
    // ---- 实时联动：改参数不发点击，也应自动重算并刷新结果 ----
    const before = els['e-comp'].textContent;
    els['p-dither'].value = 'fs';
    els['p-dither'].dispatchEvent({ type: 'input' });
    await wait(1400);
    const after = els['e-comp'].textContent;
    report.notes.push('实时联动：none -> fs 后 e-comp「' + before + '」->「' + after + '」');
    if (before === after) report.errors.push('参数改动未触发实时重算（预览不会跟着变）');
    // 预设按钮
    fire('btn-preset-photo');
    await wait(900);
    if (String(els['p-dither'].value) !== 'fs' || String(els['p-fit'].value) !== 'fill')
      report.errors.push('照片预设未生效：dither=' + els['p-dither'].value + ' fit=' + els['p-fit'].value);
    fire('btn-preset-text');
    await wait(900);
    if (String(els['p-dither'].value) !== 'none' || String(els['p-sharp'].value) !== '1.6')
      report.errors.push('文字预设未生效：dither=' + els['p-dither'].value + ' sharp=' + els['p-sharp'].value);
    // 改回 none 以便后续分块断言稳定
    els['p-dither'].value = 'none';
    els['p-dither'].dispatchEvent({ type: 'input' });
    await wait(1000);
    // 复制按钮不应抛错
    fire('btn-copyframes'); fire('btn-copyhash');
    await wait(150);
    tabs[2]._onclick(); tabs[1]._onclick(); tabs[0]._onclick();
    fire('btn-selftest'); fire('btn-stop'); fire('btn-rawsend'); fire('btn-clear');
    await wait(300);
    report.notes.push('按钮与视图无异常');
  } catch (e) { report.errors.push('冒烟主体: ' + e.message); }
  fs.writeFileSync(outPath, JSON.stringify(report));
})();
"""

def main():
    txt = open(HTML, "r", encoding="utf-8").read()
    scripts = extract_scripts(txt)
    print("index.html %d 行，内联 script %d 个，外部模块 %s" %
          (txt.count(NL), len(scripts), os.path.basename(CORE)))
    fails = []
    tmp = tempfile.mkdtemp(prefix="ysbpage_", dir=ROOT + r"/_verify")
    for i, body in enumerate(scripts, 1):
        p = os.path.join(tmp, "s%d.js" % i)
        open(p, "w", encoding="utf-8").write(body)
        r = subprocess.run(["node", "--check", p], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            fails.append("script #%d 语法错误:%s%s" % (i, NL, (r.stderr or "")[:600]))
        else:
            print("  script #%d ....... 语法 OK（%d 行）" % (i, body.count(NL)))
    probe = "const Y=require(%r);const s=Y.selftest();console.log(JSON.stringify({ok:s.ok,n:s.results.length}));" % CORE
    r = subprocess.run(["node", "-e", probe], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        fails.append("ysbadge-core.js 加载失败:" + NL + (r.stderr or "")[:400])
    else:
        d = json.loads(r.stdout.strip().splitlines()[-1])
        if d.get("ok"):
            print("  ysbadge-core.js .. 可加载，selftest %d 项全过" % d.get("n"))
        else:
            fails.append("ysbadge-core.js selftest 未全过")
    glue = NL.join(scripts)
    defined = set(ID_DEF_RE.findall(txt))
    used = set(ID_USE_RE.findall(glue)) | set(IND1_RE.findall(glue)) | set(IND2_RE.findall(glue))
    missing = sorted(used - defined)
    if missing:
        fails.append("胶水引用但不存在的 id: " + ", ".join(missing))
    else:
        print("  id 交叉核对 ...... %d 个引用全部有对应元素" % len(used))
    unused = sorted(defined - used)
    if unused:
        print("  （提示）定义未引用的 id: " + ", ".join(unused))
    run_p = os.path.join(tmp, "smoke.js")
    out_p = os.path.join(tmp, "smoke.json")
    open(run_p, "w", encoding="utf-8").write(SMOKE)
    r = subprocess.run(["node", run_p, HTML, out_p, CORE], capture_output=True, text=True, encoding="utf-8", timeout=180)
    if r.returncode != 0 or not os.path.exists(out_p):
        fails.append("冒烟测试进程失败 rc=%s%s%s" % (r.returncode, NL, (r.stderr or r.stdout or "")[:800]))
    else:
        rep = json.load(open(out_p, encoding="utf-8"))
        for n in rep.get("notes", []):
            print("  [smoke] " + n)
        for e in rep.get("errors", []):
            fails.append("冒烟: " + e)
        if not rep.get("errors"):
            print("  DOM+BLE 冒烟 ..... 编码管线 + fake GATT 连接/发送 + 视图 + 按钮全部无异常")
    print("")
    if fails:
        print("==== 失败 %d 项 ====" % len(fails))
        for f in fails:
            print("  FAIL " + f)
        print("临时目录保留供排查：%s" % tmp)
        return 1
    print("==== web/ 校验全部通过（语法 + 模块 + 引用 + 编码冒烟 + BLE 冒烟）====")
    try:
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)
    except OSError:
        print("临时目录清理失败（可手动删）：%s" % tmp)
    return 0

raise SystemExit(main())
