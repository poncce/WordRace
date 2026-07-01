/**
 * UI — all DOM manipulation.
 *
 * Depends on: GameState
 * Never touches network / socket directly.
 */

const UI = (() => {
  // ── Screen management ────────────────────────────────────────────────
  function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(id);
    if (target) target.classList.add('active');
    window.scrollTo(0, 0);
  }

  // ── Toast notifications ──────────────────────────────────────────────
  function toast(message, type = 'default', duration = 2500) {
    const container = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = 'toast' + (type !== 'default' ? ` ${type}` : '');
    el.textContent = message;
    container.appendChild(el);
    setTimeout(() => {
      el.classList.add('fade-out');
      setTimeout(() => el.remove(), 300);
    }, duration);
  }

  // ── Waiting room ─────────────────────────────────────────────────────
  function updateRoomCode(code) {
    const el = document.getElementById('room-code-big');
    if (el) el.textContent = code;
  }

  function renderPlayersList(players, myId, hostId) {
    const list = document.getElementById('players-list');
    const countEl = document.getElementById('player-count');
    if (!list) return;

    const connected = players.filter(p => p.connected !== false);
    if (countEl) countEl.textContent = connected.length;

    list.innerHTML = '';
    players.forEach(p => {
      const isHost = p.id === hostId || p.is_host;
      const isMe   = p.id === myId;
      const isConn = p.connected !== false;

      const li = document.createElement('li');
      li.className = 'player-item';
      li.innerHTML = `
        <div class="player-avatar ${isConn ? '' : 'disconnected'}">
          ${p.nickname.charAt(0).toUpperCase()}
        </div>
        <span class="player-name">${_esc(p.nickname)}</span>
        ${isHost ? '<span class="player-badge-host">Anfitrión</span>' : ''}
        ${isMe   ? '<span class="player-badge-you">tú</span>'         : ''}
        ${!isConn ? '<span class="player-badge-you">desconectado</span>' : ''}
      `;
      list.appendChild(li);
    });
  }

  function setHostControls(isHost) {
    const startBtn  = document.getElementById('start-game-btn');
    const waitHint  = document.getElementById('waiting-hint');

    if (startBtn)  startBtn.classList.toggle('hidden', !isHost);
    if (waitHint)  waitHint.classList.toggle('hidden', isHost);
  }

  // ── Game board ───────────────────────────────────────────────────────
  function buildBoard(wordLength, maxAttempts) {
    const board = document.getElementById('game-board');
    board.innerHTML = '';

    // Adjust tile size for longer words
    const tileSize = wordLength >= 7 ? '46px' : (wordLength === 6 ? '52px' : '58px');
    document.documentElement.style.setProperty('--tile-size', tileSize);

    for (let r = 0; r < maxAttempts; r++) {
      const row = document.createElement('div');
      row.className = 'board-row';
      row.dataset.row = r;
      for (let c = 0; c < wordLength; c++) {
        const tile = document.createElement('div');
        tile.className = 'tile';
        tile.dataset.row = r;
        tile.dataset.col = c;
        tile.style.width  = tileSize;
        tile.style.height = tileSize;
        row.appendChild(tile);
      }
      board.appendChild(row);
    }
  }

  function renderCurrentInput(letters, wordLength) {
    const row = GameState.getCurrentRow();
    const rowEl = _getRow(row);
    if (!rowEl) return;
    for (let c = 0; c < wordLength; c++) {
      const tile = rowEl.children[c];
      const letter = letters[c] || '';
      tile.textContent = letter;
      tile.dataset.letter = letter;
    }
    rowEl.querySelectorAll('.tile').forEach(t => t.classList.toggle('current-row', true));
  }

  function revealGuessResult(rowIndex, tiles, onComplete) {
    const rowEl = _getRow(rowIndex);
    if (!rowEl) { if (onComplete) onComplete(); return; }

    tiles.forEach((tile, i) => {
      const tileEl = rowEl.children[i];
      tileEl.style.setProperty('--tile-color', _stateColor(tile.state));
      tileEl.style.animationDelay = `${i * 120}ms`;
      tileEl.classList.add('reveal');
      tileEl.classList.remove('current-row');
      setTimeout(() => {
        tileEl.classList.remove('reveal');
        tileEl.classList.add(tile.state);
      }, 500 + i * 120);
    });

    const totalDuration = 500 + (tiles.length - 1) * 120 + 100;
    setTimeout(() => { if (onComplete) onComplete(); }, totalDuration);
  }

  function shakeRow(rowIndex) {
    const rowEl = _getRow(rowIndex);
    if (!rowEl) return;
    rowEl.classList.remove('shake');
    void rowEl.offsetWidth; // force reflow
    rowEl.classList.add('shake');
    setTimeout(() => rowEl.classList.remove('shake'), 400);
  }

  function setGuessMessage(msg, autoHide = true) {
    const el = document.getElementById('guess-message');
    if (!el) return;
    el.textContent = msg;
    el.classList.add('visible');
    if (autoHide) {
      setTimeout(() => el.classList.remove('visible'), 2000);
    }
  }

  // ── Keyboard ─────────────────────────────────────────────────────────
  const ROWS = [
    ['Q','W','E','R','T','Y','U','I','O','P'],
    ['A','S','D','F','G','H','J','K','L','Ñ'],
    ['ENTER','Z','X','C','V','B','N','M','⌫'],
  ];

  function buildKeyboard(onKey) {
    const kb = document.getElementById('keyboard');
    kb.innerHTML = '';
    ROWS.forEach(row => {
      const rowEl = document.createElement('div');
      rowEl.className = 'key-row';
      row.forEach(k => {
        const btn = document.createElement('button');
        btn.className = 'key' + (k.length > 1 ? ' wide' : '');
        btn.textContent = k;
        btn.dataset.key = k;
        btn.addEventListener('click', () => onKey(k));
        rowEl.appendChild(btn);
      });
      kb.appendChild(rowEl);
    });
  }

  function updateKeyboard(letterStates) {
    const kb = document.getElementById('keyboard');
    if (!kb) return;
    kb.querySelectorAll('.key[data-key]').forEach(btn => {
      const k = btn.dataset.key;
      const state = letterStates[k];
      btn.className = 'key' + (k.length > 1 ? ' wide' : '') + (state ? ` ${state}` : '');
    });
  }

  // ── Players sidebar ──────────────────────────────────────────────────
  function renderPlayersProgress(otherPlayers, wordLength, maxAttempts) {
    const container = document.getElementById('players-progress');
    if (!container) return;
    container.innerHTML = '';

    Object.entries(otherPlayers).forEach(([pid, data]) => {
      const item = document.createElement('div');
      item.className = 'player-progress-item';
      item.id = `pp-${pid}`;

      let statusLabel = 'playing', statusClass = 'playing';
      if (data.finished) {
        if (data.won)  { statusLabel = '¡Ganó!'; statusClass = 'won'; }
        else           { statusLabel = 'Perdió'; statusClass = 'lost'; }
      } else {
        statusLabel = `${data.attempts_used}/${maxAttempts}`;
      }

      item.innerHTML = `
        <div class="pp-header">
          <span class="pp-name">${_esc(data.nickname)}</span>
          <span class="pp-status ${statusClass}">${statusLabel}</span>
        </div>
        <div class="mini-board" id="mini-${pid}"></div>
      `;
      container.appendChild(item);
      _renderMiniBoard(pid, data.tiles_history, wordLength, maxAttempts);
    });
  }

  function updatePlayerProgress(pid, data, wordLength, maxAttempts) {
    let item = document.getElementById(`pp-${pid}`);
    if (!item) {
      // Player joined after game start
      renderPlayersProgress(GameState.getOtherPlayers(), wordLength, maxAttempts);
      return;
    }

    const header = item.querySelector('.pp-header');
    let statusLabel = 'playing', statusClass = 'playing';
    if (data.finished) {
      if (data.won)  { statusLabel = '¡Ganó!'; statusClass = 'won'; }
      else           { statusLabel = 'Perdió'; statusClass = 'lost'; }
    } else {
      statusLabel = `${data.attempts_used}/${maxAttempts}`;
    }

    const statusEl = header.querySelector('.pp-status');
    if (statusEl) {
      statusEl.textContent = statusLabel;
      statusEl.className = `pp-status ${statusClass}`;
    }

    _renderMiniBoard(pid, data.tiles_history, wordLength, maxAttempts);
  }

  function _renderMiniBoard(pid, tilesHistory, wordLength, maxAttempts) {
    const mb = document.getElementById(`mini-${pid}`);
    if (!mb) return;
    mb.innerHTML = '';

    for (let r = 0; r < maxAttempts; r++) {
      const row = document.createElement('div');
      row.className = 'mini-row';
      const tileRow = tilesHistory[r] || [];
      for (let c = 0; c < wordLength; c++) {
        const t = document.createElement('div');
        t.className = 'mini-tile' + (tileRow[c] ? ` ${tileRow[c]}` : '');
        row.appendChild(t);
      }
      mb.appendChild(row);
    }
  }

  // ── Results screen ───────────────────────────────────────────────────
  function renderResults(word, rankings, myId) {
    const titleEl    = document.getElementById('results-title');
    const wordEl     = document.getElementById('secret-word');
    const rankEl     = document.getElementById('rankings-list');

    const myRank = rankings.find(r => r.player_id === myId);
    if (titleEl) {
      titleEl.textContent = myRank?.won ? '🎉 ¡Ganaste!' : '😔 Fin del juego';
    }

    // Show word as tiles
    if (wordEl) {
      wordEl.innerHTML = '';
      [...word].forEach(letter => {
        const t = document.createElement('div');
        t.className = 'tile';
        t.textContent = letter;
        wordEl.appendChild(t);
      });
    }

    // Rankings
    if (rankEl) {
      rankEl.innerHTML = '';
      const medals = ['🥇','🥈','🥉'];
      rankings.forEach(r => {
        const item = document.createElement('div');
        item.className = 'ranking-item';
        const medal = medals[r.rank - 1] || `#${r.rank}`;
        item.innerHTML = `
          <div class="rank-medal">${medal}</div>
          <div class="rank-info">
            <div class="rank-name">${_esc(r.nickname)}${r.player_id === myId ? ' <span class="player-badge-you">(tú)</span>' : ''}</div>
            <div class="rank-detail">${r.won ? `Adivinó en ${r.attempts_used} ${r.attempts_used === 1 ? 'intento' : 'intentos'}` : 'No adivinó'}</div>
          </div>
          <div class="${r.won ? 'rank-won' : 'rank-lost'}">${r.won ? '✓' : '✗'}</div>
        `;
        rankEl.appendChild(item);
      });
    }
  }

  function setGameInfoBar(text) {
    const el = document.getElementById('game-info-bar');
    if (el) el.textContent = text;
  }

  // ── Helpers ──────────────────────────────────────────────────────────
  function _getRow(index) {
    return document.querySelector(`.board-row[data-row="${index}"]`);
  }

  function _stateColor(state) {
    const map = { correct: 'var(--correct-bg)', present: 'var(--present-bg)', absent: 'var(--absent-bg)' };
    return map[state] || 'var(--absent-bg)';
  }

  function _esc(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  return {
    showScreen, toast,
    updateRoomCode, renderPlayersList, setHostControls,
    buildBoard, renderCurrentInput, revealGuessResult, shakeRow, setGuessMessage,
    buildKeyboard, updateKeyboard,
    renderPlayersProgress, updatePlayerProgress,
    renderResults, setGameInfoBar,
  };
})();
