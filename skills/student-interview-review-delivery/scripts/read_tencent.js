/* Run in an authorized background Tencent Meeting page; never exports cookies. */
async function readTencentTranscript({detailUrl, recordId, fetchImpl = globalThis.fetch, maxPages = 30}) {
  const template = new URL(detailUrl);
  if (template.protocol !== 'https:' || template.hostname !== 'meeting.tencent.com' ||
      !template.pathname.endsWith('/minutes/detail') || !recordId ||
      template.searchParams.get('id') !== recordId ||
      !template.searchParams.get('recording_id') || !template.searchParams.get('meeting_id')) {
    throw Error('Target must match an observed Tencent minutes/detail request');
  }
  const paragraphs = new Map(); let cursor = null;
  for (let page = 1; page <= maxPages; page++) {
    const url = new URL(template);
    url.searchParams.set('limit', '500');
    if (cursor === null) { url.searchParams.set('start_pid', '0'); url.searchParams.delete('pid'); }
    else { url.searchParams.delete('start_pid'); url.searchParams.set('pid', cursor); url.searchParams.set('fview', '0'); }
    const response = await fetchImpl(url.toString(), {credentials: 'include', signal: AbortSignal.timeout(30000)});
    if (!response.ok) throw Error('Transcript HTTP request failed');
    const data = await response.json();
    if (data.code !== 0) throw Error('Transcript source denied, unavailable or schema changed: ' + data.code);
    const batch = data.minutes?.paragraphs;
    if (!Array.isArray(batch) || typeof data.more !== 'boolean') throw Error('Transcript pagination schema changed');
    for (const item of batch) {
      if (!Number.isSafeInteger(Number(item.pid)) || item.pid === null || item.pid === '') throw Error('Missing paragraph ID');
      const key = String(item.pid);
      if (paragraphs.has(key) && JSON.stringify(paragraphs.get(key)) !== JSON.stringify(item)) throw Error('Conflicting paragraph versions');
      paragraphs.set(key, item);
    }
    if (!data.more) {
      const turns = [...paragraphs.values()].sort((a,b) => Number(a.pid)-Number(b.pid)).map(p => {
        if (!Array.isArray(p.sentences) || p.sentences.some(s => !Array.isArray(s.words))) throw Error('Transcript text schema changed');
        return {pid:p.pid, timestamp_ms:p.start_time ?? null, speaker:p.speaker?.user_name || '未知发言人',
          text:p.sentences.flatMap(s=>s.words).map(w=>w.text ?? '').join('')};
      }).filter(p=>p.text.trim());
      if (!turns.length) throw Error('Empty transcript');
      return {source:'tencent', record_id:recordId, transport_complete:true, page_count:page, turns};
    }
    const next = batch.at(-1)?.pid;
    if (next === undefined || String(next) === cursor) throw Error('Transcript cursor made no progress');
    cursor = String(next);
  }
  throw Error('Transcript pagination exceeded limit; partial text is not complete');
}
if (typeof module !== 'undefined') module.exports = {readTencentTranscript};
