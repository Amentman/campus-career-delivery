const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
function reader() {
  const p = path.join(__dirname, '../scripts/read_tencent.js');
  assert.ok(fs.existsSync(p), 'missing background Tencent transcript reader');
  return require(p).readTencentTranscript;
}
const url = 'https://meeting.tencent.com/api/minutes/detail?id=synthetic-record&recording_id=synthetic-track&meeting_id=synthetic-meeting&start_pid=0';
function para(pid, text) { return {pid, start_time: 1000*pid, speaker: {user_name: pid===1?'面试官':'学生'}, sentences: [{words: [{text}]}]}; }
test('fetches all pages, deduplicates and preserves speaker/time', async () => {
  const read = reader(); const requests=[];
  const pages=[{code:0,more:true,minutes:{paragraphs:[para(1,'请介绍项目。')]}}, {code:0,more:false,minutes:{paragraphs:[para(1,'请介绍项目。'),para(2,'我做了核对。')]}}];
  const result = await read({detailUrl:url, recordId:'synthetic-record', fetchImpl:async u=>{requests.push(new URL(u));return {ok:true,json:async()=>pages.shift()};}});
  assert.equal(result.transport_complete,true); assert.equal(result.page_count,2);
  assert.deepEqual(result.turns.map(x=>x.pid),[1,2]); assert.equal(result.turns[1].text,'我做了核对。');
  assert.equal(requests[1].searchParams.get('pid'),'1');
  assert.ok(!JSON.stringify(result).includes('detailUrl'));
});
test('rejects stalled cursors, missing terminal state and conflicts', async () => {
  const read=reader();
  for (const pages of [
    [{code:0,more:true,minutes:{paragraphs:[para(1,'问题？')]}},{code:0,more:true,minutes:{paragraphs:[para(1,'问题？')]}}],
    [{code:0,minutes:{paragraphs:[para(1,'问题？')]}}],
    [{code:0,more:true,minutes:{paragraphs:[para(1,'问题？')]}},{code:0,more:false,minutes:{paragraphs:[para(1,'不同文本')]}}]
  ]) await assert.rejects(read({detailUrl:url,recordId:'synthetic-record',fetchImpl:async()=>({ok:true,json:async()=>pages.shift()})}));
});
test('rejects wrong target, permission denial and failed network', async () => {
  const read=reader();
  await assert.rejects(read({detailUrl:url,recordId:'another-record'}));
  await assert.rejects(read({detailUrl:url.replace('meeting.tencent.com','example.org'),recordId:'synthetic-record'}));
  await assert.rejects(read({detailUrl:url,recordId:'synthetic-record',fetchImpl:async()=>({ok:true,json:async()=>({code:403})})}));
  await assert.rejects(read({detailUrl:url,recordId:'synthetic-record',fetchImpl:async()=>{throw Error('network failed');}}));
});
