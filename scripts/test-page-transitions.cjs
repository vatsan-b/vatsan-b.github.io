const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const css = fs.readFileSync(path.join(__dirname, '../styles.css'), 'utf8')
  .replace(/\/\*[\s\S]*?\*\//g, '');   // ignore comments

test('uses one compositor-friendly page transition, with no permanent transform', () => {
  assert.match(css, /#quarto-content\s*\{[\s\S]*?animation:\s*pageFade 0\.3s ease-out backwards;/);
  assert.match(css, /@keyframes pageFade\s*\{[\s\S]*?opacity[\s\S]*?transform/);
  assert.doesNotMatch(css, /@view-transition\s*\{\s*navigation:\s*auto;\s*\}/);
  assert.doesNotMatch(css, /\.message\s*\{[^}]*animation/);
});
