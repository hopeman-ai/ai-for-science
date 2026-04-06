const CN={korea:'한국',japan:'일본',china:'중국',usa:'미국',eu:'EU'};
const CF={korea:'🇰🇷',japan:'🇯🇵',china:'🇨🇳',usa:'🇺🇸',eu:'🇪🇺'};
const CO=['korea','japan','china','usa','eu'];
let D={};

document.addEventListener('DOMContentLoaded',async()=>{
  setupTabs();
  await loadAll();
  renderAbout();
  renderStrategy();
  renderComparison();
  renderExecution();
  renderInsights();
  renderReferences('all');
});

async function loadAll(){
  const B='api/';
  const[a,b,c,d,e,f,g,h]=await Promise.all([
    fetch(B+'overview.json').then(r=>r.json()),
    fetch(B+'dimensions.json').then(r=>r.json()),
    fetch(B+'comparisons.json').then(r=>r.json()),
    fetch(B+'references.json').then(r=>r.json()),
    fetch(B+'ai-for-science.json').then(r=>r.json()),
    fetch(B+'execution.json').then(r=>r.json()),
    fetch(B+'external-resources.json').then(r=>r.json()).catch(()=>[]),
    fetch(B+'dashboard.json').then(r=>r.json()).catch(()=>({})),
  ]);
  D.overview=a; D.dims=b; D.refs=d; D.afs=e; D.exec=f; D.extRes=g; D.dash=h;
  D.comps={}; c.forEach(x=>{D.comps[x.dimension]=x});
  try{
    D.insights=await fetch(B+'insights.json').then(r=>r.json());
  }catch(e){D.insights={}}
  D.evalSummary={}; D.evidenceIndex={};
}

function setupTabs(){
  document.querySelectorAll('.tab-btn').forEach(btn=>{
    btn.addEventListener('click',()=>{
      document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-'+btn.dataset.tab).classList.add('active');
    });
  });
}

/* ===== 검증 배지 및 근거 보기 헬퍼 ===== */
function getVerificationBadge(section){
  const ev=D.evalSummary||{};
  const info=ev[section];
  if(!info) return'<span class="verify-badge draft">미검증</span>';
  const score=info.final_score||0;
  const verdict=info.final_verdict||'';
  if(verdict==='pass'||score>=90) return`<span class="verify-badge pass">검증 완료 ${score}점</span>`;
  if(verdict==='revise') return`<span class="verify-badge revise">수정 검토 ${score}점</span>`;
  if(verdict==='escalate') return`<span class="verify-badge escalate">전문가 검토 필요</span>`;
  return`<span class="verify-badge hold">게시 보류 ${score}점</span>`;
}

function getEvidenceButton(section){
  const ei=D.evidenceIndex||{};
  const links=(ei.content_links||[]).filter(l=>l.target_section.startsWith(section));
  if(!links.length) return'';
  const chunks=ei.evidence_chunks||[];
  const evIds=links.flatMap(l=>l.evidence_ids);
  const sources=chunks.filter(c=>evIds.includes(c.evidence_id));
  if(!sources.length) return'';
  const tooltipItems=sources.map(s=>`${s.document_title} (${s.issuing_body}, ${s.year})`).join('\\n');
  return`<button class="ev-btn" title="${tooltipItems}" onclick="alert('근거 출처:\\n${tooltipItems.replace(/'/g,"\\'")}')">근거 보기 (${sources.length})</button>`;
}

