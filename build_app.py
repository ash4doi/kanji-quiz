#!/usr/bin/env python3
"""questions_g1.json を読み込み、データを埋め込んだ単一の index.html を生成する。
ビルドツール不要。データを更新したら `python3 build_app.py` を再実行するだけ。
file:// で直接開いても動くよう、問題データは HTML 内に埋め込む。"""
import json, csv, pathlib

HERE = pathlib.Path(__file__).parent
# 学年ごとの問題ファイル（CSV）。学年を増やすときはここに1行足すだけ。
# CSVの列: id,kanji,type,yomi,word,highlight,ex1,ex1_yomi,ex2,ex2_yomi
GRADE_FILES = {"1": "kanji_g1.csv", "2": "kanji_g2.csv"}

def load_grade_csv(path):
    questions = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):  # ヘッダが1行目なので2始まり
            if not (r.get("id") or "").strip():
                continue  # 空行はスキップ
            missing = [c for c in ("id","kanji","type","yomi","word","highlight",
                                   "ex1","ex1_yomi","ex2","ex2_yomi") if not (r.get(c) or "").strip()]
            if missing:
                raise ValueError(f"{path} の {i}行目: 列が空です -> {missing}")
            questions.append({
                "id": r["id"].strip(), "kanji": r["kanji"].strip(), "type": r["type"].strip(),
                "yomi": r["yomi"].strip(), "word": r["word"].strip(), "highlight": r["highlight"].strip(),
                "examples": [
                    {"text": r["ex1"].strip(), "yomi": r["ex1_yomi"].strip()},
                    {"text": r["ex2"].strip(), "yomi": r["ex2_yomi"].strip()},
                ],
            })
    return {"questions": questions}

