// Generates sprites from art/prompts.json with Codex image_gen (ChatGPT subscription), same approach as ~/Developer/reigns/art/gen.js.
// Usage: node art/gen.mjs [slug ...]   (no args: every sprite without a raw image; JOBS=4 in parallel; MAX_USED=95 stops at that % of the 5 h window)
// Raw image -> art/raw/<slug>.png, metadata -> art/images.json, then art/pixelate.py snaps it to sprites/<slug>.png (+ sprites/<slug>@64.png if big).
import {readFileSync, writeFileSync, existsSync, readdirSync, copyFileSync, unlinkSync} from 'fs';
import {homedir} from 'os';
import {execFileSync, spawn} from 'child_process';

const here = new URL('./', import.meta.url).pathname, P = JSON.parse(readFileSync(here + 'prompts.json'));
const META = here + 'images.json', MODEL = process.env.MODEL || 'gpt-5.6-luna', EFFORT = 'low';
const JOBS = +process.env.JOBS || 4, MAX_USED = +process.env.MAX_USED || 95;
const usedPct = () => { try { return JSON.parse(execFileSync('codexbar', ['usage', '--provider', 'codex', '--json'], {encoding: 'utf8'}))[0].usage.primary.usedPercent; } catch { return 0; } };
// stdin closed: otherwise codex exec waits for more input
const out = (cmd, args) => new Promise(ok => {
  const p = spawn(cmd, args, {stdio: ['ignore', 'pipe', 'ignore'], timeout: 600_000});
  let s = ''; p.stdout.on('data', d => s += d); p.on('close', () => ok(s));
});

async function gen(sp) {
  const png = `${here}raw/${sp.slug}.png`;
  if (!existsSync(png)) {
    if (usedPct() >= MAX_USED) return console.log(`· ${sp.slug}: 5 h quota at ${MAX_USED}%, stopped`);
    const prompt = `${sp.subject}\n\n${P.style.replace('{GRID}', sp.big ? '64x64' : '32x32')}\n\nAvoid: ${P.negative}`;
    // Codex saves each image under ~/.codex/generated_images/<thread>/: copy it from this call's thread so parallel calls don't mix
    const tid = (await out('codex', ['exec', '--json', '-m', MODEL, '-c', `model_reasoning_effort=${EFFORT}`, '--skip-git-repo-check', '-s', 'read-only',
      `Call your built-in image_gen tool directly (do not read skill files or run commands). Square 1:1. Do not save or copy the file. Prompt:\n\n${prompt}`]))
      .match(/"thread_id":"([^"]+)"/)?.[1];
    const dir = `${homedir()}/.codex/generated_images/${tid}/`;
    const img = tid && existsSync(dir) && readdirSync(dir).filter(f => f.endsWith('.png')).at(-1);
    if (!img) return console.log(`✗ ${sp.slug}: no image saved`);
    copyFileSync(dir + img, png);
    const meta = existsSync(META) ? JSON.parse(readFileSync(META)) : {};
    meta[sp.slug] = {tool: 'codex image_gen (ChatGPT subscription)', model: MODEL, effort: EFFORT, date: new Date().toISOString().slice(0, 10), prompt};
    writeFileSync(META, JSON.stringify(meta, null, 2) + '\n');
  }
  try { execFileSync('python3', [here + 'pixelate.py', sp.slug, ...(sp.big ? ['--big'] : [])], {stdio: 'inherit'}); }
  catch (e) {
    // wrong background (the model sometimes paints it black): drop the raw image and try again
    if (e.status !== 2 || (sp.tries = (sp.tries || 0) + 1) > 2) return console.log(`✗ ${sp.slug}: gave up`);
    unlinkSync(png); return gen(sp);
  }
}

const want = process.argv.slice(2), queue = P.sprites.filter(s => want.length ? want.includes(s.slug) : !existsSync(`${here}raw/${s.slug}.png`));
await Promise.all(Array.from({length: JOBS}, async () => { while (queue.length) await gen(queue.shift()); }));
