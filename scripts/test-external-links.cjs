const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(path.join(__dirname, '../research.qmd'), 'utf8');

test('external research links open in a separate tab', () => {
  assert.match(source, /\[Reach Bravo 7\]\(https:\/\/reachrobotics\.com\/products\/reach-bravo\/reach-bravo-7\)\{target="_blank"\}/);
});
