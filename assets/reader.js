/* 黃泉燒肉店｜小說文庫：目錄、閱讀設定、閱讀進度（只存在讀者自己的瀏覽器） */
(function(){
  var root = document.documentElement;
  function get(k){ try{ return localStorage.getItem(k); }catch(e){ return null; } }
  function set(k,v){ try{ localStorage.setItem(k,v); }catch(e){} }

  /* ---------- 面板 ---------- */
  var toc = document.getElementById("toc"), setP = document.getElementById("setPanel");
  var bToc = document.getElementById("btnToc"), bSet = document.getElementById("btnSet"), scrim = null;
  function close(){
    toc.hidden = true; setP.hidden = true; bToc.setAttribute("aria-expanded","false"); bSet.setAttribute("aria-expanded","false");
    if(scrim){ scrim.remove(); scrim = null; }
  }
  bToc.addEventListener("click", function(){
    var open = toc.hidden; close();
    if(open){
      toc.hidden = false; bToc.setAttribute("aria-expanded","true");
      scrim = document.createElement("div"); scrim.className = "scrim"; scrim.onclick = close; document.body.appendChild(scrim);
      var here = toc.querySelector(".here"); if(here) here.scrollIntoView({block:"center"});
    }
  });
  bSet.addEventListener("click", function(){ var open = setP.hidden; close(); if(open){ setP.hidden = false; bSet.setAttribute("aria-expanded","true"); } });
  document.addEventListener("keydown", function(e){ if(e.key==="Escape") close(); });

  /* ---------- 字級與背景 ---------- */
  var fs = parseInt(get("hq.fs")) || 18, fsNow = document.getElementById("fsNow");
  function applyFs(){ root.style.setProperty("--fs", fs+"px"); fsNow.textContent = fs+"px"; set("hq.fs", fs); }
  function applyTheme(t){
    if(t) root.dataset.theme = t; else delete root.dataset.theme;
    set("hq.theme", t||"");
    setP.querySelectorAll("[data-theme]").forEach(function(b){ b.setAttribute("aria-pressed", String(b.dataset.theme===(t||""))); });
  }
  setP.addEventListener("click", function(e){
    var b = e.target.closest("button"); if(!b) return;
    if(b.dataset.fs){ fs = Math.max(14, Math.min(26, fs + (+b.dataset.fs))); applyFs(); }
    if(b.dataset.theme!=null) applyTheme(b.dataset.theme);
  });
  applyFs(); applyTheme(get("hq.theme")||"");

  /* ---------- 閱讀進度 ---------- */
  var main = document.querySelector("main[data-ch]"), bar = document.getElementById("progress");
  var read = {}; try{ read = JSON.parse(get("hq.read")||"{}")||{}; }catch(e){}
  if(main){
    var ch = main.dataset.ch;
    var here = toc.querySelector('a[data-ch="'+ch+'"]'); if(here) here.classList.add("here");
    var saved = parseFloat(get("hq.pos."+ch));
    if(saved > 0.02 && saved < 0.98 && !location.hash){
      requestAnimationFrame(function(){ window.scrollTo(0, saved * (document.documentElement.scrollHeight - innerHeight)); });
    }
    var t = 0;
    window.addEventListener("scroll", function(){
      var h = document.documentElement.scrollHeight - innerHeight, p = h > 0 ? scrollY / h : 1;
      bar.style.width = (p*100)+"%";
      clearTimeout(t);
      t = setTimeout(function(){
        set("hq.pos."+ch, p.toFixed(4)); set("hq.last", ch);
        if(p > 0.92 && !read[ch]){ read[ch] = 1; set("hq.read", JSON.stringify(read)); }
      }, 250);
    }, {passive:true});
  }

  /* ---------- 首頁：繼續閱讀 ---------- */
  var resume = document.getElementById("resume"), last = get("hq.last");
  if(resume && last){
    var a = document.querySelector('.chap[data-ch="'+last+'"]');
    if(a){
      resume.hidden = false; resume.href = a.getAttribute("href");
      resume.textContent = "繼續閱讀：第" + ("0"+last).slice(-2) + "章";
      a.classList.add("read-last");
    }
  }
  document.querySelectorAll(".chap[data-ch]").forEach(function(a){ if(read[a.dataset.ch]) a.classList.add("read-done"); });
})();

/* 圖庫燈箱 */
(function(){
  var G = window.GALLERY, lb = document.getElementById("lb");
  if(!G || !lb) return;
  var i = 0, img = document.getElementById("lbImg");
  function show(k){
    i = (k + G.length) % G.length; var it = G[i];
    img.src = it.src; img.alt = it.cap;
    document.getElementById("lbCap").textContent = it.cap;
    document.getElementById("lbSub").textContent = it.sub + "（" + (i+1) + " / " + G.length + "）";
    document.getElementById("lbLink").href = it.link;
    var nx = new Image(); nx.src = G[(i+1) % G.length].src;   // 先載下一張
  }
  function open(k){ show(k); lb.hidden = false; document.body.style.overflow = "hidden"; }
  function close(){ lb.hidden = true; document.body.style.overflow = ""; }
  document.addEventListener("click", function(e){
    var b = e.target.closest(".g-item"); if(b){ open(+b.dataset.i); return; }
    var c = e.target.closest("[data-lb]");
    if(c){ var a = c.dataset.lb; if(a==="close") close(); else show(i + (a==="next"?1:-1)); return; }
    if(!lb.hidden && e.target === lb) close();
  });
  document.addEventListener("keydown", function(e){
    if(lb.hidden) return;
    if(e.key==="Escape") close(); else if(e.key==="ArrowRight") show(i+1); else if(e.key==="ArrowLeft") show(i-1);
  });
  var x0 = null;
  lb.addEventListener("touchstart", function(e){ x0 = e.touches[0].clientX; }, {passive:true});
  lb.addEventListener("touchend", function(e){
    if(x0 == null) return; var dx = e.changedTouches[0].clientX - x0; x0 = null;
    if(Math.abs(dx) > 50) show(i + (dx < 0 ? 1 : -1));
  });
})();
