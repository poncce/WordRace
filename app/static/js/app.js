

const App = (() => {

  let _nickname   = '';
  let _playerId   = null;
  let _roomCode   = null;
  let _roomId     = null;
  let _isHost     = false;
  let _players    = [];
  let _settings   = { word_length: 5, max_attempts: 6 };
  let _inGame     = false;
  let _pendingSubmit = false;
  let _pendingStart = false;

  function init() {

    const saved = localStorage.getItem('wr_nickname');
    if (saved) {
      _nickname = saved;
      _goToLobby();
    }

    _bindUIEvents();
    _bindSocketEvents();

    SocketClient.connect();
  }

  function _bindUIEvents() {

    _on('nickname-input', 'keydown', e => { if (e.key === 'Enter') _submitNickname(); });
    _on('nickname-btn',   'click',   _submitNickname);

    _on('change-nickname-btn', 'click', () => UI.showScreen('screen-nickname'));
    _on('create-room-btn',     'click', _createRoom);
    _on('room-code-input',     'keydown', e => { if (e.key === 'Enter') _joinRoom(); });
    _on('join-room-btn',       'click', _joinRoom);

    _on('leave-waiting-btn', 'click', _leaveRoom);
    _on('copy-code-btn',     'click', () => _copyToClipboard(_roomCode, 'Código copiado'));
    _on('copy-link-btn',     'click', () => _copyToClipboard(`${location.origin}/join/${_roomCode}`, 'Enlace copiado'));
    _on('start-game-btn',    'click', _startGame);

    _on('back-to-room-btn', 'click', _backToRoom);

    document.addEventListener('keydown', _onPhysicalKey);

    const path = window.location.pathname;
    const match = path.match(/^\/join\/([A-Z0-9]{6})$/i);
    if (match) {
      localStorage.setItem('wr_pending_join', match[1].toUpperCase());
    }
  }

  function _bindSocketEvents() {
    SocketClient.on('_connected', () => {
      UI.toast('Conectado', 'success', 1500);
    });

    SocketClient.on('_disconnected', () => {
      UI.toast('Conexión perdida. Reconectando…', 'error', 3000);
    });

    SocketClient.on('_restore_session', ({ player_id, room_code }) => {
      SocketClient.emit('reconnect_player', { player_id, room_code });
    });

    SocketClient.on('room_created', data => {
      _saveSession(data.player.id, data.room_code);
      _isHost   = true;
      _players  = data.room.players;
      _settings = data.room.settings;
      _enterWaitingRoom(data.room_code, data.room_id, data.player);
    });

    SocketClient.on('room_joined', data => {
      _saveSession(data.player.id, data.room.code);
      _isHost   = data.player.is_host;
      _players  = data.room.players;
      _settings = data.room.settings;
      _enterWaitingRoom(data.room.code, data.room.id, data.player);
    });

    SocketClient.on('room_updated', data => {
      _players  = data.room.players;
      _settings = data.room.settings;

      const onResults = document.getElementById('screen-results').classList.contains('active');
      if (onResults && data.room.state === 'waiting') {
        _inGame = false;
        UI.showScreen('screen-waiting');
      }
      _renderWaitingRoom();
    });

    SocketClient.on('player_joined', data => {
      const p = data.player;
      if (!_players.find(x => x.id === p.id)) _players.push(p);
      UI.renderPlayersList(_players, _playerId, _getHostId());
      if (_inGame) GameState.addOtherPlayer(p);
      UI.toast(`${p.nickname} se unió`);
    });

    SocketClient.on('player_left', data => {
      _players = _players.filter(p => p.id !== data.player_id);
      UI.renderPlayersList(_players, _playerId, _getHostId());
      if (_inGame) {
        GameState.removeOtherPlayer(data.player_id);
        UI.renderPlayersProgress(GameState.getOtherPlayers(), GameState.getWordLength(), GameState.getMaxAttempts());
      }
      if (data.new_host_id === _playerId) {
        _isHost = true;
        UI.setHostControls(true);
      }
      UI.toast(`${data.nickname} salió`);
    });

    SocketClient.on('player_disconnected', data => {
      const p = _players.find(x => x.id === data.player_id);
      if (p) p.connected = false;
      UI.renderPlayersList(_players, _playerId, _getHostId());
      UI.toast(`${data.nickname} se desconectó`, 'error');
    });

    SocketClient.on('host_changed', data => {
      _players.forEach(p => { p.is_host = p.id === data.new_host_id; });
      if (data.new_host_id === _playerId) {
        _isHost = true;
        UI.setHostControls(true);
        UI.toast('Ahora eres el anfitrión');
      }
      UI.renderPlayersList(_players, _playerId, data.new_host_id);
    });

    SocketClient.on('game_started', data => {
      _pendingStart = false;
      _inGame = true;
      GameState.reset(data.word_length, data.max_attempts);
      GameState.initOtherPlayers(_players.filter(p => p.id !== _playerId), _playerId);

      UI.showScreen('screen-game');
      UI.buildBoard(data.word_length, data.max_attempts);
      UI.buildKeyboard(_onKeyPress);
      UI.renderPlayersProgress(GameState.getOtherPlayers(), data.word_length, data.max_attempts);
      UI.setGameInfoBar(`${data.word_length} letras · ${data.max_attempts} intentos`);
      UI.renderCurrentInput([], data.word_length);
    });

    SocketClient.on('guess_result', data => {
      _pendingSubmit = false;
      const { tiles, won, attempts_left, attempts_used } = data;

      GameState.applyGuessResult(tiles, won, attempts_left);

      const rowIndex = attempts_used - 1;
      UI.revealGuessResult(rowIndex, tiles, () => {
        UI.updateKeyboard(GameState.getLetterStates());

        if (won) {
          UI.setGuessMessage('🎉 ¡Correcto!', false);
        } else if (attempts_left <= 0) {
          UI.setGuessMessage('Sin más intentos…', false);
        } else {
          UI.renderCurrentInput([], GameState.getWordLength());
        }
      });
    });

    SocketClient.on('player_progress', data => {
      GameState.updateOtherPlayer(data.player_id, data);
      UI.updatePlayerProgress(data.player_id, data, GameState.getWordLength(), GameState.getMaxAttempts());
    });

    SocketClient.on('game_finished', data => {
      _inGame = false;
      setTimeout(() => {
        UI.renderResults(data.word, data.rankings, _playerId);
        UI.showScreen('screen-results');
      }, 1800);
    });

    SocketClient.on('reconnected', data => {
      const { player, room, game } = data;
      _playerId = player.id;
      _isHost   = player.is_host;
      _players  = room.players;
      _settings = room.settings;
      _roomCode = room.code;
      _roomId   = room.id;

      if (room.state === 'playing' && game) {
        _inGame = true;
        const wl = game.word_length;
        const ma = game.max_attempts;
        GameState.reset(wl, ma);
        GameState.initOtherPlayers(_players.filter(p => p.id !== _playerId), _playerId);

        if (game.my_guesses) {
          game.my_guesses.forEach(g => {
            GameState.applyGuessResult(g.tiles, g.tiles.every(t => t.state === 'correct'), 1);
          });
        }

        if (game.player_states) {
          Object.entries(game.player_states).forEach(([pid, state]) => {
            if (pid !== _playerId) {
              GameState.updateOtherPlayer(pid, state);
            }
          });
        }

        UI.showScreen('screen-game');
        UI.buildBoard(wl, ma);
        UI.buildKeyboard(_onKeyPress);

        GameState.getGuesses().forEach((record, rowIdx) => {
          record.tiles.forEach((tile, c) => {
            const tileEl = document.querySelector(`.tile[data-row="${rowIdx}"][data-col="${c}"]`);
            if (tileEl) {
              tileEl.textContent = tile.letter;
              tileEl.className = `tile ${tile.state}`;
            }
          });
        });

        UI.updateKeyboard(GameState.getLetterStates());
        UI.renderPlayersProgress(GameState.getOtherPlayers(), wl, ma);
        UI.renderCurrentInput([], wl);

      } else if (room.state === 'finished') {
        UI.showScreen('screen-results');
      } else {
        _enterWaitingRoom(room.code, room.id, player);
      }

      UI.toast('Reconectado', 'success', 1500);
    });

    SocketClient.on('error', data => {
      _pendingSubmit = false;
      _pendingStart = false;
      const btn = document.getElementById('start-game-btn');
      if (btn) { btn.disabled = false; btn.textContent = '¡Comenzar juego!'; }

      const msg = data.message || 'Error desconocido';

      if (data.code === 'INVALID_WORD' || data.code === 'WRONG_WORD_LENGTH' || data.code === 'DUPLICATE_GUESS') {
        UI.setGuessMessage(msg);
        UI.shakeRow(GameState.getCurrentRow());
      } else if (data.code === 'RATE_LIMIT') {
        UI.toast(msg, 'error');
      } else if (data.code === 'PLAYER_NOT_FOUND' || data.code === 'ROOM_NOT_FOUND') {

        _clearSession();
        UI.toast('Sesión expirada. Crea o únete a una sala.', 'error', 4000);
        _goToLobby();
      } else {
        UI.toast(msg, 'error', 3000);
      }
    });
  }

  function _submitNickname() {
    const input = document.getElementById('nickname-input');
    const name  = input ? input.value.trim() : '';
    if (!name) { UI.toast('Ingresa un apodo', 'error'); return; }
    _nickname = name;
    localStorage.setItem('wr_nickname', name);
    _goToLobby();
  }

  function _goToLobby() {
    const el = document.getElementById('lobby-nickname');
    if (el) el.textContent = _nickname;
    UI.showScreen('screen-lobby');

    const pending = localStorage.getItem('wr_pending_join');
    if (pending) {
      localStorage.removeItem('wr_pending_join');
      const input = document.getElementById('room-code-input');
      if (input) input.value = pending;
    }
  }

  function _createRoom() {
    if (!SocketClient.isConnected()) { UI.toast('Sin conexión', 'error'); return; }
    SocketClient.emit('create_room', { nickname: _nickname, settings: _settings });
  }

  function _joinRoom() {
    if (!SocketClient.isConnected()) { UI.toast('Sin conexión', 'error'); return; }
    const input = document.getElementById('room-code-input');
    const code  = input ? input.value.trim().toUpperCase() : '';
    if (code.length < 4) { UI.toast('Código inválido', 'error'); return; }
    SocketClient.emit('join_room', { nickname: _nickname, room_code: code });
  }

  function _enterWaitingRoom(code, roomId, player) {
    _roomCode = code;
    _roomId   = roomId;
    _playerId = player.id;
    _isHost   = player.is_host;
    _inGame   = false;

    UI.showScreen('screen-waiting');
    _renderWaitingRoom();
  }

  function _renderWaitingRoom() {
    UI.updateRoomCode(_roomCode);
    UI.renderPlayersList(_players, _playerId, _getHostId());
    UI.setHostControls(_isHost);
  }

  function _leaveRoom() {
    SocketClient.emit('leave_room', {});
    _clearSession();
    _goToLobby();
  }

  function _startGame() {
    if (_pendingStart) return;
    if (_players.length < 1) { UI.toast('Necesitas al menos 1 jugador', 'error'); return; }
    _pendingStart = true;
    const btn = document.getElementById('start-game-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Iniciando…'; }
    SocketClient.emit('start_game', { player_id: _playerId });

    setTimeout(() => {
      _pendingStart = false;
      if (btn) { btn.disabled = false; btn.textContent = '¡Comenzar juego!'; }
    }, 5000);
  }

  function _backToRoom() {
    _inGame = false;
    if (_isHost) {

      SocketClient.emit('reset_room', { player_id: _playerId });
    }
    UI.showScreen('screen-waiting');
    _renderWaitingRoom();
  }

  function _onKeyPress(key) {
    if (!_inGame || GameState.isFinished() || _pendingSubmit) return;

    if (key === 'ENTER') {
      _submitGuess();
    } else if (key === '⌫' || key === 'Backspace') {
      GameState.deleteLetter();
      UI.renderCurrentInput(GameState.getCurrentInput(), GameState.getWordLength());
    } else if (/^[A-ZÑ]$/i.test(key)) {
      GameState.addLetter(key.toUpperCase());
      UI.renderCurrentInput(GameState.getCurrentInput(), GameState.getWordLength());
    }
  }

  function _onPhysicalKey(e) {
    if (!_inGame || GameState.isFinished() || _pendingSubmit) return;
    if (e.ctrlKey || e.altKey || e.metaKey) return;
    if (e.key === 'Enter')     { _onKeyPress('ENTER'); }
    else if (e.key === 'Backspace') { _onKeyPress('⌫'); }
    else if (/^[a-záéíóúñA-ZÁÉÍÓÚÑ]$/.test(e.key)) { _onKeyPress(e.key.toUpperCase()); }
  }

  function _submitGuess() {
    if (!GameState.canSubmit()) {
      UI.setGuessMessage(`Faltan letras (${GameState.getWordLength()} en total)`);
      UI.shakeRow(GameState.getCurrentRow());
      return;
    }
    _pendingSubmit = true;
    SocketClient.emit('submit_guess', { word: GameState.getSubmitWord(), player_id: _playerId });
  }

  function _saveSession(playerId, roomCode) {
    _playerId = playerId;
    _roomCode = roomCode;
    localStorage.setItem('wr_player_id', playerId);
    localStorage.setItem('wr_room_code', roomCode);
  }

  function _clearSession() {
    _playerId = null;
    _roomCode = null;
    _roomId   = null;
    localStorage.removeItem('wr_player_id');
    localStorage.removeItem('wr_room_code');
  }

  function _getHostId() {
    const host = _players.find(p => p.is_host);
    return host ? host.id : null;
  }

  function _copyToClipboard(text, successMsg) {
    navigator.clipboard.writeText(text)
      .then(() => UI.toast(successMsg, 'success'))
      .catch(() => UI.toast('No se pudo copiar', 'error'));
  }

  function _on(id, event, handler) {
    const el = document.getElementById(id);
    if (el) el.addEventListener(event, handler);
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', () => App.init());