grades = {g: load_grade_csv(HERE / fn) for g, fn in GRADE_FILES.items()}
data_js = json.dumps(grades, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>かんじ よみクイズ（1ねん）</title>
<style>
  :root {
    --bg: #fff8ec; --card: #ffffff; --ink: #3a3226; --sub: #8a7f6c;
    --accent: #ff8a3d; --accent-d: #e8731f; --good: #34b36a; --bad: #e7544a;
    --hl: #ff5d8f; --line: #f0e7d6; --shadow: 0 6px 18px rgba(120,90,40,.12);
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  html, body { margin: 0; padding: 0; }
  body {
    font-family: "Hiragino Maru Gothic ProN", "Hiragino Sans", "Yu Gothic", "Meiryo", system-ui, sans-serif;
    background: var(--bg); color: var(--ink);
    display: flex; justify-content: center; min-height: 100vh;
  }
  .app { width: 100%; max-width: 480px; padding: 16px 16px 40px; }
  .hidden { display: none !important; }

  h1 { font-size: 1.5rem; text-align: center; margin: 18px 0 6px; }
  .lead { text-align: center; color: var(--sub); margin: 0 0 22px; font-size: .95rem; }

  .card {
    background: var(--card); border-radius: 20px; box-shadow: var(--shadow);
    padding: 22px 18px; margin-bottom: 16px;
  }
  .label { font-size: .85rem; color: var(--sub); margin: 0 0 10px; font-weight: 700; }
  .opts { display: flex; gap: 10px; flex-wrap: wrap; }
  .opt {
    flex: 1 1 28%; border: 2px solid var(--line); background: #fff; color: var(--ink);
    border-radius: 14px; padding: 12px 6px; font-size: 1rem; font-weight: 700;
    cursor: pointer; transition: .12s;
  }
  .opt.on { border-color: var(--accent); background: #fff1e3; color: var(--accent-d); }

  .btn {
    width: 100%; border: none; border-radius: 16px; padding: 16px;
    font-size: 1.15rem; font-weight: 800; cursor: pointer; color: #fff;
    background: var(--accent); box-shadow: 0 4px 0 var(--accent-d); transition: .08s;
  }
  .btn:active { transform: translateY(3px); box-shadow: 0 1px 0 var(--accent-d); }
  .btn.ghost { background: #fff; color: var(--accent-d); border: 2px solid var(--accent);
    box-shadow: none; }

  /* progress */
  .topbar { display: flex; align-items: center; gap: 10px; margin: 6px 0 18px; }
  .bar { flex: 1; height: 12px; background: var(--line); border-radius: 99px; overflow: hidden; }
  .bar > i { display: block; height: 100%; background: var(--accent); width: 0; transition: width .25s; }
  .count { font-size: .85rem; color: var(--sub); font-weight: 700; min-width: 48px; text-align: right; }

  /* question */
  .word { text-align: center; font-size: 3.2rem; font-weight: 800; letter-spacing: .04em;
    margin: 6px 0 4px; line-height: 1.2; }
  .word .hl { color: var(--hl); }
  .ask { text-align: center; color: var(--sub); margin: 0 0 18px; font-size: .95rem; }
  .ask b { color: var(--hl); }
  .examples { border-top: 1px dashed var(--line); padding-top: 14px; margin-top: 6px; }
  .examples .ex { font-size: 1.25rem; text-align: center; margin: 8px 0; line-height: 1.7; }
  ruby rt { color: var(--accent-d); font-size: .55em; font-weight: 700; }

  .answer { margin-top: 16px; }
  input.field {
    width: 100%; border: 2px solid var(--line); border-radius: 14px; padding: 14px;
    font-size: 1.5rem; text-align: center; font-family: inherit; outline: none;
  }
  input.field:focus { border-color: var(--accent); }

  /* feedback */
  .fb { text-align: center; margin: 14px 0 4px; }
  .mark { font-size: 3rem; font-weight: 800; line-height: 1; }
  .mark.good { color: var(--good); } .mark.bad { color: var(--bad); }
  .fb .yomi { font-size: 1.3rem; margin-top: 6px; }
  .fb .yomi b { color: var(--hl); font-size: 1.5rem; }

  /* result */
  .score { text-align: center; font-size: 2.6rem; font-weight: 800; margin: 6px 0; }
  .score small { display: block; font-size: .9rem; color: var(--sub); font-weight: 700; }
  .missed { margin-top: 8px; }
  .missed .chip {
    display: inline-flex; flex-direction: column; align-items: center;
    background: #fff1e3; border: 2px solid #ffd9b8; border-radius: 12px;
    padding: 6px 10px; margin: 4px; min-width: 54px;
  }
  .chip .k { font-size: 1.6rem; font-weight: 800; }
  .chip .y { font-size: .8rem; color: var(--accent-d); }
  .praise { text-align: center; font-size: 1.2rem; margin: 10px 0 18px; font-weight: 800; }
  .stack > * + * { margin-top: 10px; }

  /* streak / history */
  .streak { display: flex; justify-content: center; gap: 22px; margin: 0 0 16px; }
  .streak .s { text-align: center; }
  .streak .n { font-size: 1.7rem; font-weight: 800; color: var(--accent-d); line-height: 1; }
  .streak .t { font-size: .72rem; color: var(--sub); font-weight: 700; margin-top: 4px; }
  .tools { display: flex; gap: 10px; margin-top: 14px; }
  .tools button {
    flex: 1; font-size: .82rem; padding: 11px 6px; border-radius: 12px;
    border: 2px solid var(--line); background: #fff; color: var(--sub);
    font-weight: 700; cursor: pointer; font-family: inherit;
  }
  .tools button:active { background: #f6efe2; }
  .note { font-size: .72rem; color: var(--sub); text-align: center; margin: 8px 0 0; }
</style>
</head>
<body>
<div class="app">

  <!-- START -->
  <section id="start">
    <h1>かんじ よみクイズ 🌸</h1>
    <p class="lead" id="lead">1ねんせいの かんじ・よみのれんしゅう</p>
    <div class="streak" id="streakBox"></div>
    <div class="card">
      <p class="label">がくねん</p>
      <div class="opts" id="gradeOpts">
        <button class="opt on" data-grade="1">1ねん</button>
        <button class="opt" data-grade="2">2ねん</button>
      </div>
      <p class="label" style="margin-top:18px">もんだいの かず</p>
      <div class="opts" id="sizeOpts">
        <button class="opt on" data-size="10">10もん</button>
        <button class="opt" data-size="20">20もん</button>
        <button class="opt" data-size="all">ぜんぶ</button>
      </div>
      <p class="label" style="margin-top:18px">じゅんばん</p>
      <div class="opts" id="orderOpts">
        <button class="opt on" data-order="random">バラバラ</button>
        <button class="opt" data-order="seq">じゅんばん</button>
        <button class="opt" data-order="weak">にがて</button>
      </div>
    </div>
    <button class="btn" id="startBtn">スタート</button>
    <div class="tools">
      <button id="exportBtn">きろくを 書き出す</button>
      <button id="importBtn">きろくを よみこむ</button>
    </div>
    <input type="file" id="importFile" accept="application/json,.json" class="hidden">
    <p class="note">きろくは この きかいの ブラウザに ほぞんされます</p>
  </section>

  <!-- QUIZ -->
  <section id="quiz" class="hidden">
    <div class="topbar">
      <div class="bar"><i id="barFill"></i></div>
      <div class="count" id="count">1 / 10</div>
    </div>
    <div class="card">
      <div class="word" id="word"></div>
      <p class="ask">あかい <b>かんじ</b> の よみは？</p>
      <div class="examples" id="examples"></div>

      <div class="answer" id="answerArea">
        <input class="field" id="field" type="text" inputmode="kana"
               autocomplete="off" autocapitalize="off" placeholder="ひらがなで">
      </div>
      <div class="fb hidden" id="fb"></div>
    </div>
    <button class="btn" id="submitBtn">こたえる</button>
    <button class="btn hidden" id="nextBtn">つぎへ →</button>
  </section>

  <!-- RESULT -->
  <section id="result" class="hidden">
    <h1>けっか はっぴょう 🎉</h1>
    <div class="card">
      <div class="score" id="score"></div>
      <div class="praise" id="praise"></div>
      <div class="streak" id="streakBoxR"></div>
      <div id="missedWrap" class="hidden">
        <p class="label">まちがえた かんじ</p>
        <div class="missed" id="missed"></div>
      </div>
    </div>
    <div class="stack">
      <button class="btn hidden" id="retryWrong">まちがいだけ もういちど</button>
      <button class="btn ghost" id="restart">さいしょから</button>
    </div>
  </section>

</div>

<script>
const GRADES = __DATA__;          // { "1": {questions:[...]}, "2": {questions:[...]} }
let grade = "1";                  // 選択中の学年
let ALL = GRADES[grade].questions;

// ---- state ----
let cfg = { size: 10, order: "random" };
let session = [];   // 出題中の問題配列
let idx = 0, score = 0, wrong = [];

// ---- persistent store (localStorage) ----
// 記録は学年ごとに別々のキーで保存する。
function blankStore(){ return { stats:{}, sessions:[], lastStudyDate:null, streak:0, bestStreak:0, totalAnswered:0, totalCorrect:0 }; }
function skeyFor(g){ return "kanji_v2_g" + g; }
function loadStoreFor(g){
  let raw = null;
  try { raw = JSON.parse(localStorage.getItem(skeyFor(g))); } catch(e){}
  // 旧バージョン（学年共通キー）の1年生記録があれば引き継ぐ
  if(!raw && g === "1"){ try { raw = JSON.parse(localStorage.getItem("kanji_g1_v1")); } catch(e){} }
  return Object.assign(blankStore(), raw || {});
}
function saveStore(){ try { localStorage.setItem(skeyFor(grade), JSON.stringify(store)); } catch(e){} }
let store = loadStoreFor(grade);

function today(){ const d=new Date(), z=n=>String(n).padStart(2,'0'); return d.getFullYear()+'-'+z(d.getMonth()+1)+'-'+z(d.getDate()); }
function daysBetween(a,b){ return Math.round((new Date(b+'T00:00') - new Date(a+'T00:00'))/86400000); }

function recordAnswer(q, ok){
  const s = store.stats[q.id] || { seen:0, correct:0, lastDate:null, streak:0 };
  s.seen++; if(ok){ s.correct++; s.streak++; } else { s.streak=0; }
  s.lastDate = today();
  store.stats[q.id] = s;
  store.totalAnswered++; if(ok) store.totalCorrect++;
  saveStore();
}
function recordSession(sc, total){
  const t = today();
  if(store.lastStudyDate === null) store.streak = 1;
  else if(store.lastStudyDate === t){ /* 同じ日は連続日数を維持 */ }
  else { store.streak = (daysBetween(store.lastStudyDate, t) === 1) ? store.streak + 1 : 1; }
  store.lastStudyDate = t;
  store.bestStreak = Math.max(store.bestStreak || 0, store.streak);
  store.sessions.push({ date:t, total, score:sc });
  if(store.sessions.length > 300) store.sessions = store.sessions.slice(-300);
  saveStore();
}
function renderStreak(id){
  const el = $(id); if(!el) return;
  const acc = store.totalAnswered ? Math.round(store.totalCorrect / store.totalAnswered * 100) : 0;
  el.innerHTML =
    '<div class="s"><div class="n">'+(store.streak||0)+'</div><div class="t">れんぞく日</div></div>'+
    '<div class="s"><div class="n">'+store.sessions.length+'</div><div class="t">かいすう</div></div>'+
    '<div class="s"><div class="n">'+acc+'%</div><div class="t">せいかい率</div></div>';
}
function exportData(){
  const blob = new Blob([JSON.stringify(store, null, 2)], { type:"application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "kanji_kiroku_" + today() + ".json";
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(url), 1500);
}
function importData(file){
  const r = new FileReader();
  r.onload = () => {
    try {
      const obj = JSON.parse(r.result);
      if(!obj || typeof obj !== "object" || !("stats" in obj)) throw 0;
      store = Object.assign(blankStore(), obj);
      saveStore(); renderStreak("streakBox");
      alert("きろくを よみこみました。");
    } catch(e){ alert("ファイルを よみこめませんでした。"); }
  };
  r.readAsText(file);
}

// ---- helpers ----
const $ = (id) => document.getElementById(id);
const show = (id) => $(id).classList.remove("hidden");
const hide = (id) => $(id).classList.add("hidden");
function shuffle(a){ a=a.slice(); for(let i=a.length-1;i>0;i--){const j=Math.random()*(i+1)|0;[a[i],a[j]]=[a[j],a[i]];} return a; }

// 対象漢字を1か所だけ <span class=hl> で強調
function highlightWord(word, k){
  const i = word.indexOf(k);
  if(i<0) return word;
  return word.slice(0,i) + '<span class="hl">'+k+'</span>' + word.slice(i+k.length);
}
// 例文の対象漢字に1か所だけ ruby を付ける
function rubyText(text, k, yomi){
  const i = text.indexOf(k);
  if(i<0) return text;
  return text.slice(0,i) + '<ruby>'+k+'<rt>'+yomi+'</rt></ruby>' + text.slice(i+k.length);
}
// 入力の正規化（前後空白除去）。判定はひらがな完全一致。
const norm = (s) => (s||"").trim();

// ---- option buttons ----
function bindOpts(wrap, key){
  $(wrap).querySelectorAll(".opt").forEach(b=>{
    b.addEventListener("click", ()=>{
      $(wrap).querySelectorAll(".opt").forEach(x=>x.classList.remove("on"));
      b.classList.add("on");
      cfg[key] = b.dataset.size || b.dataset.order;
    });
  });
}
bindOpts("sizeOpts","size");
bindOpts("orderOpts","order");

// 学年切り替え（ALLと記録ストアを学年ごとに切り替える）
$("gradeOpts").querySelectorAll(".opt").forEach(b=>{
  b.addEventListener("click", ()=>{
    $("gradeOpts").querySelectorAll(".opt").forEach(x=>x.classList.remove("on"));
    b.classList.add("on");
    grade = b.dataset.grade;
    ALL = GRADES[grade].questions;
    store = loadStoreFor(grade);
    $("lead").textContent = grade + "ねんせいの かんじ・よみのれんしゅう";
    renderStreak("streakBox");
  });
});

// ---- flow ----
// にがて優先スコア（高いほど先に出す）：未出題 > 正解率が低い・しばらく解いていない > よくできている
function weakScore(q){
  const s = store.stats[q.id];
  if(!s || s.seen === 0) return 1000 + Math.random()*10;        // 未出題は最優先（同点はランダム）
  const acc  = s.correct / s.seen;                              // 正解率
  const days = s.lastDate ? Math.min(daysBetween(s.lastDate, today()), 30) : 30; // 経過日数（最大30）
  return (1 - acc)*60 + days - (s.streak||0)*8 + Math.random()*5;
}

function startSession(pool){
  let qs;
  if(cfg.order === "seq")       qs = pool.slice();
  else if(cfg.order === "weak") qs = pool.slice().sort((a,b)=>weakScore(b)-weakScore(a));
  else                          qs = shuffle(pool);             // random
  if(cfg.size !== "all"){ qs = qs.slice(0, Math.min(+cfg.size, qs.length)); }
  if(cfg.order === "weak") qs = shuffle(qs);                    // 選抜後は出題順をバラす
  session = qs; idx = 0; score = 0; wrong = [];
  hide("start"); hide("result"); show("quiz");
  renderQuestion();
}

function renderQuestion(){
  const q = session[idx];
  $("barFill").style.width = (idx/session.length*100)+"%";
  $("count").textContent = (idx+1)+" / "+session.length;
  $("word").innerHTML = highlightWord(q.word, q.highlight);
  // 出題中は読みを隠した例文
  $("examples").innerHTML = q.examples.map(e=>'<div class="ex">'+e.text+'</div>').join("");
  // 入力欄リセット
  const f = $("field"); f.value=""; f.disabled=false;
  show("answerArea"); hide("fb");
  show("submitBtn"); hide("nextBtn");
  setTimeout(()=>f.focus(), 50);
}

function submit(){
  const q = session[idx];
  const ans = norm($("field").value);
  if(ans==="") { $("field").focus(); return; }
  const ok = ans === q.yomi;
  if(ok) score++; else wrong.push(q);
  recordAnswer(q, ok);

  $("field").disabled = true;
  // 例文を読み付きで再表示
  $("examples").innerHTML = q.examples.map(e=>
    '<div class="ex">'+rubyText(e.text, q.highlight, e.yomi)+'</div>').join("");
  // フィードバック
  $("fb").innerHTML =
    '<div class="mark '+(ok?'good':'bad')+'">'+(ok?'◯':'✕')+'</div>'+
    '<div class="yomi">こたえ： <b>'+q.yomi+'</b></div>';
  show("fb");
  hide("submitBtn"); show("nextBtn");
  $("barFill").style.width = ((idx+1)/session.length*100)+"%";
}

function next(){
  idx++;
  if(idx>=session.length){ showResult(); return; }
  renderQuestion();
}

function showResult(){
  hide("quiz"); show("result");
  const total = session.length;
  recordSession(score, total);
  renderStreak("streakBoxR");
  renderStreak("streakBox");
  $("score").innerHTML = score+" / "+total+'<small>せいかい</small>';
  const rate = score/total;
  $("praise").textContent =
    rate===1 ? "ぜんもん せいかい！すごい！🌟" :
    rate>=0.8 ? "よくできました！👏" :
    rate>=0.5 ? "その ちょうし！💪" : "もういちど がんばろう！🔥";
  // 間違えた漢字（重複は1つに）
  const seen = new Set(); const uniq = [];
  wrong.forEach(q=>{ const key=q.id; if(!seen.has(key)){seen.add(key); uniq.push(q);} });
  if(uniq.length){
    show("missedWrap");
    $("missed").innerHTML = uniq.map(q=>
      '<span class="chip"><span class="k">'+q.kanji+'</span><span class="y">'+q.yomi+'</span></span>').join("");
    show("retryWrong");
  } else {
    hide("missedWrap"); hide("retryWrong");
  }
}

// ---- events ----
$("startBtn").addEventListener("click", ()=>startSession(ALL));
$("submitBtn").addEventListener("click", submit);
$("nextBtn").addEventListener("click", next);
$("field").addEventListener("keydown", e=>{ if(e.key==="Enter"){ e.preventDefault(); submit(); }});
$("retryWrong").addEventListener("click", ()=>{
  const pool = [...new Map(wrong.map(q=>[q.id,q])).values()];
  cfg.size = "all"; startSession(pool);
});
$("restart").addEventListener("click", ()=>{ hide("result"); hide("quiz"); show("start"); renderStreak("streakBox"); });

// データ管理
$("exportBtn").addEventListener("click", exportData);
$("importBtn").addEventListener("click", ()=>$("importFile").click());
$("importFile").addEventListener("change", e=>{ if(e.target.files[0]) importData(e.target.files[0]); e.target.value=""; });

// 起動時
renderStreak("streakBox");
</script>
</body>
</html>
"""

out = HTML.replace("__DATA__", data_js)
(HERE / "index.html").write_text(out, encoding="utf-8")
total = sum(len(d["questions"]) for d in grades.values())
print("index.html を生成しました（学年:", list(grades), " 合計問題数:", total, "）")
