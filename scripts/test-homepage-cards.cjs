const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const page = fs.readFileSync(path.join(root, 'index.qmd'), 'utf8');

test('homepage has three accessible, reduced-motion-safe image cards', () => {
  assert.equal((page.match(/class="homepage-card"/g) || []).length, 3);
  assert.match(page, /assets\/homepage\/(?:hsa-arm-pull|hsagripper-windex|underwater-test)\.png/);
  assert.equal((page.match(/<picture>/g) || []).length, 3);
  assert.match(page, /assets\/homepage\/(?:hsa-arm-pull|hsagripper-windex|underwater-test)-900\.webp/);
  assert.match(page, /\.homepage-work\s*\{[\s\S]*display:\s*flex;[\s\S]*flex-wrap:\s*wrap;[\s\S]*justify-content:\s*center;/);
  const rendered = fs.readFileSync(path.join(root, 'docs/index.html'), 'utf8');
  assert.match(rendered, /<div class="homepage-work"[^>]*>\s*<a class="homepage-card"/);
  assert.doesNotMatch(rendered, /<div class="homepage-work"[^>]*>\s*<p>/);
  for (const name of ['hsa-arm-pull.png', 'underwater-test.png', 'hsagripper-windex.png']) {
    assert.ok(fs.existsSync(path.join(root, 'assets/homepage', name)), `${name} is missing`);
  }
});
