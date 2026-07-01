

const SocketClient = (() => {
  let _socket = null;
  let _pingInterval = null;
  let _handlers = {};
  let _connected = false;

  function on(event, handler) {
    if (!_handlers[event]) _handlers[event] = [];
    _handlers[event].push(handler);
  }

  function off(event, handler) {
    if (!_handlers[event]) return;
    _handlers[event] = _handlers[event].filter(h => h !== handler);
  }

  function _dispatch(event, data) {
    (_handlers[event] || []).forEach(h => {
      try { h(data); } catch (e) { console.error(`Handler error [${event}]:`, e); }
    });
  }

  function connect() {
    if (_socket) return;

    _socket = io({
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 10000,
    });

    _socket.on('connect', () => {
      _connected = true;
      console.log('[socket] connected:', _socket.id);
      _dispatch('_connected', {});
      _startHeartbeat();

      const savedId   = localStorage.getItem('wr_player_id');
      const savedCode = localStorage.getItem('wr_room_code');
      if (savedId && savedCode) {
        _dispatch('_restore_session', { player_id: savedId, room_code: savedCode });
      }
    });

    _socket.on('disconnect', reason => {
      _connected = false;
      _stopHeartbeat();
      console.log('[socket] disconnected:', reason);
      _dispatch('_disconnected', { reason });
    });

    _socket.on('connect_error', err => {
      console.warn('[socket] connect error:', err.message);
      _dispatch('_connect_error', { message: err.message });
    });

    const SERVER_EVENTS = [
      'room_created', 'room_joined', 'room_updated',
      'player_joined', 'player_left', 'player_disconnected',
      'host_changed', 'game_started', 'guess_result',
      'player_progress', 'game_finished', 'reconnected',
      'error', 'pong',
    ];
    SERVER_EVENTS.forEach(evt => {
      _socket.on(evt, data => {
        console.debug(`[socket] ← ${evt}`, data);
        _dispatch(evt, data);
      });
    });
  }

  function _startHeartbeat() {
    _pingInterval = setInterval(() => {
      if (_socket && _connected) {
        _socket.emit('ping', { timestamp: Date.now() });
      }
    }, 15000);
  }

  function _stopHeartbeat() {
    clearInterval(_pingInterval);
    _pingInterval = null;
  }

  function emit(event, data = {}) {
    if (!_socket || !_connected) {
      console.warn('[socket] tried to emit while disconnected:', event);
      return;
    }
    console.debug(`[socket] → ${event}`, data);
    _socket.emit(event, data);
  }

  function isConnected() { return _connected; }

  return { connect, on, off, emit, isConnected };
})();
