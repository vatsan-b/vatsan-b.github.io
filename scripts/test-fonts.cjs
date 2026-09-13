const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const css = fs.readFileSync(path.join(__dirname, '../styles.css'), 'utf8');

test('uses Newsreader as the site body font from Google Fonts', () => {
  assert.match(css, /fonts\.googleapis\.com\/css2\?family=Newsreader:/);
  assert.match(css, /--main-font:\s*"Newsreader", serif;/);
  assert.match(css, /--font-nav:\s*"Newsreader", serif;/);
});
