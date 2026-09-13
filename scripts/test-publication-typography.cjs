const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');

test('publication titles are regular while venues use italic emphasis', () => {
  const parser = fs.readFileSync(path.join(root, 'scripts/bib-to-quarto-parser.py'), 'utf8');
  assert.match(parser, /\.publication-authors/);

  const output = fs.readFileSync(path.join(root, 'publications-parsed.qmd'), 'utf8');
  assert.match(output, /Torsion Resistant Strain Limiting Layers Enable High Grip Strength of Electrically-Driven Handed Shearing Auxetic Grippers\\\n/);
  assert.doesNotMatch(output, /\*Torsion Resistant Strain Limiting Layers Enable High Grip Strength of Electrically-Driven Handed Shearing Auxetic Grippers\*/);
  assert.match(output, /Good, I\.\\\*, Balaji, S\.\\\*, Miske, J\. N\., Lipton, J\. I\. • \*Co-first Authors\*/);
  assert.match(output, /\[Good, I\.\\\*, Balaji, S\.\\\*, Miske, J\. N\., Lipton, J\. I\. • \*Co-first Authors\*\]\{\.publication-authors\}/);
});
