const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'assets/gallery/gallery.js'), 'utf8');

test('gallery takes captions from the editable content source, not the generated manifest', () => {
  assert.match(script, /CONTENT_URL\s*=\s*["']scripts\/gallery-content\.json["']/);
  assert.match(script, /Promise\.all\(\[\s*fetchJson\(MANIFEST_URL\),\s*fetchJson\(CONTENT_URL\)\s*\]\)/s);
  assert.match(script, /captionsByFile\.has\(item\.file\).*item\.caption\s*=\s*captionsByFile\.get\(item\.file\)/s);
  assert.match(fs.readFileSync(path.join(root, '_quarto.yml'), 'utf8'), /- scripts\/gallery-content\.json/);
});