/* ===== TAB 1: AI for Science ===== */
function renderAbout(){
  const a=D.afs; if(!a||!a.definition) return;
  const def=a.definition, imp=a.importance, comp=a.components, tr=a.global_trends;
  const dash=D.dash||{};
  const gs=dash.globalSnapshot||{};
  const ss=dash.strategyStructure||{};
  const dr=dash.dataReliability||{};
  const pos=dash.positioning||{};

  document.getElementById('tab-about').innerHTML=`
    <div class="banner banner-blue">
      <div class="bl">AI for Science 정의</div>
      <div class="bt"><strong>${def.summary}</strong></div>
      <div class="bt" style="margin-top:8px;font-size:.88rem;opacity:.9">${def.description}</div>
    </div>

    ${gs.countries?`
    <div class="dash-section">
      <div class="stitle"><h2>${gs.title||'글로벌 전략 스냅샷'}</h2><p>${gs.subtitle||''}</p></div>
      <div class="snapshot-grid">${gs.countries.map(c=>`
        <div class="snapshot-card">
          <div class="snap-flag">${c.flag}</div>
          <div class="snap-name">${c.name}</div>
          <div class="snap-type">${c.type}</div>
        </div>
      `).join('')}</div>
    </div>`:''}

    ${ss.cards?`
    <div class="dash-section">
      <div class="stitle"><h2>${ss.title||'전략 구조 요약'}</h2><p>${ss.subtitle||''}</p></div>
      <div class="structure-grid">${ss.cards.map(c=>`
        <div class="structure-card">
          <div class="str-icon">${c.icon}</div>
          <div class="str-label">${c.label}</div>
          <div class="str-value">${c.value}</div>
          <div class="str-countries">${c.countries}</div>
          <div class="str-desc">${c.desc}</div>
        </div>
      `).join('')}</div>
      ${ss.note?`<div class="structure-note">${ss.note}</div>`:''}
    </div>`:''}

    ${pos.countries?`
    <div class="dash-section">
      <div class="stitle"><h2>${pos.title||'국가 전략 포지셔닝'}</h2><p>${pos.subtitle||''}</p></div>
      <div class="chart-container">
        <div class="chart-wrapper">
          <canvas id="posChart" width="700" height="500"></canvas>
        </div>
        <div class="chart-legend">
          ${pos.countries.map(c=>`
            <div class="legend-item">
              <span class="legend-dot" style="background:${c.color}"></span>
              <span class="legend-flag">${c.flag}</span>
              <span class="legend-name">${c.name}</span>
              <span class="legend-type">${c.type}</span>
            </div>
          `).join('')}
        </div>
        <div class="chart-note">${pos.note||''}</div>
      </div>
    </div>`:''}

    ${dr.items?`
    <div class="dash-section reliability-section">
      <div class="stitle"><h2>${dr.title||'데이터 기반 정보'}</h2></div>
      <div class="reliability-grid">${dr.items.map(i=>`
        <div class="rel-item"><span class="rel-value">${i.value}</span> <span class="rel-label">${i.label}</span><span class="rel-desc"> · ${i.desc}</span></div>
      `).join('')}</div>
    </div>`:''}

    <div class="stitle"><h2>핵심 개념</h2></div>
    <div class="concept-grid">${def.key_aspects.map(k=>`
      <div class="concept-card"><div class="concept-term">${k.term}</div><div class="concept-desc">${k.desc}</div></div>
    `).join('')}</div>

    <div class="stitle mt2"><h2>왜 중요한가</h2></div>
    <div class="grid g1" style="gap:1rem">${imp.reasons.map(r=>`
      <div class="rcard"><div class="rl">${r.label}</div><div class="rd">${r.detail}</div></div>
    `).join('')}</div>

    <div class="stitle mt2"><h2>핵심 구성요소</h2></div>
    <div class="grid g5">${comp.items.map(c=>`
      <div class="cmpcard">
        <div class="cicon">${c.icon}</div>
        <div class="cname">${c.name}</div>
        <ul class="celems">${c.elements.map(e=>`<li>${e}</li>`).join('')}</ul>
        <div class="cstatus">${c.status}</div>
      </div>
    `).join('')}</div>

    <div class="stitle mt2"><h2>글로벌 트렌드</h2></div>
    <div class="grid g1" style="gap:1rem">${tr.trends.map(t=>`
      <div class="rcard"><div class="ry">${t.year}</div><div class="rl">${t.label}</div><div class="rd">${t.detail}</div></div>
    `).join('')}</div>
  `;

  // 포지셔닝 차트 그리기
  if(pos.countries){
    requestAnimationFrame(()=>drawPositioningChart(pos));
  }
}

