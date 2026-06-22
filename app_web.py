import os
import json
from flask import Flask, Response, request, stream_with_context
from dotenv import load_dotenv

load_dotenv()

from database.db import init_db

app = Flask(__name__)
init_db()

HTML_HOME = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VerdictOS — AI Courtroom</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0D0D0D; color: #FFFFFF; font-family: 'Courier New', monospace; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem; }
  .container { width: 100%; max-width: 720px; }
  .header { text-align: center; margin-bottom: 2rem; }
  .title { font-size: 2.8rem; font-weight: bold; color: #E94560; letter-spacing: 0.1em; }
  .subtitle { color: #00D4FF; font-size: 0.85rem; letter-spacing: 0.3em; margin-top: 0.4rem; }
  .box { border: 2px solid #E94560; padding: 2rem; margin-bottom: 1.5rem; }
  label { color: #F5A623; font-size: 0.85rem; letter-spacing: 0.15em; display: block; margin-bottom: 0.5rem; }
  input[type=text] { width: 100%; background: #1a1a1a; border: 1px solid #444; color: #fff; font-family: 'Courier New', monospace; font-size: 1rem; padding: 0.7rem 1rem; outline: none; }
  input[type=text]:focus { border-color: #E94560; }
  .btn-row { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1rem; }
  button { font-family: 'Courier New', monospace; font-size: 0.85rem; font-weight: bold; letter-spacing: 0.1em; border: none; cursor: pointer; padding: 0.6rem 1.2rem; }
  .btn-primary { background: #E94560; color: #fff; }
  .btn-demo { background: #F5A623; color: #000; }
  .btn-primary:hover { background: #c73350; }
  .btn-demo:hover { background: #d48d1a; }
  .tag-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 1.5rem; justify-content: center; }
  .tag { border: 1px solid #333; padding: 0.25rem 0.75rem; font-size: 0.75rem; color: #888; letter-spacing: 0.1em; }
  .divider { border: none; border-top: 1px solid #222; margin: 1.5rem 0; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="title">VERDICTOS</div>
    <div class="subtitle">GENERATE &middot; INVESTIGATE &middot; ARGUE &middot; DECIDE</div>
  </div>
  <div class="box">
    <form method="POST" action="/trial">
      <label>DESCRIBE YOUR DISPUTE</label>
      <input type="text" name="dispute" placeholder="e.g. My roommate stole my biryani from the hostel fridge" autofocus>
      <div class="btn-row">
        <button type="submit" class="btn-primary">&#9632; FILE CASE</button>
      </div>
    </form>
    <hr class="divider">
    <label>DEMO CASES</label>
    <div class="btn-row">
      <form method="POST" action="/demo/biryani"><button type="submit" class="btn-demo">BIRYANI THEFT</button></form>
      <form method="POST" action="/demo/spiderman"><button type="submit" class="btn-demo">SPIDERMAN COLLECTIBLE</button></form>
      <form method="POST" action="/demo/attendance"><button type="submit" class="btn-demo">PROXY ATTENDANCE</button></form>
      <form method="POST" action="/demo/textbook"><button type="submit" class="btn-demo">DAMAGED TEXTBOOK</button></form>
    </div>
  </div>
  <div class="tag-row">
    <span class="tag">Python 3.11</span>
    <span class="tag">Gemini 1.5-flash</span>
    <span class="tag">SWI-Prolog</span>
    <span class="tag">Firebase</span>
    <span class="tag">Neuro-Symbolic AI</span>
  </div>
</div>
</body>
</html>"""

TRIAL_SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VerdictOS — Trial in Progress</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0D0D0D; color: #FFFFFF; font-family: 'Courier New', monospace; padding: 1.5rem; }}
  .top-bar {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #E94560; padding-bottom: 0.75rem; margin-bottom: 1.5rem; }}
  .logo {{ color: #E94560; font-weight: bold; font-size: 1.1rem; letter-spacing: 0.1em; }}
  .back {{ color: #888; text-decoration: none; font-size: 0.8rem; }}
  .back:hover {{ color: #E94560; }}
  .layout {{ display: grid; grid-template-columns: 38% 62%; gap: 1rem; height: calc(100vh - 100px); }}
  .panel {{ border: 1px solid #333; padding: 1rem; overflow-y: auto; }}
  .panel-left {{ border-color: #E94560; }}
  .panel-right {{ border-color: #00D4FF; }}
  .panel-title {{ font-size: 0.75rem; letter-spacing: 0.2em; color: #F5A623; font-weight: bold; margin-bottom: 0.75rem; border-bottom: 1px solid #222; padding-bottom: 0.4rem; }}
  .ev-item {{ font-size: 0.8rem; color: #ccc; margin-bottom: 0.5rem; padding-left: 0.5rem; border-left: 2px solid #F5A623; }}
  .ev-type {{ font-size: 0.7rem; color: #888; }}
  .wit-item {{ font-size: 0.8rem; margin-bottom: 0.75rem; }}
  .wit-name {{ color: #E94560; font-weight: bold; }}
  .wit-alibi {{ color: #888; font-size: 0.75rem; font-style: italic; }}
  .log-line {{ font-size: 0.82rem; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }}
  .log-line.system {{ color: #00D4FF; font-weight: bold; }}
  .log-line.prosecution {{ color: #E94560; }}
  .log-line.defence {{ color: #4a9eff; }}
  .log-line.contradiction {{ color: #FF4444; font-weight: bold; }}
  .log-line.verdict {{ color: #39FF14; font-size: 1rem; font-weight: bold; }}
  .log-line.dim {{ color: #555; }}
  .log-line.witness {{ color: #F5A623; font-weight: bold; }}
  .log-line.qa {{ color: #ccc; padding-left: 1rem; }}
  .status {{ font-size: 0.75rem; color: #39FF14; border-top: 1px solid #222; padding-top: 0.5rem; margin-top: 0.5rem; }}
  .cursor {{ display: inline-block; width: 8px; height: 14px; background: #39FF14; animation: blink 1s step-end infinite; vertical-align: middle; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  #verdict-banner {{ display: none; margin-top: 1rem; border: 2px solid #E94560; padding: 1.5rem; text-align: center; }}
  #verdict-banner .v-title {{ color: #E94560; font-size: 0.8rem; letter-spacing: 0.3em; margin-bottom: 0.5rem; }}
  #verdict-banner .v-case {{ color: #00D4FF; font-size: 0.9rem; margin-bottom: 1rem; }}
  #verdict-banner .v-result {{ font-size: 1.8rem; font-weight: bold; margin-bottom: 1rem; }}
  #verdict-banner .v-contradictions {{ color: #F5A623; font-size: 0.8rem; text-align: left; margin-bottom: 1rem; }}
  #verdict-banner .v-firebase {{ color: #555; font-size: 0.75rem; }}
  .btn-new {{ background: #E94560; color: #fff; border: none; font-family: 'Courier New', monospace; font-size: 0.85rem; font-weight: bold; padding: 0.6rem 1.5rem; cursor: pointer; margin-top: 1rem; letter-spacing: 0.1em; }}
</style>
</head>
<body>
<div class="top-bar">
  <span class="logo">&#9632; VERDICTOS — TRIAL IN PROGRESS</span>
  <a href="/" class="back">&#8592; NEW CASE</a>
</div>
<div class="layout">
  <div class="panel panel-left">
    <div class="panel-title">EVIDENCE BOARD</div>
    <div id="evidence-list"></div>
    <div class="panel-title" style="margin-top:1rem;">WITNESSES</div>
    <div id="witness-list"></div>
    <div id="verdict-banner">
      <div class="v-title">&#9632; THE COURT HAS REACHED A VERDICT &#9632;</div>
      <div class="v-case" id="v-case"></div>
      <div class="v-result" id="v-result"></div>
      <div class="v-contradictions" id="v-contradictions"></div>
      <div class="v-firebase" id="v-firebase"></div>
      <a href="/"><button class="btn-new">&#9632; NEW CASE</button></a>
    </div>
  </div>
  <div class="panel panel-right">
    <div class="panel-title">TRIAL TRANSCRIPT</div>
    <div id="transcript"></div>
    <div class="status" id="status">Initialising trial pipeline... <span class="cursor"></span></div>
  </div>
</div>
<script>
const transcript = document.getElementById('transcript');
const statusEl = document.getElementById('status');
const evidenceList = document.getElementById('evidence-list');
const witnessList = document.getElementById('witness-list');
const verdictBanner = document.getElementById('verdict-banner');

function appendLog(text, cls) {{
  const div = document.createElement('div');
  div.className = 'log-line ' + (cls || '');
  div.textContent = text;
  transcript.appendChild(div);
  transcript.scrollTop = transcript.scrollHeight;
}}

const es = new EventSource('{stream_url}');

es.addEventListener('log', e => {{
  const d = JSON.parse(e.data);
  appendLog(d.text, d.cls || '');
}});

es.addEventListener('status', e => {{
  statusEl.innerHTML = JSON.parse(e.data).text + ' <span class="cursor"></span>';
}});

es.addEventListener('evidence', e => {{
  const item = JSON.parse(e.data);
  const div = document.createElement('div');
  div.className = 'ev-item';
  div.innerHTML = '<span class="ev-type">[' + item.type + ']</span> ' + item.desc;
  evidenceList.appendChild(div);
}});

es.addEventListener('witness', e => {{
  const item = JSON.parse(e.data);
  const div = document.createElement('div');
  div.className = 'wit-item';
  div.innerHTML = '<div class="wit-name">' + item.name + '</div><div class="wit-alibi">' + item.alibi + '</div>';
  witnessList.appendChild(div);
}});

es.addEventListener('verdict', e => {{
  const d = JSON.parse(e.data);
  const color = d.verdict === 'guilty' ? '#FF4444' : '#39FF14';
  document.getElementById('v-case').textContent = d.title;
  document.getElementById('v-result').textContent = 'VERDICT: ' + d.verdict.toUpperCase().replace('_', ' ');
  document.getElementById('v-result').style.color = color;
  if (d.contradictions && d.contradictions.length) {{
    document.getElementById('v-contradictions').textContent = 'Contradictions: ' + d.contradictions.join(', ');
  }}
  if (d.firebase_id) {{
    document.getElementById('v-firebase').textContent = 'Archived: ' + d.firebase_id;
  }}
  verdictBanner.style.display = 'block';
  statusEl.innerHTML = 'Trial complete.';
  es.close();
}});

es.addEventListener('error_end', e => {{
  statusEl.innerHTML = 'Error: ' + JSON.parse(e.data).text;
  es.close();
}});
</script>
</body>
</html>"""


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def stream_trial(dispute: str, demo_key: str | None):
    import services.trial_runner as runner
    from database.db import save_case, save_witnesses, save_evidence

    def generate():
        try:
            if demo_key:
                demo = runner.load_demo(demo_key)
                dispute_text = demo['dispute_text']

                yield sse('status', {'text': 'Loading demo case...'})
                yield sse('log', {'text': f"━━━ {demo['title'].upper()} ━━━", 'cls': 'system'})
                yield sse('log', {'text': f"Setting: {demo.get('setting', '')}"})
                yield sse('log', {'text': f"Defendant: {demo.get('defendant', '')}", 'cls': 'prosecution'})
                yield sse('log', {'text': f"Plaintiff: {demo.get('plaintiff', '')}"})

                evidence_list = demo.get('pre_generated_evidence', [])
                witnesses = demo.get('pre_generated_witnesses', [])

                yield sse('log', {'text': '\n━━━ EVIDENCE BOARD ━━━', 'cls': 'system'})
                for e in evidence_list:
                    yield sse('log', {'text': f"  ■ [{e.get('evidence_type','?')}] {e.get('description','')}"})
                    yield sse('evidence', {'type': e.get('evidence_type', '?'), 'desc': e.get('description', '')})

                yield sse('log', {'text': '\n━━━ WITNESSES ━━━', 'cls': 'system'})
                for w in witnesses:
                    yield sse('log', {'text': f"  ■ {w.get('name','')} — {w.get('occupation','')}", 'cls': 'witness'})
                    yield sse('log', {'text': f"    Alibi: {w.get('alibi_claim','')}", 'cls': 'dim'})
                    yield sse('witness', {'name': w.get('name', ''), 'alibi': w.get('alibi_claim', '')})

                yield sse('log', {'text': '\n━━━ OPENING ARGUMENTS ━━━', 'cls': 'system'})
                yield sse('log', {'text': 'PROSECUTION: The evidence is irrefutable. Motive, opportunity, and physical proof place the defendant at the scene.', 'cls': 'prosecution'})
                yield sse('log', {'text': 'DEFENCE: The prosecution relies on circumstantial evidence. Reasonable doubt has not been eliminated.', 'cls': 'defence'})

                yield sse('log', {'text': '\n━━━ CROSS-EXAMINATION ━━━', 'cls': 'system'})
                for w in witnesses:
                    yield sse('log', {'text': f"\nWitness: {w.get('name','')}", 'cls': 'witness'})
                    yield sse('log', {'text': f"  PROSECUTION: Where were you at the time of the incident?", 'cls': 'prosecution'})
                    yield sse('log', {'text': f"  {w.get('alibi_claim','')}", 'cls': 'qa'})
                    yield sse('log', {'text': '  PROSECUTION: Our records directly contradict that statement.', 'cls': 'prosecution'})
                    yield sse('log', {'text': '  ⚠ WITNESS FALTERS UNDER QUESTIONING', 'cls': 'contradiction'})

                yield sse('status', {'text': 'Running Prolog verdict engine...'})
                yield sse('log', {'text': '\n━━━ PROLOG VERDICT ENGINE ━━━', 'cls': 'system'})

                prolog_result = runner.step_run_prolog(evidence_list, witnesses, demo.get('defendant', 'defendant'))
                if prolog_result.get('error'):
                    pre = demo.get('pre_generated_verdict', {})
                    prolog_result = {'verdict': pre.get('verdict', 'guilty'), 'contradictions': pre.get('contradictions', [])}

                for c in prolog_result.get('contradictions', []):
                    yield sse('log', {'text': f"  CONTRADICTION DETECTED: {c}", 'cls': 'contradiction'})

                case_id = save_case(dispute_text, demo)
                save_evidence(case_id, evidence_list)
                save_witnesses(case_id, witnesses)
                firebase_id = runner.step_archive(case_id, demo['title'], prolog_result, [])

                verdict = prolog_result['verdict'].upper().replace('_', ' ')
                yield sse('log', {'text': f"\n━━━ VERDICT: {verdict} ━━━", 'cls': 'verdict'})
                yield sse('verdict', {
                    'title': demo['title'],
                    'verdict': prolog_result['verdict'],
                    'contradictions': prolog_result.get('contradictions', []),
                    'firebase_id': firebase_id or '',
                })
                return

            yield sse('status', {'text': 'Step 1/6 · Generating case...'})
            yield sse('log', {'text': '━━━ CASE GENERATION ━━━', 'cls': 'system'})
            case_data = runner.step_generate_case(dispute)
            case_id = save_case(dispute, case_data)
            yield sse('log', {'text': f"CASE: {case_data.get('title', '')}"})
            yield sse('log', {'text': f"Setting: {case_data.get('setting', '')}"})
            yield sse('log', {'text': f"Defendant: {case_data.get('defendant', '')}", 'cls': 'prosecution'})
            yield sse('log', {'text': f"Plaintiff: {case_data.get('plaintiff', '')}"})

            yield sse('status', {'text': 'Step 2/6 · Extracting evidence...'})
            yield sse('log', {'text': '\n━━━ EVIDENCE EXTRACTION ━━━', 'cls': 'system'})
            evidence_data = runner.step_generate_evidence(case_data)
            evidence_list = evidence_data.get('evidence_list', [])
            save_evidence(case_id, evidence_list)
            for e in evidence_list:
                yield sse('log', {'text': f"  ■ [{e.get('evidence_type','?')}] {e.get('description','')}"})
                yield sse('evidence', {'type': e.get('evidence_type', '?'), 'desc': e.get('description', '')})

            yield sse('status', {'text': 'Step 3/6 · Generating witnesses...'})
            yield sse('log', {'text': '\n━━━ WITNESS GENERATION ━━━', 'cls': 'system'})
            witnesses = runner.step_generate_witnesses(case_data)
            save_witnesses(case_id, witnesses)
            for w in witnesses:
                yield sse('log', {'text': f"  ■ {w.get('name','')} — {w.get('occupation','')}", 'cls': 'witness'})
                yield sse('log', {'text': f"    Alibi: {w.get('alibi_claim','')}", 'cls': 'dim'})
                yield sse('witness', {'name': w.get('name', ''), 'alibi': w.get('alibi_claim', '')})

            yield sse('status', {'text': 'Step 4/6 · Lawyer arguments...'})
            yield sse('log', {'text': '\n━━━ OPENING ARGUMENTS ━━━', 'cls': 'system'})
            args = runner.step_generate_args(case_data, evidence_list)
            yield sse('log', {'text': f"PROSECUTION: {args.get('prosecution','')}", 'cls': 'prosecution'})
            yield sse('log', {'text': f"DEFENCE: {args.get('defence','')}", 'cls': 'defence'})

            yield sse('status', {'text': 'Step 5/6 · Cross-examination...'})
            yield sse('log', {'text': '\n━━━ CROSS-EXAMINATION ━━━', 'cls': 'system'})
            cross_exams = []
            for witness in witnesses:
                yield sse('log', {'text': f"\nWitness: {witness.get('name','')}", 'cls': 'witness'})
                cx = runner.step_cross_examine(witness, case_data)
                cross_exams.append(cx)
                for qa in cx:
                    q = qa.get('questioner', 'Q')
                    cls = 'prosecution' if q == 'PROSECUTION' else 'defence'
                    yield sse('log', {'text': f"  {q}: {qa.get('question','')}", 'cls': cls})
                    prefix = '  ⚠ CONTRADICTION  ' if qa.get('contradiction') else '  '
                    c = 'contradiction' if qa.get('contradiction') else 'qa'
                    yield sse('log', {'text': f"{prefix}{qa.get('answer','')}", 'cls': c})

            yield sse('status', {'text': 'Step 6/6 · Running Prolog verdict engine...'})
            yield sse('log', {'text': '\n━━━ PROLOG VERDICT ENGINE ━━━', 'cls': 'system'})
            prolog_result = runner.step_run_prolog(evidence_list, witnesses, case_data.get('defendant', 'defendant'))
            for c in prolog_result.get('contradictions', []):
                yield sse('log', {'text': f"  CONTRADICTION DETECTED: {c}", 'cls': 'contradiction'})
            if prolog_result.get('error'):
                yield sse('log', {'text': f"  (Prolog note: {prolog_result['error']})", 'cls': 'dim'})

            firebase_id = runner.step_archive(case_id, case_data.get('title', ''), prolog_result, cross_exams)

            verdict = prolog_result['verdict'].upper().replace('_', ' ')
            yield sse('log', {'text': f"\n━━━ VERDICT: {verdict} ━━━", 'cls': 'verdict'})
            yield sse('verdict', {
                'title': case_data.get('title', ''),
                'verdict': prolog_result['verdict'],
                'contradictions': prolog_result.get('contradictions', []),
                'firebase_id': firebase_id or '',
            })

        except Exception as exc:
            yield sse('log', {'text': f"ERROR: {exc}", 'cls': 'contradiction'})
            yield sse('error_end', {'text': str(exc)})

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        },
    )


@app.route('/')
def home():
    return HTML_HOME


@app.route('/trial', methods=['POST'])
def trial_page():
    dispute = request.form.get('dispute', '').strip()
    if not dispute:
        return home()
    stream_url = f'/stream?dispute={dispute}'
    return TRIAL_SHELL.format(stream_url=stream_url)


@app.route('/demo/<key>', methods=['POST'])
def demo_page(key: str):
    stream_url = f'/stream/demo/{key}'
    return TRIAL_SHELL.format(stream_url=stream_url)


@app.route('/stream')
def stream_custom():
    dispute = request.args.get('dispute', '')
    return stream_trial(dispute, None)


@app.route('/stream/demo/<key>')
def stream_demo(key: str):
    return stream_trial('', key)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
