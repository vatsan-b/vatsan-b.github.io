const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

async function boot(width, reduced = false) {
  const source = fs.readFileSync(path.join(__dirname, '../index.qmd'), 'utf8');
  assert.ok(!source.includes('three.module'), 'Three.js must be removed');
  const script = source.match(/<script>([\s\S]*?)<\/script>/)[1];
  let options;
  const callbacks = { motion: {}, window: {}, document: {} };
  const media = { matches: reduced, addEventListener(type, fn) { callbacks.motion[type] = fn; } };
  const element = {};
  let sourceOptions;
  const container = {
    running: false, draws: 0, resets: 0, resizes: 0,
    pause() { this.running = false; },
    play() { this.running = true; },
    draw() { this.draws++; },
    async refresh() {
      this.options = structuredClone(sourceOptions);
      this.running = this.options.autoPlay;
    },
    async reset(next) { this.resets++; sourceOptions = next; await this.refresh(); },
    canvas: { async windowResize() { container.resizes++; await container.refresh(); } },
  };
  const document = {
    hidden: false, body: { appendChild() {} }, getElementById() { return element; },
    addEventListener(type, fn) { callbacks.document[type] = fn; },
  };
  await vm.runInNewContext(script, {
    document,
    window: { innerWidth: width, innerHeight: 800, matchMedia() { return media; },
      addEventListener(type, fn) { callbacks.window[type] = fn; } },
    setTimeout, clearTimeout,
    loadSlim: async () => {},
    tsParticles: { load: async (config) => { options = sourceOptions = config.options; await container.refresh(); return container; } },
    console,
  });
  return { options, container, media, callbacks, document };
}
async function optionsFor(width, reduced = false) { return (await boot(width, reduced)).options; }

test('registered preference callback resets source options and preserves settings both ways', async () => {
  for (const initiallyReduced of [false, true]) {
    const { container, media, callbacks, options } = await boot(1280, initiallyReduced);
    for (const reduced of [!initiallyReduced, initiallyReduced]) {
      media.matches = reduced;
      await callbacks.motion.change();
      assert.equal(container.options.particles.move.enable, !reduced);
      assert.equal(container.running, !reduced);
      assert.equal(container.options.particles.number.value, options.particles.number.value);
      assert.deepEqual(container.options.particles.color, structuredClone(options.particles.color));
      assert.equal(container.options.particles.move.speed, options.particles.move.speed);
    }
    assert.equal(container.resets, 2);
    assert.equal(container.options.pauseOnOutsideViewport, false);
  }
});

test('mobile has a smaller particle budget', async () => {
  const desktop = await optionsFor(1280);
  const mobile = await optionsFor(390);
  assert.ok(mobile.responsive[0].options.particles.number.value <= 40);
  assert.equal(mobile.particles.number.value, desktop.particles.number.value,
    'base budget must stay desktop-sized so resizing back restores it');
});

test('reduced motion uses a single static frame', async () => {
  const o = await optionsFor(1280, true);
  assert.equal(o.autoPlay, false);
  assert.equal(o.particles.move.enable, false);
});

test('uses bounded, slow tsParticles links without expensive effects', async () => {
  const o = await optionsFor(1280);
  assert.equal(o.fpsLimit, 30);
  assert.equal(o.detectRetina, false);
  assert.equal(o.pauseOnBlur, true);
  assert.equal(o.particles.links.enable, true);
  assert.ok(o.particles.color.value.includes('#FDD26E'));
  assert.ok(o.particles.number.value <= 100);
  assert.ok(o.particles.move.speed <= 0.3);
  assert.equal(o.interactivity.events.onHover.enable, false);
});
