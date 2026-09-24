// SPDX-License-Identifier: GPL-3.0-or-later
// Static source contracts and reference mathematics only: these are NOT browser,
// WebGL shader execution, pixel rendering, accessibility or network-capture tests.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const read = name => readFileSync(new URL(`../web/${name}`, import.meta.url), 'utf8');
const viewer = read('viewer.js');
const app = read('app.js');
const html = read('index.html');
const vertex = viewer.match(/const vs=`([^`]+)`;/)?.[1];
const fragment = viewer.match(/const fs=`([^`]+)`;/)?.[1];
const compact = value => value.replace(/\s+/g, '');

test('visible tool name is JR Delipack ModelKit in title and heading', () => {
  assert.match(html, /<title>JR Delipack ModelKit(?:\s|<)/);
  assert.match(html, /<h1>JR Delipack ModelKit<\/h1>/);
});

test('CSP disallows outbound connections and limits executable resources to self', () => {
  const policy = html.match(/http-equiv="Content-Security-Policy"\s+content="([^"]+)"/)?.[1];
  assert.ok(policy, 'A declared CSP is required');
  const directives = new Map(policy.split(';').map(value => value.trim().split(/\s+/))
    .filter(parts => parts[0]).map(([name, ...values]) => [name, values]));
  for (const name of ['default-src', 'connect-src', 'object-src', 'base-uri', 'form-action']) {
    assert.deepEqual(directives.get(name), ["'none'"]);
  }
  assert.deepEqual(directives.get('script-src'), ["'self'"]);
  assert.deepEqual(directives.get('style-src'), ["'self'"]);
  assert.deepEqual(directives.get('img-src'), ['blob:', 'data:']);
});

test('positive pitch projects the bowl top nearer; negative pitch reveals the bottom', () => {
  assert.ok(vertex, 'Vertex shader source must be present');
  assert.ok(compact(vertex).includes('gl_Position=vec4(v.x/aspect,v.z,v.y*0.2,1.0);'));
  assert.ok(compact(vertex).includes('d*(b*q.x+a*q.y)-e*q.z'));
  assert.match(html, /id="pitch"[^>]*value="55"/);
  assert.match(viewer, /\$\('pitch'\)\.value=55/);
  // At x=y=0, rotated view-Y is -sin(pitch)*world-Z. With WebGL LESS,
  // smaller NDC Z wins: positive pitch must bring world +Z towards the viewer.
  const depth = (worldZ, pitchDegrees) => -Math.sin(pitchDegrees * Math.PI / 180) * worldZ * 0.2;
  assert.ok(depth(1, 55) < depth(0, 55));
  assert.ok(depth(1, -55) > depth(0, -55));
  assert.equal(depth(1, 0), depth(0, 0));
  assert.match(viewer, /gl\.enable\(gl\.DEPTH_TEST\)/);
});

test('display shader contains the linear-RGB to sRGB piecewise transfer', () => {
  assert.ok(fragment, 'Fragment shader source must be present');
  const source = compact(fragment);
  assert.ok(source.includes('vec3linearColor=max(color*light,vec3(0.0));'));
  assert.ok(source.includes('mix(12.92*linearColor,1.055*pow(linearColor,vec3(1.0/2.4))-0.055,step(vec3(0.0031308),linearColor))'));
  assert.ok(source.includes('gl_FragColor=vec4(displayColor,1.0);'));
});

test('sRGB reference endpoints, threshold and midtone remain numerically correct', () => {
  // Independent reference equation, not execution of the GLSL in a graphics driver.
  const toSrgb = linear => linear < 0.0031308
    ? 12.92 * linear : 1.055 * linear ** (1 / 2.4) - 0.055;
  assert.equal(toSrgb(0), 0);
  assert.ok(Math.abs(toSrgb(1) - 1) < 1e-12);
  assert.ok(Math.abs(toSrgb(0.18) - 0.46135612950044164) < 1e-12);
  const threshold = 0.0031308;
  assert.ok(Math.abs(12.92 * threshold - toSrgb(threshold)) < 3e-8);
  const values = [0, 0.001, threshold, 0.01, 0.18, 0.5, 1].map(toSrgb);
  assert.ok(values.every((value, index) => !index || value > values[index - 1]));
});