function drawPositioningChart(pos){
  const canvas=document.getElementById('posChart');
  if(!canvas) return;
  const dpr=window.devicePixelRatio||1;
  const rect=canvas.parentElement.getBoundingClientRect();
  const W=Math.min(rect.width,700);
  const H=Math.round(W*0.7);
  canvas.width=W*dpr; canvas.height=H*dpr;
  canvas.style.width=W+'px'; canvas.style.height=H+'px';
  const ctx=canvas.getContext('2d');
  ctx.scale(dpr,dpr);

  const pad={top:40,right:30,bottom:50,left:50};
  const cw=W-pad.left-pad.right, ch=H-pad.top-pad.bottom;

  // 배경
  ctx.fillStyle='#f8fafc'; ctx.fillRect(0,0,W,H);

  // 사분면 배경
  ctx.fillStyle='#f0f4ff'; ctx.fillRect(pad.left,pad.top,cw/2,ch/2);
  ctx.fillStyle='#f0fdf4'; ctx.fillRect(pad.left+cw/2,pad.top,cw/2,ch/2);
  ctx.fillStyle='#fefce8'; ctx.fillRect(pad.left,pad.top+ch/2,cw/2,ch/2);
  ctx.fillStyle='#fdf2f8'; ctx.fillRect(pad.left+cw/2,pad.top+ch/2,cw/2,ch/2);

  // 그리드
  ctx.strokeStyle='#e2e8f0'; ctx.lineWidth=1;
  ctx.setLineDash([4,4]);
  for(let i=0;i<=4;i++){
    const x=pad.left+(cw/4)*i;
    ctx.beginPath(); ctx.moveTo(x,pad.top); ctx.lineTo(x,pad.top+ch); ctx.stroke();
    const y=pad.top+(ch/4)*i;
    ctx.beginPath(); ctx.moveTo(pad.left,y); ctx.lineTo(pad.left+cw,y); ctx.stroke();
  }
  ctx.setLineDash([]);

  // 축 (중앙)
  ctx.strokeStyle='#94a3b8'; ctx.lineWidth=1.5;
  const cx=pad.left+cw/2, cy=pad.top+ch/2;
  ctx.beginPath(); ctx.moveTo(pad.left,cy); ctx.lineTo(pad.left+cw,cy); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx,pad.top); ctx.lineTo(cx,pad.top+ch); ctx.stroke();

  // 축 라벨
  ctx.fillStyle='#64748b'; ctx.font='600 11px -apple-system,sans-serif'; ctx.textAlign='center';
  ctx.fillText(pos.axisX.min,pad.left+cw*0.15,H-12);
  ctx.fillText(pos.axisX.max,pad.left+cw*0.85,H-12);
  ctx.save(); ctx.translate(14,pad.top+ch*0.85); ctx.rotate(-Math.PI/2);
  ctx.fillText(pos.axisY.min,0,0); ctx.restore();
  ctx.save(); ctx.translate(14,pad.top+ch*0.15); ctx.rotate(-Math.PI/2);
  ctx.fillText(pos.axisY.max,0,0); ctx.restore();

  // 국가 마커
  pos.countries.forEach(c=>{
    const px=pad.left+(c.x/100)*cw;
    const py=pad.top+((100-c.y)/100)*ch;

    // 그림자
    ctx.beginPath(); ctx.arc(px,py,22,0,Math.PI*2);
    ctx.fillStyle=c.color+'18'; ctx.fill();

    // 원
    ctx.beginPath(); ctx.arc(px,py,16,0,Math.PI*2);
    ctx.fillStyle='#fff'; ctx.fill();
    ctx.strokeStyle=c.color; ctx.lineWidth=3; ctx.stroke();

    // 국기
    ctx.font='15px serif'; ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(c.flag,px,py);

    // 국가명 라벨
    ctx.font='700 12px -apple-system,sans-serif'; ctx.fillStyle='#1e293b';
    ctx.textBaseline='top';
    ctx.fillText(c.name,px,py+22);
  });
}

/* ===== TAB 2: 국가 전략 ===== */
function renderStrategy(){
  const{countries}=D.overview;
  const md=buildOverviewMd(countries);
  document.getElementById('tab-strategy').innerHTML=`
    <div class="stitle"><h2>국가별 전략 개요</h2><p>5개국의 AI for Science 핵심 전략을 한눈에 비교합니다.</p></div>
    <div class="grid g5">${CO.map(k=>{const c=countries[k];return`
      <div class="cc" data-c="${k}">
        <div class="ct"><span class="flag">${c.flag}</span><span class="cn">${c.name}</span></div>
        <div class="sb"><span class="pill">${c.strategy_type}</span></div>
        <div class="ol">${c.one_line}</div>
        <div class="mt">
          <div class="mr"><span class="ml">핵심 문제</span><span class="mv">${c.core_problem}</span></div>
          <div class="mr"><span class="ml">접근 방식</span><span class="mv">${c.key_approach}</span></div>
          <div class="mr"><span class="ml">추진 기관</span><span class="mv">${c.lead_agency}</span></div>
        </div>
      </div>`;}).join('')}</div>
    <div class="stitle mt2"><h2>전략 요약 비교</h2></div>
    <div class="card"><div class="md">${marked.parse(md)}</div></div>
  `;
}
function buildOverviewMd(c){
  return`### 5개국 전략 요약 비교\n\n| 구분 | ${CO.map(k=>`${CF[k]} ${CN[k]}`).join(' | ')} |\n|------|${CO.map(()=>'------').join('|')}|\n| **전략 유형** | ${CO.map(k=>c[k].strategy_type).join(' | ')} |\n| **핵심 문제** | ${CO.map(k=>c[k].core_problem).join(' | ')} |\n| **접근 방식** | ${CO.map(k=>c[k].key_approach).join(' | ')} |\n| **추진 기관** | ${CO.map(k=>c[k].lead_agency).join(' | ')} |`;
}

