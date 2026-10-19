const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'assets/gallery/gallery.js'), 'utf8');

test('gallery reads captions from the generated manifest, which the generator keeps in sync', () => {
  assert.match(script, /fetchJson\(MANIFEST_URL\)/);
  assert.doesNotMatch(script, /CONTENT_URL/);
  const generator = fs.readFileSync(path.join(root, 'scripts/generate-gallery-derivatives.py'), 'utf8');
  assert.match(generator, /--captions-only/);
  const content = JSON.parse(fs.readFileSync(path.join(root, 'scripts/gallery-content.json'), 'utf8'));
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'assets/gallery-derivatives/manifest.json'), 'utf8'));
  for (const [key, entries] of Object.entries(content.galleries)) {
    const byFile = new Map(manifest.galleries[key].map(i => [i.file, i.caption]));
    for (const e of entries) assert.equal(byFile.get(e.file), e.caption, `caption out of sync for ${e.file}; run generate-gallery-derivatives.py --captions-only`);
  }
});