test('synthetic drawing labels use a different fill colour than their background', () => {
  const start = app.indexOf("el('synthetic').onclick=()=>{");
  const end = app.indexOf("el('calibrate').onclick", start);
  assert.ok(start >= 0 && end > start);
  const handler = app.slice(start, end);
  const backgroundFill = handler.slice(0, handler.indexOf('c.fillRect('))
    .match(/c\.fillStyle='(#[0-9a-fA-F]{6})'/)?.[1].toLowerCase();
  assert.ok(backgroundFill, 'The synthetic background must set its fill colour');
  const labelPositions = [...handler.matchAll(/c\.fillText\(/g)].map(match => match.index);
  assert.ok(labelPositions.length >= 2, 'Both calibration labels must be retained');
  for (const position of labelPositions) {
    const assignments = [...handler.slice(0, position).matchAll(/c\.fillStyle='(#[0-9a-fA-F]{6})'/g)];
    const labelFill = assignments.at(-1)?.[1].toLowerCase();
    assert.ok(labelFill, 'The label must have an explicit effective fill colour');
    assert.notEqual(labelFill, backgroundFill, 'Label fill must not reuse the background fill');
  }
});

test('viewer rendering is event-driven, visibility guarded and not an animation loop', () => {
  assert.doesNotMatch(viewer, /\b(?:requestAnimationFrame|setInterval|setTimeout)\s*\(/);
  assert.match(viewer, /function render\(\)\{if\(document\.hidden\|\|gl\.isContextLost\(\)\)return/);
  assert.match(viewer, /addEventListener\('input',render\)/);
  assert.match(viewer, /addEventListener\('resize',render\)/);
  assert.match(viewer, /addEventListener\('visibilitychange'/);
  assert.match(viewer, /Math\.min\(window\.devicePixelRatio\|\|1,1\.5\)/);
});

test('local scripts contain no network client and use local image object URLs', () => {
  assert.doesNotMatch(app + viewer, /\bfetch\s*\(|\b(?:XMLHttpRequest|WebSocket|EventSource)\b|\.sendBeacon\s*\(/);
  const scripts = [...html.matchAll(/<script\b[^>]*src="([^"]+)"/g)].map(match => match[1]);
  assert.deepEqual(scripts, ['viewer.js', 'app.js']);
  assert.match(app, /URL\.createObjectURL\(f\)/);
  assert.match(app, /URL\.revokeObjectURL\(currentURL\)/);
  assert.match(app, /img\.src=url/);
  assert.match(app, /Photos are NOT included in exported JSON/);
});

test('numeric and keyboard-oriented fallback controls remain present', () => {
  assert.match(html, /Keyboard-accessible numeric alternative/);
  assert.match(html, /id="height" type="number"/);
  for (const name of ['yaw', 'pitch', 'zoom']) {
    assert.match(html, new RegExp(`id="${name}" type="range"`));
  }
  assert.match(html, /<select id="part">/);
  assert.match(html, /id="viewStatus" role="status" aria-live="polite"/);
  assert.match(viewer, /if\(!gl\).*WebGL unavailable/s);
});

test('image and mesh input budgets and decode failure handling remain bounded', () => {
  assert.match(app, /\['image\/png','image\/jpeg','image\/webp'\]\.includes\(f\.type\)/);
  assert.match(app, /f\.size>10\*1024\*1024/);
  assert.match(app, /img\.naturalWidth\*img\.naturalHeight>20_000_000/);
  assert.match(app, /img\.onerror=.*Cannot decode this image/s);
  assert.match(viewer, /f\.size>20\*1024\*1024/);
  assert.match(viewer, /m\.vertices_mm\.length>65535/);
  assert.match(viewer, /total>150000/);
  assert.match(viewer, /m\.faces\.length>140000/);
});