/* ===== TAB 3: 비교 분석 ===== */
function renderComparison(){
  const el=document.getElementById('tab-comparison');
  el.innerHTML=`
    <div class="stitle"><h2>비교 항목 선택</h2><p>항목을 선택하면 5개국 비교 분석을 카드와 표로 확인할 수 있습니다.</p></div>
    <div class="chips" id="chips"></div>
    <div id="compResult"></div>
  `;
  const chips=document.getElementById('chips');
  chips.innerHTML=D.dims.map(d=>`<button class="chip" data-d="${d.code}">${d.label}</button>`).join('');
  chips.querySelectorAll('.chip').forEach(c=>{
    c.addEventListener('click',()=>{
      chips.querySelectorAll('.chip').forEach(x=>x.classList.remove('active'));
      c.classList.add('active');
      showComp(c.dataset.d);
    });
  });
  if(D.dims.length){chips.querySelector('.chip').classList.add('active');showComp(D.dims[0].code)}
}
function showComp(dim){
  const comp=D.comps[dim]; if(!comp)return;
  const md=`### ${comp.label} — 5개국 비교\n\n| 국가 | 핵심 요약 | 상세 분석 |\n|------|----------|----------|\n${CO.map(k=>`| **${CF[k]} ${CN[k]}** | ${comp.data[k].summary} | ${comp.data[k].detail} |`).join('\n')}`;
  document.getElementById('compResult').innerHTML=`
    <div class="stitle"><h3>${comp.label}</h3><p>${comp.description}</p></div>
    <div class="grid g5" style="margin-bottom:1.2rem">${CO.map(k=>{const d=comp.data[k];return`
      <div class="compc" data-c="${k}">
        <div class="cco">${CF[k]} ${CN[k]}</div>
        <div class="ccs">${d.summary}</div>
        <div class="ccd">${d.detail}</div>
      </div>`;}).join('')}</div>
    <div class="card"><div class="md">${marked.parse(md)}</div></div>
  `;
}

/* ===== TAB 4: 실행 전략 ===== */
function renderExecution(){
  const ex=D.exec; if(!ex)return;
  const priCls=p=>p==='최상'?'top':p==='상'?'high':'mid';
  const renderChallenges=(section)=>section.challenges.map(c=>`
    <div class="excard">
      <div class="exname">${c.name}</div>
      <span class="expri ${priCls(c.priority)}">우선순위: ${c.priority}</span>
      <div class="exrow"><b>현재:</b> ${c.current}</div>
      <div class="exrow"><b>실행:</b> ${c.action}</div>
      <div class="exrow"><b>일정:</b> ${c.timeline}</div>
    </div>
  `).join('');

  const gov=ex.governance_models;
  document.getElementById('tab-execution').innerHTML=`
    <div class="stitle"><h2>기술적 과제</h2><p>${ex.technical.title}</p></div>
    <div class="grid g2">${renderChallenges(ex.technical)}</div>

    <div class="stitle mt2"><h2>산업적 과제</h2><p>${ex.industrial.title}</p></div>
    <div class="grid g2">${renderChallenges(ex.industrial)}</div>

    <div class="stitle mt2"><h2>제도적 과제</h2><p>${ex.institutional.title}</p></div>
    <div class="grid g2">${renderChallenges(ex.institutional)}</div>

    <div class="stitle mt2"><h2>거버넌스 모델 비교</h2></div>
    <div class="grid g4">${gov.models.map(m=>`
      <div class="govcard">
        <div class="gm">${m.model}</div>
        <div class="gc">${m.country}</div>
        <div class="gd">${m.description}</div>
        <div class="gp"><b>장점:</b> ${m.pros}</div>
        <div class="gp"><b>단점:</b> ${m.cons}</div>
        <div class="gp"><b>한국 적용:</b> ${m.korea_fit}</div>
      </div>
    `).join('')}</div>
    <div class="banner banner-purple mt2">
      <div class="bl">한국 추천 거버넌스</div>
      <div class="bt">${gov.korea_recommendation}</div>
    </div>
  `;
}

