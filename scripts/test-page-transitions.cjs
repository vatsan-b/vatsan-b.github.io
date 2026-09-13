const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const css = fs.readFileSync(path.join(__dirname, '../styles.css'), 'utf8');

test('uses one compositor-friendly page transition system', () => {
  assert.match(css, /#quarto-content\s*\{[\s\S]*will-change:\s*opacity, transform;/);
  assert.match(css, /@view-transition\s*\{\s*navigation:\s*none;\s*\}/);
  assert.doesNotMatch(css, /@view-transition\s*\{\s*navigation:\s*auto;\s*\}/);
});
