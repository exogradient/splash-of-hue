/* ═══════ HOME — Paint-chip card stack logic ═══════
   Builds the card stack inside #menu.
   Toolbar markup lives in index.html (not generated here).
   Depends on: startGame() from index.html.
   ═══════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* Each tab earns one centered visual cue; ordinal decoration is intentionally omitted. */
  var MODES = [
    {
      id: 'match', label: 'Match It', cls: 'home-match',
      detail: 'Tune beside the target',
      cue: '<span class="home-cue-pair"><i></i><i></i></span>',
    },
    {
      id: 'picture', label: 'Picture It', cls: 'home-picture',
      detail: 'Pick the color from HSB',
      cue: '<span class="home-cue-hsb"><i>H</i><i>S</i><i>B</i></span>',
    },
    {
      id: 'call', label: 'Call It', cls: 'home-call',
      detail: 'Choose its closest word',
      cue: '<span class="home-cue-word">coral</span>',
    },
    {
      id: 'split', label: 'Split It', cls: 'home-split',
      detail: 'Estimate hue, saturation, brightness',
      cue: '<span class="home-cue-bars"><i></i><i></i><i></i></span>',
    },
  ];

  function buildHome() {
    var menu = document.getElementById('menu');
    if (!menu) return;

    /* Grab the toolbar before we restructure — it's already in the HTML */
    var tools = menu.querySelector('.home-tools');

    /* ── Shell ── */
    var shell = document.createElement('div');
    shell.className = 'menu-shell';

    /* ── Stack wrapper (cards + toolbar) ── */
    var stack = document.createElement('div');
    stack.className = 'home-stack';

    /* ── Cards row (the overlapping deck) ── */
    var cards = document.createElement('div');
    cards.className = 'home-cards';

    /* Play card */
    var play = document.createElement('button');
    play.className = 'home-play';
    play.setAttribute('data-mode', 'play');
    play.setAttribute('aria-label', 'Play — memorize a color, recreate it from memory');
    play.innerHTML =
      '<span class="home-brand">splash of hue</span>' +
      '<span class="home-play-label">Play</span>';
    play.addEventListener('click', function () { startGame('play'); });
    cards.appendChild(play);

    /* Secondary mode cards */
    var COMING_SOON = {};
    MODES.forEach(function (m) {
      var card = document.createElement('button');
      var soon = COMING_SOON[m.id];
      card.className = 'home-mode ' + m.cls + (soon ? ' home-mode--soon' : '');
      card.setAttribute('data-mode', m.id);
      card.setAttribute('aria-label', m.label + ' — ' + m.detail + (soon ? ' (coming soon)' : ''));
      if (soon) {
        card.disabled = true;
        card.innerHTML = '<span class="home-mode-head" aria-hidden="true">' + m.cue + '</span>' +
          '<span class="home-mode-copy"><span class="home-mode-name">' + m.label + '</span></span>' +
          '<span class="home-mode-soon">Soon</span>';
      } else {
        card.innerHTML = '<span class="home-mode-head" aria-hidden="true">' + m.cue + '</span>' +
          '<span class="home-mode-copy"><span class="home-mode-name">' + m.label + '</span></span>';
        card.addEventListener('click', function () { startGame(m.id); });
      }
      cards.appendChild(card);
    });

    stack.appendChild(cards);

    /* Toolbar sits below cards, inherits the same max-width */
    if (tools) stack.appendChild(tools);

    shell.appendChild(stack);

    /* ── Replace menu contents with shell ── */
    menu.innerHTML = '';
    menu.appendChild(shell);

  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildHome);
  } else {
    buildHome();
  }
})();
