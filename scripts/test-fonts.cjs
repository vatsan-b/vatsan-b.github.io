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

test('loads a real Newsreader italic face for publication metadata', () => {
  assert.match(css, /family=Newsreader:ital,opsz,wght@0,6\.\.72,200\.\.800;1,6\.\.72,200\.\.800/);
  assert.match(css, /p em, figcaption em\s*\{[\s\S]*font-style:\s*italic;[\s\S]*font-weight:\s*400;/);
  assert.match(css, /\.publication-authors\s*\{\s*font-weight:\s*200;/);
});