/* ===== TAB 5: 인사이트 ===== */
function renderInsights(){
  const ins=D.insights; if(!ins)return;
  const pest=ins.korea_pest||{};
  const pol=ins.policy_proposals||{};
  const bridge=ins.pest_policy_bridge||{};
  const banner=pest.summaryBanner||{};
  const cards=pest.pestCards||[];
  const mapping=pest.policyMapping||[];

  const urgCls=u=>u==='즉시'?'imm':u.includes('1')&&!u.includes('2')?'y1':'y2';

  document.getElementById('tab-insights').innerHTML=`
    ${banner.text?`<div class="banner banner-purple">
      <div class="bl">${banner.title||'한국의 현재 위치'}</div>
      <div class="bt">${banner.text}</div>
    </div>`:''}

    <div class="stitle">
      <h2>${pest.sectionTitle||'한국 AI for Science PEST 진단'}</h2>
      <p>${pest.sectionDescription||''}</p>
    </div>

    ${cards.length?`<div class="pest-grid">${cards.map(c=>`
      <div class="pest-card" style="border-top-color:${c.color}">
        <div class="pest-header">
          <div class="pest-axis" style="background:${c.color}">${c.axis}</div>
          <div class="pest-title">${c.title}</div>
        </div>
        <div class="pest-section">
          <div class="pest-label state">현재 상태</div>
          <ul>${c.currentState.map(s=>`<li>${s}</li>`).join('')}</ul>
        </div>
        <div class="pest-section">
          <div class="pest-label bottleneck">핵심 문제 / 병목</div>
          <ul>${c.bottlenecks.map(b=>`<li>${b}</li>`).join('')}</ul>
        </div>
        <div class="pest-section">
          <div class="pest-label implication">시사점</div>
          <ul>${c.implications.map(i=>`<li>${i}</li>`).join('')}</ul>
        </div>
      </div>
    `).join('')}</div>`:''}

    ${bridge.description?`
    <div class="stitle"><h2>${bridge.title||'PEST 진단과 정책 제안의 연결'}</h2>
      <p>${bridge.description}</p>
    </div>`:''}

    ${mapping.length?`
    <div class="card" style="margin-bottom:2rem">
      <table class="map-table">
        <thead><tr><th>정책 제안</th><th>주 대응 축</th><th>보조 연계 축</th><th>해결 대상 병목</th></tr></thead>
        <tbody>${mapping.map(m=>`
          <tr>
            <td style="font-weight:600">${m.policy}</td>
            <td><span class="axis-tag axis-${m.primaryAxis}">${m.primaryAxis}</span></td>
            <td><span class="axis-tag axis-${m.secondaryAxis}">${m.secondaryAxis}</span></td>
            <td style="font-size:.82rem;color:var(--sub)">${m.targetBottleneck}</td>
          </tr>
        `).join('')}</tbody>
      </table>
    </div>`:''}

    ${pol.proposals?`
    <div class="stitle"><h2>정책 제안</h2></div>
    <div class="grid g1" style="gap:1rem">${pol.proposals.map(p=>`
      <div class="polcard">
        <span class="pnum">${String(p.id).padStart(2,'0')}</span>
        <div class="ptitle">${p.title}</div>
        <span class="purg ${urgCls(p.urgency)}">${p.urgency} · ${p.category}</span>
        <div class="pd">${p.detail}</div>
        <div class="pi"><b>기대효과:</b> ${p.expected_impact}</div>
      </div>
    `).join('')}</div>`:''}

    ${D.extRes&&D.extRes.length?`
    <div class="stitle mt2"><h2>글로벌 정책 참고</h2><p>추가적인 국가별 AI 정책 현황과 데이터는 아래 글로벌 정책 플랫폼에서 확인할 수 있습니다.</p></div>
    <div class="grid g2">${D.extRes.map(r=>`
      <div class="refc ext-card">
        <div class="rt"><a href="${r.url}" target="_blank" rel="noopener">${r.name}</a> <span class="rb ext-badge">외부 ↗</span></div>
        <div class="rd" style="font-size:.86rem;color:var(--sub);margin:6px 0">${r.description}</div>
        <a href="${r.url}" target="_blank" rel="noopener" class="rlb">바로가기 &rarr;</a>
      </div>
    `).join('')}</div>`:''}
  `;
}

