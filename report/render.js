/* report/render.js — REPORT_DATA 를 읽어 DOM 을 생성. 외부 의존성 없음.
 * real 영역은 실제 수치를, pending 영역은 skeleton/placeholder 를 그린다. */
(function () {
  var D = window.REPORT_DATA;
  var app = document.getElementById("app");

  /* --- tiny helpers --- */
  function el(tag, cls, html) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  }
  function esc(s) { return String(s).replace(/[&<>]/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]; }); }
  function fmt(v, kind) {
    if (kind === "ratio") return v.toFixed(2).replace(/\.00$/, ".00");
    return String(v);
  }
  function section(id, kicker, title, leadHtml) {
    var s = el("section"); s.id = id;
    var w = el("div", "wrap");
    w.appendChild(el("div", "kicker", kicker));
    w.appendChild(el("h2", null, title));
    if (leadHtml) w.appendChild(el("p", "lead", leadHtml));
    s.appendChild(w);
    app.appendChild(s);
    return w;
  }

  /* =============================================================
   * Section 1 — Hero
   * ===========================================================*/
  (function hero() {
    var h = el("header", "hero");
    var w = el("div", "wrap");
    w.appendChild(el("span", "scope", esc(D.meta.scopeNote)));
    w.appendChild(el("h1", null, esc(D.meta.title)));
    w.appendChild(el("p", "sub", "“" + esc(D.meta.subtitle) + "”"));
    w.appendChild(el("div", "metaline",
      esc(D.meta.dataSources) + "<br>" +
      "updated " + esc(D.meta.updated) + " · " + esc(D.meta.purpose)));
    h.appendChild(w);
    app.appendChild(h);
  })();

  /* =============================================================
   * Section 2 — Initial Discovery (climb funnel)  [REAL]
   * ===========================================================*/
  (function discovery() {
    var c = D.real.climb;
    var w = section("discovery", "01 · Initial Discovery",
      'climb cohort — 오르던 캐릭터의 260 도달과 그 이후 <span class="badge real">Real</span>',
      esc(c.screening) + " 를 추린 모멘텀 코호트 <b>n=" + c.cohortN + "</b>. 이벤트 성수기 앵커.");

    /* stat row */
    var f = c.funnel;
    var stats = el("div", "stats");
    [
      ["n=" + f[1].n, "35일 내 Lv.260 도달", f[1].pct.toFixed(1) + "% of " + c.cohortN],
      [f[2].n + " / " + f[1].n, "260 도달 후 최종 Lv.260", f[2].pct.toFixed(1) + "%"],
      [f[3].n + " / " + f[1].n, "261+ 도달", f[3].pct.toFixed(1) + "%"],
      [f[4].n + " / " + f[1].n, "270+ 도달", f[4].pct.toFixed(1) + "%"]
    ].forEach(function (r) {
      var s = el("div", "stat");
      s.appendChild(el("div", "v num", r[0]));
      s.appendChild(el("div", "k", r[1]));
      s.appendChild(el("div", "s num", r[2]));
      stats.appendChild(s);
    });
    w.appendChild(stats);

    /* funnel */
    var fun = el("div", "funnel panel");
    f.forEach(function (row) {
      var r = el("div", "frow");
      r.appendChild(el("div", "lab", esc(row.label) + (row.sub ? '<span class="sub">' + esc(row.sub) + "</span>" : "")));
      var bar = el("div", "fbar");
      var i = el("i"); i.style.width = Math.max(row.pct, 1.2) + "%";
      bar.appendChild(i);
      r.appendChild(bar);
      var v = el("div", "val num", row.n + '<span class="p">' + row.pct.toFixed(1) + "%</span>");
      r.appendChild(v);
      fun.appendChild(r);
    });
    w.appendChild(fun);

    /* robustness mini-table */
    var rb = el("div", "panel"); rb.style.marginTop = "16px";
    rb.appendChild(el("div", "mname", "robustness — 관측창을 좁혀도 유지되는가 (‘관측 기간 부족’ 반론 검정)"));
    var tbl = el("div"); tbl.style.marginTop = "10px";
    c.robustness.forEach(function (x) {
      var row = el("div", "frow");
      row.style.gridTemplateColumns = "170px 1fr 92px";
      row.appendChild(el("div", "lab", esc(x.window)));
      var bar = el("div", "fbar");
      var i = el("i"); i.style.width = x.pct + "%"; i.style.background = "linear-gradient(90deg,#8957e5,#a371f7)";
      bar.appendChild(i); row.appendChild(bar);
      row.appendChild(el("div", "val num", x.final260 + "/" + x.reach260 + '<span class="p">' + x.pct.toFixed(1) + "%</span>"));
      tbl.appendChild(row);
    });
    rb.appendChild(tbl);
    w.appendChild(rb);

    w.appendChild(el("div", "note msg", "<b>메시지.</b> " + esc(c.message)));
    w.appendChild(el("div", "note caveat", esc(c.caveat)));
  })();

  /* =============================================================
   * Section 3 — Historical EDA  [REAL, descriptive]
   * ===========================================================*/
  (function eda() {
    var sg = D.real.signature;
    var w = section("eda", "02 · Historical EDA",
      esc(sg.chartTitle) + ' <span class="badge real">Real</span>',
      "이벤트 기간에 크게 성장한 캐릭터(Parker)와 여러 시즌에 걸쳐 성장한 캐릭터(Persistent candidate)의 <b>과거 성장 형태</b> 비교.");

    var lg = el("div", "legend");
    lg.innerHTML =
      '<span><i style="background:var(--parker)"></i>Seasonal Parker (n=' + sg.groups[0].n + ")</span>" +
      '<span><i style="background:var(--persistent)"></i>Persistent candidate (n=' + sg.groups[1].n + ")</span>";
    w.appendChild(lg);

    var cmp = el("div", "cmp panel");
    Object.keys(sg.metricMeta).forEach(function (mk) {
      var meta = sg.metricMeta[mk];
      var pv = sg.groups[0].metrics[mk], sv = sg.groups[1].metrics[mk];
      var mx = Math.max(pv, sv) || 1;
      var m = el("div", "m");
      m.appendChild(el("div", "mname", esc(meta.name)));
      var bars = el("div", "bars");
      [["parker", "Parker", pv], ["persistent", "Persistent", sv]].forEach(function (b) {
        var row = el("div", "b " + b[0]);
        row.appendChild(el("div", "who", b[1]));
        var tr = el("div", "track");
        var i = el("i"); i.style.width = (b[2] / mx * 100) + "%";
        tr.appendChild(i); row.appendChild(tr);
        row.appendChild(el("div", "bv num", fmt(b[2], meta.fmt)));
        bars.appendChild(row);
      });
      m.appendChild(bars);
      cmp.appendChild(m);
    });
    w.appendChild(cmp);

    w.appendChild(el("div", "note msg", "<b>핵심.</b> " + esc(sg.keyMessage)));
    w.appendChild(el("div", "note", "<b>주의 — descriptive signature.</b> " + esc(sg.circularityNote)));

    /* H1 verdict */
    var h1 = D.real.hypotheses[0];
    var hv = el("div", "panel"); hv.style.marginTop = "16px";
    hv.innerHTML = '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">' +
      '<span class="num" style="font-weight:800;color:var(--muted-2)">' + h1.id + '</span>' +
      '<span style="font-size:13px">' + esc(h1.text) + '</span>' +
      '<span class="badge notsup">Not Supported</span></div>' +
      '<div style="font-size:12px;color:var(--muted);margin-top:8px">' + esc(h1.basis) + '</div>';
    w.appendChild(hv);
  })();

  /* =============================================================
   * Section 4 — Analysis Question Evolution  [REAL / process]
   * ===========================================================*/
  (function evolution() {
    var w = section("evolution", "03 · 분석 질문의 발전",
      "질문이 어떻게 바뀌었는가",
      "초기 가설이 데이터와 맞지 않을 때 질문을 다시 세운 과정. 포트폴리오에서 사고방식을 보여주는 부분.");
    var evo = el("div", "evo");
    D.real.questionEvolution.forEach(function (e) {
      var row = el("div", "e");
      row.appendChild(el("div", "dot", String(e.step)));
      var body = el("div");
      body.appendChild(el("div", "q", esc(e.q)));
      body.appendChild(el("div", "n", esc(e.note)));
      row.appendChild(body);
      evo.appendChild(row);
    });
    w.appendChild(evo);
  })();

  /* =============================================================
   * Section 5 — 2-Layer Framework  [REAL / conceptual]
   * ===========================================================*/
  (function framework() {
    var fw = D.real.framework;
    var w = section("framework", "04 · Analytical Framework",
      "2-Layer — Character ≠ Account",
      "OCID 기반 분석은 캐릭터 단위다. 캐릭터가 멈춰도 계정은 활성일 수 있으므로 outcome 을 두 층으로 분리한다.");

    var g = el("div", "fw");
    [["l1", fw.layer1], ["l2", fw.layer2]].forEach(function (p) {
      var col = el("div", "col " + p[0]);
      col.appendChild(el("h3", null, esc(p[1].name)));
      col.appendChild(el("div", "cd", esc(p[1].desc)));
      var ax = el("div", "ax");
      p[1].axes.forEach(function (a) {
        var box = el("div", "a");
        box.appendChild(el("div", "an", esc(a.key)));
        box.appendChild(el("div", "am", esc(a.meaning)));
        ax.appendChild(box);
      });
      col.appendChild(ax);
      if (p[1].warnings) {
        var wn = el("div", "warns");
        p[1].warnings.forEach(function (x) { wn.appendChild(el("div", "w", esc(x))); });
        col.appendChild(wn);
      }
      g.appendChild(col);
    });
    w.appendChild(g);
    w.appendChild(el("p", "neq", "Character inactivity <b>≠</b> Account churn"));
    w.appendChild(el("div", "note", "Union 은 account-level progression 의 <b>proxy</b> 이며 account retention·login 의 직접 측정치가 아니다. 동일 계정의 다른 캐릭터 progression 은 공개 API 로 연결할 수 없다."));
  })();

  /* =============================================================
   * Section 6 — Phase B Prospective Validation  [PENDING]
   * ===========================================================*/
  (function phaseb() {
    var pb = D.pending.phaseB;
    var w = section("phaseb", "05 · Prospective Validation",
      'Phase B — 이벤트 종료 후 추적 <span class="badge pending">Pending</span>',
      "미래 데이터다. 결과 영역은 수집 전까지 placeholder 로 둔다. Pilot <b>n=" + pb.pilotN + "</b> (" + esc(pb.pilotBreakdown) + ") · 추적 축 " + pb.trackedAxes.join(" / ") + ".");

    /* timeline */
    var tl = el("div", "tl");
    pb.timeline.forEach(function (t) {
      var node = el("div", "t");
      node.appendChild(el("div", "dot"));
      node.appendChild(el("div", "lab", esc(t.label)));
      node.appendChild(el("div", "dt", esc(t.date)));
      tl.appendChild(node);
    });
    w.appendChild(tl);

    /* status banner */
    w.appendChild(el("div", "note", '<b>' + esc(pb.status) + '.</b> 아래 카드는 +28 / +56 데이터 확보 시 실제 결과로 교체된다 (data.js 의 pending.phaseB 를 채우면 자동 반영).'));

    /* outcome cards — skeleton */
    var pc = el("div", "pcards"); pc.style.marginTop = "16px";
    pb.outcomeCards.forEach(function (c) {
      var card = el("div", "pcard");
      card.appendChild(el("div", "pa", esc(c.axis)));
      card.appendChild(el("div", "pq", esc(c.question)));
      var sk = el("div"); sk.appendChild(el("div", "skeleton")); sk.appendChild(el("div", "skeleton s2"));
      card.appendChild(sk);
      card.appendChild(el("div", "ps", "pending"));
      pc.appendChild(card);
    });
    w.appendChild(pc);

    /* waves */
    var wv = el("div", "waves");
    pb.waves.forEach(function (x) {
      var box = el("div", "wave");
      box.appendChild(el("div", "wn", esc(x.name) + " · " + esc(x.when)));
      box.appendChild(el("div", "ww", esc(x.scope) + " · 예상 " + esc(x.calls) + " calls · 상태: 미실행"));
      wv.appendChild(box);
    });
    w.appendChild(wv);

    /* provisional state cards */
    var lab = el("div", "lead"); lab.style.margin = "26px 0 8px";
    lab.innerHTML = "Phase B outcome 전까지 <b>provisional state</b> — 정답 라벨로 쓰지 않음";
    w.appendChild(lab);
    var st = el("div", "states");
    pb.stateCards.forEach(function (c) {
      var box = el("div", "state");
      box.appendChild(el("span", null, esc(c.name)));
      box.appendChild(el("span", "badge pending", "pending"));
      st.appendChild(box);
    });
    w.appendChild(st);
  })();

  /* =============================================================
   * Section 7 — PM Decision  [Hypothesis / Proposed]
   * ===========================================================*/
  (function pm() {
    var p = D.pm;
    var w = section("pm", "06 · PM Decision",
      'Seasonal → Sustainable 전환 <span class="badge pending">PM Hypothesis</span>',
      "최종적으로 검증하려는 business question:");

    var bq = el("div", "panel");
    bq.style.fontSize = "15px"; bq.style.lineHeight = "1.6";
    bq.innerHTML = "“" + esc(p.businessQuestion) + "”";
    w.appendChild(bq);

    var flow = el("div", "flow"); flow.style.marginTop = "22px";
    p.conversionFlow.forEach(function (f, i) {
      if (i) flow.appendChild(el("div", "arrow", "→"));
      var box = el("div", "f");
      box.appendChild(el("div", "fl", esc(f.label)));
      box.appendChild(el("div", "fn", esc(f.note)));
      flow.appendChild(box);
    });
    w.appendChild(flow);

    var acts = el("div", "acts");
    p.proposedActions.forEach(function (a) {
      var box = el("div", "act");
      box.appendChild(el("div", "at", esc(a.name)));
      box.appendChild(el("div", "ai", esc(a.idea)));
      box.appendChild(el("span", "badge pending", esc(a.status)));
      acts.appendChild(box);
    });
    w.appendChild(acts);

    w.appendChild(el("div", "note caveat", esc(p.disclaimer)));
  })();

  /* --- footer fill --- */
  document.getElementById("foot-repo").textContent = D.meta.repo;
  document.getElementById("foot-scope").textContent = D.meta.scopeNote;
})();
