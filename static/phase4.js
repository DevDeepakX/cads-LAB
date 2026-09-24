(() => {
  const json = async (url, options = {}) => {
    options.headers = {...(options.headers || {})};
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes((options.method || 'GET').toUpperCase())) options.headers['X-CSRFToken'] = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Request failed');
    return data;
  };
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  const time = value => value ? new Date(value).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'}) : '--:--:--';
  const toast = message => { const node = document.getElementById('page-toast'); if (!node) return; node.textContent = message; node.classList.add('show'); setTimeout(() => node.classList.remove('show'), 3200); };

  document.getElementById('menu-button')?.addEventListener('click', () => document.getElementById('sidebar')?.classList.toggle('open'));

  async function dashboard() {
    const data = await json('/api/dashboard');
    const current = data.current_lab;
    document.querySelector('[data-metric="progress"]').textContent = `${data.progress.percent}%`;
    document.querySelector('[data-meter="progress"]').style.width = `${data.progress.percent}%`;
    document.querySelector('[data-metric="labs"]').textContent = `${data.progress.completed} / ${data.progress.total}`;
    document.querySelector('[data-metric="xp"]').textContent = data.xp;
    document.querySelector('[data-metric="findings"]').textContent = data.open_findings;
    document.querySelector('[data-metric="events"]').textContent = data.events;
    document.getElementById('catalog-count').textContent = `${data.labs.length} lab${data.labs.length === 1 ? '' : 's'}`;
    document.getElementById('learning-path').innerHTML = data.labs.length ? data.labs.map(lab => `<a class="activity-item" href="/labs/${esc(lab.slug)}"><span><strong>${esc(lab.id)}</strong> ${esc(lab.title)}</span><small>${esc(lab.category)} · ${lab.xp} XP</small></a>`).join('') : '<p class="empty-state">No labs are available.</p>';
    document.getElementById('current-lab-title').textContent = current ? current.title : 'No active lab';
    document.getElementById('current-lab-meta').textContent = current ? `${current.lab_id} · ${current.objectives_passed} of ${current.objectives_total} objectives complete` : 'Start the Public S3 Bucket lab to create a private simulator environment.';
    document.getElementById('current-lab-status').textContent = current?.completed ? 'COMPLETED' : current ? 'IN PROGRESS' : 'NOT STARTED';
    document.getElementById('current-lab-progress').textContent = `${current?.progress || 0}% complete`;
    document.getElementById('current-lab-meter').style.width = `${current?.progress || 0}%`;
    document.getElementById('continue-link').href = current ? `/lab/${encodeURIComponent(current.lab_id)}` : '/labs';
    document.getElementById('continue-link').textContent = current ? 'Continue lab →' : 'Open lab catalog →';
    document.getElementById('recent-activity').innerHTML = data.recent_activity.length ? data.recent_activity.map(event => `<div class="activity-item"><span>${esc(event.service)} · ${esc(event.event_name)}</span><small>${time(event.timestamp)} · ${esc(event.outcome)}</small></div>`).join('') : '<p class="empty-state">No active simulator session.</p>';
  }

  async function progress() {
    const data = await json('/api/progress');
    document.getElementById('overall-percent').textContent = `${data.overall.percent}%`;
    document.getElementById('overall-meter').style.width = `${data.overall.percent}%`;
    document.getElementById('overall-count').textContent = `${data.overall.completed} / ${data.overall.total} labs completed`;
    const entries = Object.entries(data.categories);
    document.getElementById('progress-categories').innerHTML = entries.length ? entries.map(([name, item]) => { const percent = item.total ? Math.round(item.completed / item.total * 100) : 0; return `<article class="category-card"><span class="eyebrow">Learning area</span><h3>${esc(name)}</h3><strong>${item.completed} / ${item.total}</strong><p class="muted">labs completed</p><div class="meter"><i style="width:${percent}%"></i></div></article>`; }).join('') : '<p class="empty-state">No learning areas are available.</p>';
  }

  async function startLab(button) { try { const data = await json(`/api/labs/${encodeURIComponent(button.dataset.startLab)}/start`, {method:'POST'}); window.location.href = `/lab/${encodeURIComponent(data.lab.lab_id)}`; } catch (error) { toast(error.message); } }
  document.querySelector('[data-start-lab]')?.addEventListener('click', event => startLab(event.currentTarget));

  const labId = window.CADS_LAB_ID;
  let activeFinding = null;
  async function workspace() {
    try { await json(`/api/labs/${encodeURIComponent(labId)}/state`); } catch { await json(`/api/labs/${encodeURIComponent(labId)}/start`, {method:'POST'}); }
    await Promise.all([loadProgress(), loadResources(), loadFindings(), loadEvents(), loadTimeline()]);
  }
  async function loadProgress() {
    const data = await json(`/api/labs/${encodeURIComponent(labId)}/progress`);
    document.getElementById('objective-count').textContent = `${data.passed} / ${data.total}`;
    document.getElementById('objective-list').innerHTML = Object.entries(data.objectives).map(([id, objective]) => `<div class="objective-item"><span class="objective-check ${objective.status === 'PASS' ? 'pass' : ''}">${objective.status === 'PASS' ? 'OK' : '○'}</span><div><span>${esc(objective.message)}</span><small class="objective-time">${esc(id)} · ${objective.status}</small></div></div>`).join('');
    document.getElementById('completion-banner').hidden = data.percent < 100;
  }
  async function loadResources() {
    const data = await json(`/api/labs/${encodeURIComponent(labId)}/resources`);
    document.getElementById('resource-list').innerHTML = data.resources.map(resource => `<div class="resource-item" data-resource="${esc(resource.resource_name)}"><span class="resource-type">${esc(resource.resource_type)}</span><span class="resource-name">${esc(resource.resource_name)}</span><span class="resource-meta">${esc(resource.region)} · ${esc(resource.status)}</span></div>`).join('');
    document.querySelectorAll('[data-resource]').forEach(item => item.addEventListener('click', () => {
      const resource = data.resources.find(entry => entry.resource_name === item.dataset.resource);
      const detail = document.getElementById('resource-detail');
      detail.hidden = false;
      let fields = `<dt>Type</dt><dd>${esc(resource.resource_type)}</dd><dt>Region</dt><dd>${esc(resource.region)}</dd>`;
      const cfg = resource.configuration || {};
      if (resource.resource_type === 'S3_BUCKET') {
        fields += `<dt>Public access</dt><dd class="${cfg.public_access ? 'risk-text' : 'safe-text'}">${cfg.public_access ? 'ENABLED' : 'BLOCKED'}</dd><dt>Encryption</dt><dd>${cfg.encryption ? 'ENABLED' : 'DISABLED'}</dd><dt>Logging</dt><dd>${cfg.logging ? 'ENABLED' : 'DISABLED'}</dd>`;
      } else if (resource.resource_type === 'IAM_USER') {
        fields += `<dt>User</dt><dd>${esc(cfg.user_name || resource.resource_name)}</dd><dt>Attached</dt><dd>${esc((cfg.attached_policies || []).join(', ') || 'None')}</dd><dt>Status</dt><dd class="${cfg.escalated || cfg.compromised ? 'risk-text' : 'safe-text'}">${cfg.escalated ? 'ESCALATED' : cfg.compromised ? 'COMPROMISED' : 'LEAST_PRIVILEGE'}</dd>`;
      } else if (resource.resource_type === 'IAM_POLICY') {
        fields += `<dt>Policy ARN</dt><dd>${esc(cfg.policy_arn || '-')}</dd><dt>Status</dt><dd>ACTIVE</dd>`;
      } else if (resource.resource_type === 'SECURITY_GROUP') {
        const rules = (cfg.inbound_rules || []).map(r => `${r.protocol}/${r.port} from ${r.source}`).join(', ');
        const hasOpen = (cfg.inbound_rules || []).some(r => String(r.port) === '22' && r.source === '0.0.0.0/0');
        fields += `<dt>Group ID</dt><dd>${esc(cfg.group_id || '-')}</dd><dt>Inbound</dt><dd class="${hasOpen ? 'risk-text' : 'safe-text'}">${esc(rules)}</dd>`;
      } else if (resource.resource_type === 'EC2_INSTANCE') {
        fields += `<dt>Instance</dt><dd>${esc(cfg.instance_id || resource.resource_name)}</dd><dt>Type</dt><dd>${esc(cfg.instance_type || 't3.medium')}</dd><dt>Public IP</dt><dd>${esc(cfg.public_ip || '-')}</dd>`;
      } else if (resource.resource_type === 'CLOUDTRAIL_TRAIL') {
        fields += `<dt>Trail</dt><dd>${esc(cfg.trail_name || resource.resource_name)}</dd><dt>Logging</dt><dd class="safe-text">${cfg.is_logging ? 'ENABLED' : 'DISABLED'}</dd><dt>Multi-Region</dt><dd>${cfg.is_multi_region ? 'YES' : 'NO'}</dd>`;
      }
      detail.innerHTML = `<p class="eyebrow">Selected resource</p><strong>${esc(resource.resource_name)}</strong><dl>${fields}</dl>`;
    }));
  }
  async function loadFindings() {
    const data = await json(`/api/labs/${encodeURIComponent(labId)}/findings`);
    const open = data.findings.filter(item => item.status !== 'RESOLVED').length;
    document.getElementById('finding-count').textContent = `${open} open`;
    document.getElementById('finding-list').innerHTML = data.findings.length ? data.findings.map(finding => `<article class="finding-item"><h3>${esc(finding.title)}</h3><p>${esc(finding.description)}</p><div class="finding-meta"><span class="severity-high">${esc(finding.severity)}</span><span>${esc(finding.status)} · ${esc(finding.resource_id)}</span></div><button class="finding-button" data-investigate="${esc(finding.finding_id)}">Investigate</button>${finding.status !== 'RESOLVED' ? `<button class="finding-button finding-button-primary" data-remediate="${esc(finding.finding_id)}">Remediate</button>` : ''}</article>`).join('') : '<p class="empty-state">No findings yet. Investigate the environment from the terminal.</p>';
    document.querySelectorAll('[data-investigate]').forEach(button => button.addEventListener('click', () => investigate(button.dataset.investigate)));
    document.querySelectorAll('[data-remediate]').forEach(button => button.addEventListener('click', () => remediate(button.dataset.remediate)));
  }
  async function loadEvents() {
    const query = new URLSearchParams(); const service = document.getElementById('event-service').value; const severity = document.getElementById('event-severity').value; if (service) query.set('service', service); if (severity) query.set('severity', severity);
    const data = await json(`/api/labs/${encodeURIComponent(labId)}/events?${query}`); const services = [...new Set(data.events.map(event => event.service))]; const select = document.getElementById('event-service'); const selected = select.value; select.innerHTML = '<option value="">All services</option>' + services.map(item => `<option>${esc(item)}</option>`).join(''); select.value = selected;
    document.getElementById('event-list').innerHTML = data.events.length ? `<div class="event-row"><span>TIME</span><span>SERVICE</span><span>EVENT</span><span>ACTOR</span><span>OUTCOME</span></div>` + data.events.map(event => `<div class="event-row"><span class="event-time">${time(event.timestamp)}</span><span>${esc(event.service)}</span><span>${esc(event.event_name)}<br><small>${esc(event.resource_name || '-')}</small></span><span>${esc(event.actor)}</span><span class="severity-${esc(event.severity).toLowerCase()}">${esc(event.outcome)}</span></div>`).join('') : '<p class="empty-state">No events match this filter.</p>';
  }
  async function loadTimeline() { const data = await json(`/api/labs/${encodeURIComponent(labId)}/timeline`); document.getElementById('timeline').innerHTML = data.events.length ? data.events.map(event => `<div class="timeline-item"><time>${time(event.timestamp)}</time><strong>${esc(event.service)} · ${esc(event.event_name)}</strong><span>${esc(event.actor)} · ${esc(event.outcome)}${event.resource_name ? ` · ${esc(event.resource_name)}` : ''}</span></div>`).join('') : '<p class="empty-state">Timeline follows the simulator event stream.</p>'; }
  async function investigate(findingId) { try { const data = await json(`/api/labs/${encodeURIComponent(labId)}/findings/${encodeURIComponent(findingId)}/investigate`, {method:'POST'}); activeFinding = data.finding; const detail = document.getElementById('finding-detail'); detail.hidden = false; detail.innerHTML = `<p class="eyebrow">Finding detail</p><h3>${esc(data.finding.title)}</h3><p>${esc(data.finding.description)}</p><dl><dt>Status</dt><dd>${esc(data.finding.status)}</dd><dt>Service</dt><dd>${esc(data.finding.service)}</dd><dt>Resource</dt><dd>${esc(data.finding.resource_id)}</dd><dt>Evidence</dt><dd>${data.finding.evidence.length} records</dd></dl><p class="recommendation">${esc(data.finding.recommendation)}</p>${data.finding.status !== 'RESOLVED' ? `<button class="button button-primary" data-detail-remediate="${esc(findingId)}">Apply remediation</button>` : ''}`; detail.querySelector('[data-detail-remediate]')?.addEventListener('click', () => remediate(findingId)); document.getElementById('investigation').scrollIntoView({behavior:'smooth', block:'start'}); toast(`Investigating ${data.finding.title}`); await loadFindings(); } catch (error) { toast(error.message); } }
  async function remediate(findingId) { try { const data = await json(`/api/labs/${encodeURIComponent(labId)}/findings/${encodeURIComponent(findingId)}/remediate`, {method:'POST'}); toast(`Remediation applied: ${data.event.event_name}`); await Promise.all([loadProgress(), loadResources(), loadFindings(), loadEvents(), loadTimeline()]); if (activeFinding) investigate(findingId); } catch (error) { toast(error.message); } }
  async function runCommand(event) { event.preventDefault(); const input = document.getElementById('command-input'); const command = input.value.trim(); if (!command) return; const output = document.getElementById('terminal-output'); output.insertAdjacentHTML('beforeend', `<div class="terminal-line terminal-command">student@cads:~$ ${esc(command)}</div>`); input.value = ''; try { const result = await json('/api/terminal/command', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({command})}); output.insertAdjacentHTML('beforeend', `<div class="terminal-line ${result.status === 'ok' ? 'terminal-output-line' : 'terminal-error'}">${esc(result.output || result.message || result.status)}</div>`); } catch (error) { output.insertAdjacentHTML('beforeend', `<div class="terminal-line terminal-error">${esc(error.message)}</div>`); } output.scrollTop = output.scrollHeight; await Promise.all([loadProgress(), loadResources(), loadFindings(), loadEvents(), loadTimeline()]); }
  document.getElementById('terminal-form')?.addEventListener('submit', runCommand);
  document.getElementById('clear-terminal')?.addEventListener('click', () => { document.getElementById('terminal-output').innerHTML = '<div class="terminal-line terminal-info">Terminal cleared.</div>'; });
  document.getElementById('event-service')?.addEventListener('change', loadEvents); document.getElementById('event-severity')?.addEventListener('change', loadEvents); document.getElementById('refresh-events')?.addEventListener('click', event => { event.preventDefault(); loadEvents(); });
  document.querySelector('[data-reset-lab]')?.addEventListener('click', async event => { try { await json(`/api/labs/${encodeURIComponent(event.currentTarget.dataset.resetLab)}/reset`, {method:'POST'}); document.getElementById('terminal-output').innerHTML = '<div class="terminal-line terminal-info">Environment reset.</div>'; await workspace(); toast('Lab environment reset'); } catch (error) { toast(error.message); } });
  if (document.getElementById('dashboard-metrics')) dashboard().catch(error => toast(error.message));
  if (document.getElementById('progress-categories')) progress().catch(error => toast(error.message));
  if (labId) workspace().catch(error => toast(error.message));
})();