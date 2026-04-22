
    (function() {
      var curGran = 'day';
      var curView = 'spu';

      var regionTree = [
        { name: '欧洲', children: [
          { label: '德国', code: 'DE' },
          { label: '西班牙', code: 'ES' },
          { label: '法国', code: 'FR' },
          { label: '意大利', code: 'IT' }
        ]},
        { name: '北美洲', children: [
          { label: '美国', code: 'US' }
        ]},
        { name: '其它', children: [
          { label: 'Global', code: 'Global' }
        ]}
      ];

      var codeToStores = {
        'DE': ['美国 TK・艾斯特尼 - 欧洲直邮店 DE'],
        'ES': ['美国 TK・艾斯特尼 - 欧洲直邮店 ES'],
        'FR': ['美国 TK・艾斯特尼 - 欧洲直邮店 FR'],
        'IT': ['美国 TK・艾斯特尼 - 欧洲直邮店 IT'],
        'US': ['美国 TK・艾斯特尼 - 美区特 1 店 US', '美国 TK・艾斯特尼 - 美区特 2 店 US', '美国 TK・艾斯特尼 - 美区特 3 店 US'],
        'Global': ['美国TK独立站-shopify:Global']
      };

      var allStores = [];
      Object.keys(codeToStores).forEach(function(k) { allStores = allStores.concat(codeToStores[k]); });

      var cascadeSelection = { region: '', country: '', stores: [] };

      function initCascade() {
        var trigger = document.getElementById('cascadeTrigger');
        var panel = document.getElementById('cascadePanel');
        var left = document.getElementById('cascadeLeft');
        var right = document.getElementById('cascadeRight');
        var activeIdx = -1;
        function renderLeft() {
          left.innerHTML = regionTree.map(function(r, i) {
            return '<div class="cl-item" data-idx="' + i + '"><span>' + r.name + '</span><button type="button" class="only-btn" data-idx="' + i + '">仅选此项</button><span class="arrow">›</span></div>';
          }).join('');
        }
        function renderRight(idx) {
          if (idx < 0 || idx >= regionTree.length) { right.innerHTML = ''; return; }
          right.innerHTML = regionTree[idx].children.map(function(c) {
            return '<div class="cr-item" data-code="' + c.code + '">' + c.label + '</div>';
          }).join('');
        }
        function openPanel() { panel.classList.add('open'); trigger.classList.add('open'); }
        function closePanel() { panel.classList.remove('open'); trigger.classList.remove('open'); activeIdx = -1; }
        function setSelection(region, country, st, label) {
          cascadeSelection = { region: region, country: country, stores: st };
          if (label) {
            trigger.innerHTML = '<span class="tag">' + label + '<span class="tag-close" id="cascadeClear">&times;</span></span>';
            document.getElementById('cascadeClear').addEventListener('click', function(e) { e.stopPropagation(); clearCascade(); });
          } else {
            trigger.innerHTML = '<span class="placeholder">请选择</span>';
          }
          syncStoreOptions();
          closePanel();
        }
        function clearCascade() { setSelection('', '', [], ''); }
        renderLeft();
        left.addEventListener('mouseover', function(e) {
          var item = e.target.closest('.cl-item'); if (!item) return;
          var idx = parseInt(item.getAttribute('data-idx'), 10);
          if (idx === activeIdx) return; activeIdx = idx;
          left.querySelectorAll('.cl-item').forEach(function(el, i) { el.classList.toggle('active', i === idx); });
          renderRight(idx);
        });
        left.addEventListener('click', function(e) {
          var btn = e.target.closest('.only-btn'); if (!btn) return; e.stopPropagation();
          var idx = parseInt(btn.getAttribute('data-idx'), 10);
          var r = regionTree[idx]; var st = [];
          r.children.forEach(function(c) { st = st.concat(codeToStores[c.code] || []); });
          setSelection(r.name, '', st, r.name);
        });
        right.addEventListener('click', function(e) {
          var item = e.target.closest('.cr-item'); if (!item) return;
          var code = item.getAttribute('data-code');
          var regionName = activeIdx >= 0 ? regionTree[activeIdx].name : '';
          setSelection(regionName, code, codeToStores[code] || [], regionName + ' / ' + item.textContent);
        });
        trigger.addEventListener('click', function() { if (panel.classList.contains('open')) closePanel(); else openPanel(); });
        document.addEventListener('click', function(e) { if (!document.getElementById('cascadeWrap').contains(e.target)) closePanel(); });
        window._clearCascade = clearCascade;
      }

      function syncStoreOptions() {
        var sel = document.getElementById('qStore');
        var prev = sel.value;
        sel.innerHTML = '<option value="">请选择店铺</option>';
        var list = cascadeSelection.stores.length ? cascadeSelection.stores : allStores;
        list.forEach(function(s) { sel.innerHTML += '<option value="' + s + '">' + s + '</option>'; });
        if (list.indexOf(prev) !== -1) sel.value = prev; else sel.value = '';
      }

      initCascade();
      syncStoreOptions();

      var spusByShop = {
        '美国 TK・艾斯特尼 - 美区特 1 店 US': ['AL-W0161', 'AL-W0180', 'AL-W0169', 'AL-W5558'],
        '美国 TK・艾斯特尼 - 美区特 2 店 US': ['AL-W0161'],
        '美国 TK・艾斯特尼 - 美区特 3 店 US': ['ALYMX-DROPSW'],
        '美国 TK・艾斯特尼 - 欧洲直邮店 DE': ['AL-W0161'],
        '美国 TK・艾斯特尼 - 欧洲直邮店 ES': ['AL-W0161', 'AL-W0180'],
        '美国 TK・艾斯特尼 - 欧洲直邮店 FR': ['AL-W0169'],
        '美国 TK・艾斯特尼 - 欧洲直邮店 IT': ['AL-W0161'],
        '美国TK独立站-shopify:Global': ['AL-W5558']
      };
      var pidsBySpu = {
        'AL-W0161':    ['1729439482671567205', '1729773126172578149', '1729416165725475173', '1729380011223344556'],
        'AL-W0180':    ['1731657241623302501', '1731657241623302502'],
        'AL-W0169':    ['1729355500112233445', '1729322000112233444'],
        'AL-W5558':    ['1729300000112233443'],
        'ALYMX-DROPSW':['1729416165725475173', '1729380011223344556']
      };
      var pidSpuManageData = [
        { store: '美国 TK・艾斯特尼 - 美区特 1 店 US', pid: '1729439482671567205', mainSpu: 'AL-W0161', createdAt: '2026-03-18 10:22:31', updatedAt: '2026-04-12 16:10:08' },
        { store: '美国 TK・艾斯特尼 - 美区特 1 店 US', pid: '1729773126172578149', mainSpu: 'AL-W0161', createdAt: '2026-03-18 10:25:16', updatedAt: '2026-04-12 16:10:08' },
        { store: '美国 TK・艾斯特尼 - 美区特 2 店 US', pid: '1731657241623302501', mainSpu: 'AL-W0180', createdAt: '2026-03-19 09:43:20', updatedAt: '2026-04-12 16:11:32' },
        { store: '美国 TK・艾斯特尼 - 美区特 2 店 US', pid: '1731657241623302502', mainSpu: 'AL-W0180', createdAt: '2026-03-19 09:44:08', updatedAt: '2026-04-12 16:11:32' },
        { store: '美国 TK・艾斯特尼 - 欧洲直邮店 DE', pid: '1729416165725475173', mainSpu: 'ALYMX-DROPSW', createdAt: '2026-03-20 14:08:45', updatedAt: '2026-04-15 11:36:40' },
        { store: '美国 TK・艾斯特尼 - 欧洲直邮店 FR', pid: '1729380011223344556', mainSpu: 'AL-W0169', createdAt: '2026-03-20 14:10:03', updatedAt: '2026-04-15 11:36:40' },
        { store: '美国 TK・艾斯特尼 - 欧洲直邮店 IT', pid: '1729355500112233445', mainSpu: 'AL-W0169', createdAt: '2026-03-21 08:31:12', updatedAt: '2026-04-16 09:05:17' },
        { store: '美国TK独立站-shopify:Global', pid: '1729300000112233443', mainSpu: 'AL-W5558', createdAt: '2026-03-21 08:35:56', updatedAt: '2026-04-16 09:05:17' }
      ];
      var editingPidSpuRecord = null;

      function hash(str) {
        var h = 5381;
        for (var i = 0; i < str.length; i++) h = ((h << 5) + h) + str.charCodeAt(i);
        return Math.abs(h);
      }
      function mockPidQty(pid, dateStr) {
        var h = hash(pid + dateStr);
        if (pid.endsWith('556') || pid.endsWith('443')) return 1 + (h % 5);
        if (pid.endsWith('502')) return 10 + (h % 20);
        return 15 + (h % 60);
      }

      function fmtDate(d) {
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
      }
      function fmtLabel(d) {
        return d.getFullYear() + '/' + (d.getMonth() + 1) + '/' + d.getDate();
      }
      function parseDate(s) { return new Date(s + 'T12:00:00'); }

      function enumDays(start, end) {
        var out = [], d = parseDate(start), last = parseDate(end);
        while (d <= last) { out.push(fmtDate(d)); d.setDate(d.getDate() + 1); }
        return out;
      }

      function getISOWeek(d) {
        var dt = new Date(d.getTime());
        dt.setHours(0, 0, 0, 0);
        dt.setDate(dt.getDate() + 3 - (dt.getDay() + 6) % 7);
        var week1 = new Date(dt.getFullYear(), 0, 4);
        var wn = 1 + Math.round(((dt.getTime() - week1.getTime()) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
        return dt.getFullYear() + '-W' + String(wn).padStart(2, '0');
      }

      function shortMMDD(dateStr) {
        var p = dateStr.split('-');
        return p[1] + '/' + p[2];
      }

      function buildBuckets(days, gran) {
        if (gran === 'day') return days.map(function(d) {
          var dt = parseDate(d);
          return { label: fmtLabel(dt), days: [d] };
        });
        var map = {}, order = [];
        days.forEach(function(d) {
          var key;
          if (gran === 'week') key = getISOWeek(parseDate(d));
          else if (gran === 'month') key = d.slice(0, 7);
          else if (gran === 'quarter') key = d.slice(0, 4) + '-Q' + Math.ceil(parseInt(d.slice(5, 7), 10) / 3);
          else if (gran === 'year') key = d.slice(0, 4);
          else key = d.slice(0, 7);
          if (!map[key]) { map[key] = []; order.push(key); }
          map[key].push(d);
        });
        return order.map(function(k) {
          var ds = map[k];
          var label = (gran === 'week') ? (shortMMDD(ds[0]) + '~' + shortMMDD(ds[ds.length - 1])) : k;
          return { label: label, days: ds };
        });
      }

      function pidBucketQty(pid, bucket) {
        var s = 0;
        bucket.days.forEach(function(d) { s += mockPidQty(pid, d); });
        return s;
      }

      /** 环比百分比：本期 vs 上期（日→昨天，周→上周，月→上月，季→上季，年→去年）。返回展示用字符串，如 +12.5% / -8.0% / — */
      function fmtChainRatio(current, previous) {
        if (previous === 0) return current === 0 ? '0%' : '—';
        var pct = ((current - previous) / previous) * 100;
        var sign = pct >= 0 ? '+' : '';
        return sign + (Math.round(pct * 10) / 10) + '%';
      }

      function getDateRange() {
        return { start: document.getElementById('qStartDate').value, end: document.getElementById('qEndDate').value };
      }

      function getFiltered() {
        var store = document.getElementById('qStore').value;
        if (!store || !spusByShop[store]) return null;
        var spus = spusByShop[store];
        var field = document.getElementById('qSearchField').value;
        var keyword = (document.getElementById('qSearchVal').value || '').trim().toLowerCase();
        if (keyword) {
          if (field === 'spu') {
            spus = spus.filter(function(s) { return s.toLowerCase().indexOf(keyword) !== -1; });
          } else if (field === 'pid') {
            spus = spus.filter(function(spu) {
              var pids = pidsBySpu[spu] || [];
              return pids.some(function(p) { return p.toLowerCase().indexOf(keyword) !== -1; });
            });
          }
        }
        return { store: store, name: store, spus: spus };
      }

      function render() {
        var data = getFiltered();
        var tbody = document.getElementById('resultBody');
        var range = getDateRange();

        if (!data || !data.spus.length || !range.start || !range.end || range.start > range.end) {
          tbody.innerHTML = '<tr><td colspan="' + (curView === 'spu' ? '10' : '12') + '" class="empty-tip">请选择店铺后点击「查询」</td></tr>';
          return;
        }

        var days = enumDays(range.start, range.end);
        var buckets = buildBuckets(days, curGran).reverse();
        var granLabel = curGran === 'day' ? '日' : curGran === 'week' ? '周' : curGran === 'month' ? '月' : curGran === 'quarter' ? '季' : '年';
        var diffLabel = '环比';
        document.getElementById('filterInfo').textContent =
          '店铺：' + data.name + '　日期：' + range.start + ' 至 ' + range.end + '　日期类型：' + granLabel + '　维度：' + (curView === 'spu' ? 'SPU汇总' : 'PID明细');

        var bLen = buckets.length;
        var thead = document.getElementById('resultHead');
        if (curView === 'spu') {
          thead.innerHTML =
            '<tr><th class="sticky-col-1">店铺名</th><th class="sticky-col-2">SPU(公式)</th>' +
            '<th class="sticky-col-3">小计</th><th class="sticky-col-4">平均值</th><th class="sticky-col-5">' + diffLabel + '</th>' +
            '<th colspan="' + bLen + '">计数项: SKU sold quantity in the order.</th>' +
            '</tr>' +
            '<tr><th class="sticky-col-1"></th><th class="sticky-col-2"></th><th class="sticky-col-3"></th><th class="sticky-col-4"></th><th class="sticky-col-5"></th>' +
            buckets.map(function(b) { return '<th>' + b.label + '</th>'; }).join('') +
            '</tr>';
        } else {
          thead.innerHTML =
            '<tr><th class="sticky-col-1">店铺名</th><th class="sticky-col-2">SPU(公式)</th><th class="sticky-col-3">PID</th><th class="sticky-col-4">分析</th>' +
            '<th class="sticky-col-5">小计</th><th class="sticky-col-6">平均值</th><th class="sticky-col-7">' + diffLabel + '</th>' +
            '<th colspan="' + bLen + '">计数项: SKU sold quantity in the order.</th>' +
            '</tr>' +
            '<tr><th class="sticky-col-1"></th><th class="sticky-col-2"></th><th class="sticky-col-3"></th><th class="sticky-col-4"></th><th class="sticky-col-5"></th><th class="sticky-col-6"></th><th class="sticky-col-7"></th>' +
            buckets.map(function(b) { return '<th>' + b.label + '</th>'; }).join('') +
            '</tr>';
        }

        function sumArr(arr) { return arr.reduce(function(a, b) { return a + b; }, 0); }
        function avgArr(arr) { return arr.length ? Math.round(sumArr(arr) / arr.length) : 0; }

        var groups = [];
        data.spus.forEach(function(spu) {
          var pids = pidsBySpu[spu] || [];
          var pidRows = pids.map(function(pid) {
            var vals = buckets.map(function(b) { return pidBucketQty(pid, b); });
            var s1 = vals.length >= 1 ? vals[vals.length - 1] : 0;
            var s2 = vals.length >= 2 ? vals[vals.length - 2] : 0;
            var diffNum = s1 - s2;
            var diffStr = fmtChainRatio(s1, s2);
            var sub = sumArr(vals);
            var avg = avgArr(vals);
            return { pid: pid, vals: vals, diffNum: diffNum, diffStr: diffStr, sub: sub, avg: avg };
          });
          var totals = buckets.map(function(_, i) {
            var s = 0; pidRows.forEach(function(pr) { s += pr.vals[i]; }); return s;
          });
          var t1 = totals.length >= 1 ? totals[totals.length - 1] : 0;
          var t2 = totals.length >= 2 ? totals[totals.length - 2] : 0;
          var totalDiffNum = t1 - t2;
          var totalDiffStr = fmtChainRatio(t1, t2);
          var totalSub = sumArr(totals);
          var totalAvg = avgArr(totals);
          groups.push({ spu: spu, totals: totals, totalDiffNum: totalDiffNum, totalDiffStr: totalDiffStr, totalSub: totalSub, totalAvg: totalAvg, pidRows: pidRows });
        });

        groups.sort(function(a, b) { return (b.totalSub || 0) - (a.totalSub || 0); });

        var storeTotals = buckets.map(function(_, i) {
          var s = 0;
          groups.forEach(function(g) { s += g.totals[i] || 0; });
          return s;
        });
        var storeTotalSub = sumArr(storeTotals);
        var storeTotalAvg = avgArr(storeTotals);
        var storeT1 = storeTotals.length >= 1 ? storeTotals[storeTotals.length - 1] : 0;
        var storeT2 = storeTotals.length >= 2 ? storeTotals[storeTotals.length - 2] : 0;
        var storeDiffStr = fmtChainRatio(storeT1, storeT2);

        var html = '';
        if (curView === 'spu') {
          var spuRowCount = groups.length + 1;
          groups.forEach(function(group, gidx) {
            html += '<tr class="spu-row">';
            if (gidx === 0) {
              html += '<td class="sticky-col-1" rowspan="' + spuRowCount + '">' + data.name + '</td>';
            }
            html += '<td class="sticky-col-2"><span class="spu-cell"><span class="spu-name">' + group.spu + '</span></span></td>';
            html += '<td class="sticky-col-3" style="font-weight:600;">' + group.totalSub + '</td>';
            html += '<td class="sticky-col-4" style="font-weight:600;">' + group.totalAvg + '</td>';
            html += '<td class="sticky-col-5 ' + (group.totalDiffNum < 0 ? 'diff-neg' : '') + '">' + group.totalDiffStr + '</td>';
            group.totals.forEach(function(v) { html += '<td>' + v + '</td>'; });
            html += '</tr>';
          });
        } else {
          var totalRowCount = 0;
          groups.forEach(function(g) { totalRowCount += 1 + g.pidRows.length; });
          totalRowCount += 1;

          var firstRow = true;
          groups.forEach(function(group, gidx) {
            var rowspan = 1 + group.pidRows.length;

            html += '<tr class="spu-row">';
            if (firstRow) {
              html += '<td class="sticky-col-1" rowspan="' + totalRowCount + '">' + data.name + '</td>';
              firstRow = false;
            }
            html += '<td class="sticky-col-2" rowspan="' + rowspan + '"><span class="spu-cell"><span class="spu-name">' + group.spu + '</span> <button type="button" class="btn-ai-spu" data-gidx="' + gidx + '" title="AI 分析（' + group.spu + '）"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L9.5 8.5L3 9l5 4.5L6.5 21L12 17l5.5 4-1.5-7.5L21 9l-6.5-.5L12 2z"/></svg></button></span></td>';
            html += '<td class="sticky-col-3">合计</td>';
            html += '<td class="sticky-col-4">—</td>';
            html += '<td class="sticky-col-5" style="font-weight:600;">' + group.totalSub + '</td>';
            html += '<td class="sticky-col-6" style="font-weight:600;">' + group.totalAvg + '</td>';
            html += '<td class="sticky-col-7 ' + (group.totalDiffNum < 0 ? 'diff-neg' : '') + '">' + group.totalDiffStr + '</td>';
            group.totals.forEach(function(v) { html += '<td>' + v + '</td>'; });
            html += '</tr>';

            var spuEnc = encodeURIComponent(group.spu || '');
            var storeEnc = encodeURIComponent(data.name || '');
            group.pidRows.forEach(function(pr) {
              html += '<tr>';
              html += '<td class="sticky-col-3">' + pr.pid + '</td>';
              html += '<td class="sticky-col-4"><button type="button" class="btn-detail-analysis" title="PID 明细" data-spu="' + spuEnc + '" data-store="' + storeEnc + '"><svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M3.5 18.49l6-6.01 4 4L20 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/></svg></button></td>';
              html += '<td class="sticky-col-5">' + pr.sub + '</td>';
              html += '<td class="sticky-col-6">' + pr.avg + '</td>';
              html += '<td class="sticky-col-7 ' + (pr.diffNum < 0 ? 'diff-neg' : '') + '">' + pr.diffStr + '</td>';
              pr.vals.forEach(function(v) { html += '<td>' + v + '</td>'; });
              html += '</tr>';
            });
          });
        }

        html += '<tr class="row-store-total">';
        html += '<td class="sticky-col-2">店铺小计合计</td>';
        if (curView === 'spu') {
          html += '<td class="sticky-col-3">' + storeTotalSub + '</td>';
          html += '<td class="sticky-col-4">' + storeTotalAvg + '</td>';
          html += '<td class="sticky-col-5">' + storeDiffStr + '</td>';
        } else {
          html += '<td class="sticky-col-3">—</td>';
          html += '<td class="sticky-col-4">—</td>';
          html += '<td class="sticky-col-5">' + storeTotalSub + '</td>';
          html += '<td class="sticky-col-6">' + storeTotalAvg + '</td>';
          html += '<td class="sticky-col-7">' + storeDiffStr + '</td>';
        }
        storeTotals.forEach(function(v) { html += '<td>' + v + '</td>'; });
        html += '</tr>';

        tbody.innerHTML = html;

        var modal = document.getElementById('aiModal');
        var modalBody = document.getElementById('aiModalBody');
        function closeModal() { modal.classList.remove('visible'); }
        document.getElementById('aiModalClose').onclick = closeModal;
        modal.onclick = closeModal;

        tbody.querySelectorAll('.btn-ai-spu').forEach(function(btn) {
          btn.addEventListener('click', function(e) {
            e.stopPropagation();
            var gidx = parseInt(btn.getAttribute('data-gidx'), 10);
            var g = groups[gidx];
            if (!g) return;
            var bLabels = buckets.map(function(b) { return b.label; });
            modalBody.textContent = generateAiAnalysis(g, data.name, bLabels);
            document.getElementById('aiModalTitle').innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L9.5 8.5L3 9l5 4.5L6.5 21L12 17l5.5 4-1.5-7.5L21 9l-6.5-.5L12 2z"/></svg>AI 分析 · ' + g.spu;
            modal.classList.add('visible');
          });
        });
        tbody.querySelectorAll('.btn-detail-analysis').forEach(function(btn) {
          btn.addEventListener('click', function(e) {
            e.stopPropagation();
            var spu = decodeURIComponent(btn.getAttribute('data-spu') || '');
            var store = decodeURIComponent(btn.getAttribute('data-store') || '');
            window._detailAnalysisSpu = spu;
            window._detailAnalysisStore = store;
            var startEl = document.getElementById('detailStartDate');
            var endEl = document.getElementById('detailEndDate');
            if (startEl) startEl.value = '2025-12-10';
            if (endEl) endEl.value = '2026-03-12';
            document.querySelectorAll('#detailGranTabs .tab').forEach(function(t) { t.classList.toggle('active', t.getAttribute('data-gran') === 'day'); });
            window._detailAnalysisGran = 'day';
            renderDetailAnalysisTable();
            document.getElementById('detailModal').classList.add('visible');
          });
        });
      }

      function generateAiAnalysis(group, shopName, labels) {
        var t = group.totals;
        var s2 = t.length >= 2 ? t[t.length - 2] : 0;
        var s1 = t.length >= 1 ? t[t.length - 1] : 0;
        var trend = s1 >= s2 ? '环比上升' : '环比下降';
        var l2 = labels.length >= 2 ? labels[labels.length - 2] : '上期';
        var l1 = labels.length >= 1 ? labels[labels.length - 1] : '本期';
        var parts = [];
        parts.push('【' + shopName + ' · ' + group.spu + '】' + l2 + ' 合计 ' + s2 + ' 件，' + l1 + ' 合计 ' + s1 + ' 件，' + trend + '；环比 ' + group.totalDiffStr + '。');
        parts.push('共 ' + group.pidRows.length + ' 个 PID。');
        var negPids = group.pidRows.filter(function(p) { return p.diffNum < 0; });
        if (negPids.length) {
          parts.push('环比为负的 PID：' + negPids.map(function(p) { return p.pid.slice(-10) + '（' + p.diffStr + '）'; }).join('、') + '，建议关注库存或推广。');
        } else {
          parts.push('各 PID 环比均非负，趋势平稳。');
        }
        parts.push('以上为基于该 SPU 数据的结构化摘要，可配合运营做补货或复盘。');
        return parts.join('\n\n');
      }

      var DETAIL_COLS = 51;
      var detailHeaders = ['日期','PID','主推SPU','分析','客单价','平均补贴/单','财务GMV','商品交易总额4','成交件数5','订单数6','商品卡GMV31','直播GMV15','短视频GMV23','商品卡GMV占比','直播GMV占比','短视频GMV占比','商品卡商品交易总额33','商品卡成交件数32','客单价','曝光33','商品卡片的页面浏览次数36','去重浏览35','去重客户36','商品卡点击37','商品卡转化38','商品卡短视频商品交易总额25','短视频成交件数24','客单价','视频曝光次数25','来自视频的页面浏览次数28','来自视频的去重页面浏览次数27','视频去重商品客户数28','视频点击率29','视频转化率30','商务挂车量','剪辑挂车量','合计挂车量','商务开单视频','剪辑开单视频','开单视频合计','vas消耗','GMVMAX消耗','广告总消耗','广告单量','广告订单数','广告GMV','总GMV','总ACOAS','广告ROI（测算）','广告AcoAs','广告ROI设置数'];
      var detailAdColStart = 40;
      var detailPctCols = { 13: true, 14: true, 15: true, 29: true, 30: true };
      function detailMockCell(j, rowSeed) {
        if (j <= 3) return '';
        var s = rowSeed + j * 7;
        var r = (Math.sin(s) * 0.5 + 0.5);
        if (detailPctCols[j]) return (r * 25).toFixed(1) + '%';
        if (j >= 4 && j <= 12) return Math.round(50 + r * 800);
        if (j >= 16 && j <= 27) return Math.round(20 + r * 400);
        if (j >= 31 && j <= 39) return Math.round(r * 50);
        if (j >= 40) return Math.round(r * 2000);
        return Math.round(10 + r * 100);
      }
      function renderDetailAnalysisTable() {
        var thead = document.getElementById('detailAnalysisThead');
        var tbody = document.getElementById('detailAnalysisBody');
        if (!thead || !tbody) return;
        thead.innerHTML =
          '<tr><th class="th-module bg-blue">日期</th><th class="th-module bg-yellow" colspan="3">商品基础信息</th><th class="th-module bg-blue" colspan="12">GMV情况</th><th class="th-module bg-yellow" colspan="9">商品卡</th><th class="th-module bg-blue" colspan="9">短视频</th><th class="th-module bg-yellow" colspan="6">商务剪辑情况</th><th class="th-module bg-blue" colspan="11">广告情况</th></tr>' +
          '<tr>' + detailHeaders.map(function(h, i) {
            var cls = (i >= detailAdColStart) ? ' class="th-col col-num-right"' : ' class="th-col"';
            return '<th' + cls + '>' + String(h).replace(/</g, '&lt;') + '</th>';
          }).join('') + '</tr>';
        var startVal = document.getElementById('detailStartDate') && document.getElementById('detailStartDate').value;
        var endVal = document.getElementById('detailEndDate') && document.getElementById('detailEndDate').value;
        if (!startVal || !endVal || startVal > endVal) {
          tbody.innerHTML = '<tr><td colspan="' + DETAIL_COLS + '" style="text-align:center;color:var(--muted);padding:1rem;">请选择时间范围（开始～结束）</td></tr>';
          return;
        }
        var spu = window._detailAnalysisSpu || '—';
        var gran = window._detailAnalysisGran || 'day';
        var days = enumDays(startVal, endVal);
        var buckets = buildBuckets(days, gran);
        if (!buckets.length) {
          tbody.innerHTML = '<tr><td colspan="' + DETAIL_COLS + '" style="text-align:center;color:var(--muted);padding:1rem;">该时间范围内无数据</td></tr>';
          return;
        }
        var fakePids = ['AL-W0161', 'AL-W0169', 'AL-W0180', 'AL-W5558'];
        var rows = [];
        var totals = [];
        for (var j = 0; j < DETAIL_COLS; j++) totals[j] = (j <= 3 || detailPctCols[j]) ? null : 0;
        buckets.forEach(function(b, bi) {
          var pid = fakePids[bi % fakePids.length];
          var row = [b.label, pid, spu, '—'];
          for (var j = 4; j < DETAIL_COLS; j++) {
            var v = detailMockCell(j, bi * 13 + 1);
            row.push(v);
            if (!detailPctCols[j] && totals[j] !== null) {
              var n = parseFloat(String(v).replace('%', ''));
              if (!isNaN(n)) totals[j] += n;
            }
          }
          rows.push(row);
        });
        var trs = rows.map(function(row) {
          return '<tr>' + row.map(function(cell, i) {
            var cls = (i >= detailAdColStart) ? ' class="col-num-right"' : '';
            return '<td' + cls + '>' + String(cell).replace(/</g, '&lt;') + '</td>';
          }).join('') + '</tr>';
        });
        var totalCells = [];
        for (var j = 0; j < DETAIL_COLS; j++) {
          var cls = (j >= detailAdColStart) ? ' class="col-num-right"' : '';
          if (j === 0) { totalCells.push('<td' + cls + '>合计</td>'); continue; }
          if (j === 1 || j === 2 || j === 3) { totalCells.push('<td' + cls + '></td>'); continue; }
          if (detailPctCols[j]) { totalCells.push('<td' + cls + '></td>'); continue; }
          var val = totals[j] != null ? (Math.round(totals[j] * 100) / 100).toString() : '';
          totalCells.push('<td' + cls + '>' + val + '</td>');
        }
        tbody.innerHTML = trs.join('') + '<tr class="row-total">' + totalCells.join('') + '</tr>';
      }

      function escapeCell(v) {
        var s = String(v);
        if (s.indexOf('"') >= 0 || s.indexOf(',') >= 0 || s.indexOf('\n') >= 0) return '"' + s.replace(/"/g, '""') + '"';
        return s;
      }
      function escapeHtml(v) {
        return String(v == null ? '' : v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
      }
      function getNowDateTime() {
        var d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0') + ' ' +
          String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0') + ':' + String(d.getSeconds()).padStart(2, '0');
      }
      function initManageStoreOptions() {
        var sel = document.getElementById('manageStore');
        if (!sel) return;
        sel.innerHTML = '<option value="">全部店铺</option>' + allStores.map(function(store) {
          return '<option value="' + escapeHtml(store) + '">' + escapeHtml(store) + '</option>';
        }).join('');
      }
      function getManageFilteredData() {
        var store = (document.getElementById('manageStore').value || '').trim();
        var pid = (document.getElementById('managePid').value || '').trim().toLowerCase();
        var spu = (document.getElementById('manageSpu').value || '').trim().toLowerCase();
        return pidSpuManageData.filter(function(item) {
          if (store && item.store !== store) return false;
          if (pid && item.pid.toLowerCase().indexOf(pid) === -1) return false;
          if (spu && item.mainSpu.toLowerCase().indexOf(spu) === -1) return false;
          return true;
        });
      }
      function renderManagePidSpuTable() {
        var rows = getManageFilteredData();
        var tbody = document.getElementById('managePidSpuBody');
        var summary = document.getElementById('manageSummary');
        if (summary) summary.textContent = '共 ' + rows.length + ' 条记录';
        if (!tbody) return;
        if (!rows.length) {
          tbody.innerHTML = '<tr><td colspan="6" class="manage-empty">未匹配到符合条件的 PID 与主推SPU 记录</td></tr>';
          return;
        }
        tbody.innerHTML = rows.map(function(item) {
          return '<tr>' +
            '<td>' + escapeHtml(item.store) + '</td>' +
            '<td>' + escapeHtml(item.pid) + '</td>' +
            '<td>' + escapeHtml(item.mainSpu) + '</td>' +
            '<td>' + escapeHtml(item.createdAt) + '</td>' +
            '<td>' + escapeHtml(item.updatedAt) + '</td>' +
            '<td><button type="button" class="manage-action-btn" data-pid="' + escapeHtml(item.pid) + '" data-store="' + escapeHtml(item.store) + '">编辑</button></td>' +
            '</tr>';
        }).join('');
      }
      function openManagePidSpuModal() {
        renderManagePidSpuTable();
        document.getElementById('managePidSpuModal').classList.add('visible');
      }
      function closeManagePidSpuModal() {
        document.getElementById('managePidSpuModal').classList.remove('visible');
      }
      function openEditPidSpuModal(record) {
        if (!record) return;
        editingPidSpuRecord = record;
        document.getElementById('editStore').value = record.store;
        document.getElementById('editPid').value = record.pid;
        document.getElementById('editSpu').value = record.mainSpu;
        document.getElementById('editPidSpuModal').classList.add('visible');
      }
      function closeEditPidSpuModal() {
        editingPidSpuRecord = null;
        document.getElementById('editPidSpuModal').classList.remove('visible');
      }

      function doExport() {
        var data = getFiltered();
        var range = getDateRange();
        if (!data || !data.spus.length || !range.start || !range.end) {
          alert('请先选择店铺并点击「查询」后再导出');
          return;
        }
        var days = enumDays(range.start, range.end);
        var buckets = buildBuckets(days, curGran);
        var csvHeaders = curView === 'spu'
          ? ['店铺名', 'SPU(公式)', '小计', '平均值', '环比'].concat(buckets.map(function(b) { return b.label; }))
          : ['店铺名', 'SPU(公式)', 'PID'].concat(buckets.map(function(b) { return b.label; })).concat(['环比']);
        var lines = [csvHeaders.map(escapeCell).join(',')];

        data.spus.forEach(function(spu) {
          var pids = pidsBySpu[spu] || [];
          var pidRows = pids.map(function(pid) {
            var vals = buckets.map(function(b) { return pidBucketQty(pid, b); });
            var s1 = vals.length >= 1 ? vals[vals.length - 1] : 0;
            var s2 = vals.length >= 2 ? vals[vals.length - 2] : 0;
            var diffStr = fmtChainRatio(s1, s2);
            return { pid: pid, vals: vals, diffStr: diffStr };
          });
          var totals = buckets.map(function(_, i) {
            var s = 0; pidRows.forEach(function(pr) { s += pr.vals[i]; }); return s;
          });
          var t1 = totals.length >= 1 ? totals[totals.length - 1] : 0;
          var t2 = totals.length >= 2 ? totals[totals.length - 2] : 0;
          var totalDiffStr = fmtChainRatio(t1, t2);
          var totalAvg = avgArr(totals);
          if (curView === 'spu') {
            var totalSub = sumArr(totals);
            lines.push([data.name, spu, totalSub, totalAvg, totalDiffStr].concat(totals).map(escapeCell).join(','));
          } else {
            pidRows.forEach(function(pr) {
              lines.push([data.name, spu, pr.pid].concat(pr.vals).concat([pr.diffStr]).map(escapeCell).join(','));
            });
          }
        });

        var csv = '\uFEFF' + lines.join('\n');
        var blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = '销量趋势_' + data.name + '_' + range.start + '_' + range.end + '.csv';
        a.click();
        URL.revokeObjectURL(a.href);
      }

      function bindTabs(groupId, setter) {
        var group = document.getElementById(groupId);
        group.querySelectorAll('.tab').forEach(function(tab) {
          tab.addEventListener('click', function() {
            group.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
            tab.classList.add('active');
            setter(tab);
            render();
          });
        });
      }
      bindTabs('granTabs', function(tab) { curGran = tab.getAttribute('data-gran'); });
      bindTabs('viewTabs', function(tab) { curView = tab.getAttribute('data-view'); });

      document.getElementById('btnQuery').onclick = render;
      document.getElementById('btnReset').onclick = function() {
        if (window._clearCascade) window._clearCascade();
        document.getElementById('qStore').value = '';
        document.getElementById('qStartDate').value = '2025-06-01';
        document.getElementById('qEndDate').value = '2026-03-10';
        document.getElementById('qSearchField').value = 'spu';
        document.getElementById('qSearchVal').value = '';
        curGran = 'day';
        curView = 'spu';
        document.querySelectorAll('#granTabs .tab').forEach(function(t) { t.classList.toggle('active', t.getAttribute('data-gran') === 'day'); });
        document.querySelectorAll('#viewTabs .tab').forEach(function(t) { t.classList.toggle('active', t.getAttribute('data-view') === 'spu'); });
        document.getElementById('filterInfo').textContent = '';
        document.getElementById('resultBody').innerHTML = '<tr><td colspan="12" class="empty-tip">请选择店铺后点击「查询」</td></tr>';
      };
      document.getElementById('btnMetricHelp').onclick = function() {
        alert([
          '数据统计说明',
          '1. 订单数据每半小时更新一次，SPU 主数据按天同步，两个刷新链路独立执行。',
          '2. 查询支持店铺单选，也支持先按站点筛选后联动收敛可选店铺列表。',
          '3. 统计时间按店铺所属市场本地时间归集，仅纳入订单金额不为 0 且非取消状态的订单明细。',
          '4. 顶部支持 SPU汇总 / PID明细 两种维度切换，默认展示 PID明细。',
          '5. 小计、平均值与环比均基于当前时间粒度区间计算。'
        ].join('\n'));
      };
      initManageStoreOptions();
      document.getElementById('btnManagePidSpu').onclick = openManagePidSpuModal;
      document.getElementById('btnCloseManagePidSpu').onclick = closeManagePidSpuModal;
      document.getElementById('managePidSpuModal').onclick = function(e) { if (e.target === this) closeManagePidSpuModal(); };
      document.getElementById('btnQueryManagePidSpu').onclick = renderManagePidSpuTable;
      document.getElementById('btnResetManagePidSpu').onclick = function() {
        document.getElementById('manageStore').value = '';
        document.getElementById('managePid').value = '';
        document.getElementById('manageSpu').value = '';
        renderManagePidSpuTable();
      };
      document.getElementById('managePidSpuBody').addEventListener('click', function(e) {
        var btn = e.target.closest('.manage-action-btn');
        if (!btn) return;
        var pid = btn.getAttribute('data-pid');
        var store = btn.getAttribute('data-store');
        var record = pidSpuManageData.find(function(item) { return item.pid === pid && item.store === store; });
        openEditPidSpuModal(record);
      });
      document.getElementById('btnCloseEditPidSpu').onclick = closeEditPidSpuModal;
      document.getElementById('btnCancelEditPidSpu').onclick = closeEditPidSpuModal;
      document.getElementById('editPidSpuModal').onclick = function(e) { if (e.target === this) closeEditPidSpuModal(); };
      document.getElementById('btnSaveEditPidSpu').onclick = function() {
        if (!editingPidSpuRecord) return;
        var newSpu = (document.getElementById('editSpu').value || '').trim();
        if (!newSpu) {
          alert('请输入主推SPU');
          return;
        }
        editingPidSpuRecord.mainSpu = newSpu;
        editingPidSpuRecord.updatedAt = getNowDateTime();
        renderManagePidSpuTable();
        closeEditPidSpuModal();
        alert('主推SPU 已更新');
      };
      document.getElementById('btnExport').onclick = doExport;
      (function() {
        var dm = document.getElementById('detailModal');
        var dmClose = document.getElementById('detailModalClose');
        function closeDetailModal() { if (dm) dm.classList.remove('visible'); }
        if (dmClose) dmClose.onclick = closeDetailModal;
        if (dm) dm.onclick = function(e) { if (e.target === dm) closeDetailModal(); };
        var granTabs = document.getElementById('detailGranTabs');
        if (granTabs) granTabs.addEventListener('click', function(e) {
          var tab = e.target.closest('.tab'); if (!tab) return;
          granTabs.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
          tab.classList.add('active');
          window._detailAnalysisGran = tab.getAttribute('data-gran');
          if (typeof renderDetailAnalysisTable === 'function') renderDetailAnalysisTable();
        });
        ['detailStartDate', 'detailEndDate'].forEach(function(id) {
          var el = document.getElementById(id); if (el) el.addEventListener('change', function() { if (typeof renderDetailAnalysisTable === 'function') renderDetailAnalysisTable(); });
        });
      })();

      document.getElementById('btnExportImg').onclick = function() {
        var tableCard = document.querySelector('.table-card');
        if (!tableCard) { alert('暂无表格内容'); return; }
        var wrap = tableCard.querySelector('.table-wrap');
        var origOverflow = wrap.style.overflow;
        wrap.style.overflow = 'visible';
        html2canvas(tableCard, { scale: 2, useCORS: true, backgroundColor: '#fff' }).then(function(canvas) {
          wrap.style.overflow = origOverflow;
          var a = document.createElement('a');
          a.href = canvas.toDataURL('image/png');
          var data = getFiltered();
          var range = getDateRange();
          a.download = '商品统计_' + (data ? data.name : '') + '_' + (range.start || '') + '_' + (range.end || '') + '.png';
          a.click();
        }).catch(function() {
          wrap.style.overflow = origOverflow;
          alert('导出图片失败，请重试');
        });
      };

      document.getElementById('qStore').value = '美国 TK・艾斯特尼 - 美区特 1 店 US';
      document.getElementById('qStartDate').value = '2025-06-01';
      document.getElementById('qEndDate').value = '2026-03-10';
      render();
    })();
  