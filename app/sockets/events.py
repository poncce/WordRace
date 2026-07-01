"""
Socket.IO event name constants.

Protocol: every message is a JSON object with shape:
  { "type": "<EVENT_NAME>", "payload": { ... } }

However, Flask-SocketIO uses event names as the first argument to emit(),
so we use these constants as event names directly.

=== CLIENT → SERVER ===

  create_room
    payload: { nickname, settings: { word_length, max_attempts } }

  join_room
    payload: { nickname, room_code }

  leave_room
    payload: {}

  start_game
    payload: {}

  submit_guess
    payload: { word }

  update_settings
    payload: { settings: { word_length, max_attempts } }

  reconnect_player
    payload: { player_id, room_code }

  ping
    payload: { timestamp }

=== SERVER → CLIENT ===

  room_created
    payload: { room_code, room_id, player: { id, nickname, is_host } }

  room_joined
    payload: { room: Room, player: Player }

  room_updated
    payload: { room: Room }

  player_joined
    payload: { player: Player }

  player_left
    payload: { player_id, nickname, new_host_id? }

  player_disconnected
    payload: { player_id, nickname }

  host_changed
    payload: { new_host_id, new_host_nickname }

  game_started
    payload: { word_length, max_attempts, player_ids: [] }

  guess_result
    payload: { player_id, word, tiles: [{letter, state}], attempts_used, attempts_left, won }

  player_progress
    payload: { player_id, attempts_used, won, finished, tiles_history: [[state, ...], ...] }

  game_finished
    payload: { word, winner_id?, rankings: [{ rank, player_id, nickname, guesses, won }] }

  reconnected
    payload: { player: Player, room: Room, game: Game? }

  error
    payload: { code, message }

  pong
    payload: { timestamp }
"""

# Client → Server
CREATE_ROOM = "create_room"
JOIN_ROOM = "join_room"
LEAVE_ROOM = "leave_room"
START_GAME = "start_game"
SUBMIT_GUESS = "submit_guess"
UPDATE_SETTINGS = "update_settings"
RECONNECT_PLAYER = "reconnect_player"
RESET_ROOM = "reset_room"
PING = "ping"

# Server → Client
ROOM_CREATED = "room_created"
ROOM_JOINED = "room_joined"
ROOM_UPDATED = "room_updated"
PLAYER_JOINED = "player_joined"
PLAYER_LEFT = "player_left"
PLAYER_DISCONNECTED = "player_disconnected"
HOST_CHANGED = "host_changed"
GAME_STARTED = "game_started"
GUESS_RESULT = "guess_result"
PLAYER_PROGRESS = "player_progress"
GAME_FINISHED = "game_finished"
RECONNECTED = "reconnected"
ERROR = "error"
PONG = "pong"
