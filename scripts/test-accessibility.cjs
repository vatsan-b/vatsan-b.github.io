const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');

test('about portrait has meaningful alternative text', () => {
  const rendered = fs.readFileSync(path.join(root, 'docs/about.html'), 'utf8');
  assert.match(rendered, /<img[^>]+src="assets\/images\/srivatsanb-photo\.jpg"[^>]+alt="Portrait of Srivatsan Balaji"/);
});

test('research figures have descriptive alternative text', () => {
  const research = fs.readFileSync(path.join(root, 'docs/research.html'), 'utf8');
  for (const src of ['bravo-gripper.png', 'parallel-jaw-lowres.png', 'TR-SLL_Lift_Hero.png']) {
    assert.match(research, new RegExp(`<img[^>]+src="assets/images/${src.replace('.', '\\.') }"[^>]+alt="[^"]+"`));
  }
});