/* ===== TAB 6: 데이터 & 출처 ===== */
function renderReferences(country){
  const refs=country==='all'?D.refs:D.refs.filter(r=>r.country===country);
  const el=document.getElementById('tab-references');
  if(!el.querySelector('.chips')){
    const extHtml=D.extRes&&D.extRes.length?`
      <div class="ext-resources">
        <div class="stitle"><h2>글로벌 정책 참고 서비스</h2><p>국가 AI 전략 비교의 보조 참고자료로 활용할 수 있는 글로벌 정책 데이터 플랫폼입니다.</p></div>
        <div class="grid g2" style="margin-bottom:2rem">${D.extRes.map(r=>`
          <div class="refc ext-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:5px">
              <div class="rt"><a href="${r.url}" target="_blank" rel="noopener">${r.name}</a></div>
              <span class="rb ext-badge">외부 서비스 ↗</span>
            </div>
            <div class="rm">${r.category}</div>
            <div class="rd" style="font-size:.86rem;color:var(--sub);margin:8px 0">${r.description}</div>
            <a href="${r.url}" target="_blank" rel="noopener" class="rlb">바로가기 &rarr;</a>
          </div>
        `).join('')}</div>
      </div>`:'';
    el.innerHTML=`
      ${extHtml}
      <div class="stitle"><h2>데이터 & 출처</h2><p>각 국가 전략의 근거 문서와 원문 링크를 제공합니다.</p></div>
      <div class="chips" id="refChips">
        <button class="chip active" data-c="all">전체</button>
        <button class="chip" data-c="korea">한국</button>
        <button class="chip" data-c="japan">일본</button>
        <button class="chip" data-c="china">중국</button>
        <button class="chip" data-c="usa">미국</button>
        <button class="chip" data-c="eu">EU</button>
      </div>
      <div id="refGrid" class="grid g2"></div>
    `;
    document.getElementById('refChips').querySelectorAll('.chip').forEach(c=>{
      c.addEventListener('click',()=>{
        document.getElementById('refChips').querySelectorAll('.chip').forEach(x=>x.classList.remove('active'));
        c.classList.add('active');
        fillRefs(c.dataset.c);
      });
    });
  }
  fillRefs(country);
}
function fillRefs(country){
  const refs=country==='all'?D.refs:D.refs.filter(r=>r.country===country);
  document.getElementById('refGrid').innerHTML=refs.map(r=>{
    const primaryBadge=r.isPrimary?'<span class="rb primary-badge">현행 대표 정책 문서</span>':'';
    const countryName=CN[r.country]||r.country;
    return`
    <div class="refc${r.isPrimary?' primary-doc':''}" data-c="${r.country}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:5px">
        <div class="rt"><a href="${r.url}" target="_blank" rel="noopener">${r.title}</a></div>
        <span class="rb" data-c="${r.country}">${countryName}</span>
      </div>
      ${primaryBadge}
      <div class="rm">${r.source} · ${r.year}년${r.status==='active'?' · <strong>현행</strong>':''}</div>
      <div class="rs">${refSum(r.summary)}</div>
      <a href="${r.url}" target="_blank" rel="noopener" class="rlb">원문 보기 &rarr;</a>
    </div>`;
  }).join('');
}
function refSum(s){
  if(!s)return'';
  return`
    <div class="rss"><div class="rsl">배경</div><div class="rst">${s.background}</div></div>
    <div class="rss"><div class="rsl">핵심 내용</div><div class="rst">${s.key_content}</div></div>
    <div class="rss"><div class="rsl">주요 추진 과제</div><ul class="rsul">${s.main_measures.map(m=>`<li>${m}</li>`).join('')}</ul></div>
    <div class="rss"><div class="rsl">의의</div><div class="rst">${s.significance}</div></div>
  `;
}
