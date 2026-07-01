

const GameState = (() => {
  let _wordLength   = 5;
  let _maxAttempts  = 6;
  let _currentRow   = 0;
  let _currentInput = [];
  let _guesses      = [];
  let _finished     = false;
  let _won          = false;
  let _letterStates = {};
  let _otherPlayers = {};

  const STATE_PRIORITY = { correct: 3, present: 2, absent: 1 };

  function reset(wordLength, maxAttempts) {
    _wordLength   = wordLength;
    _maxAttempts  = maxAttempts;
    _currentRow   = 0;
    _currentInput = [];
    _guesses      = [];
    _finished     = false;
    _won          = false;
    _letterStates = {};
    _otherPlayers = {};
  }

  function initOtherPlayers(players, myId) {
    _otherPlayers = {};
    players.forEach(p => {
      if (p.id !== myId) {
        _otherPlayers[p.id] = {
          nickname: p.nickname,
          attempts_used: 0,
          won: false,
          finished: false,
          tiles_history: [],
        };
      }
    });
  }

  function addLetter(letter) {
    if (_finished || _currentInput.length >= _wordLength) return false;
    _currentInput.push(letter.toUpperCase());
    return true;
  }

  function deleteLetter() {
    if (_currentInput.length === 0) return false;
    _currentInput.pop();
    return true;
  }

  function getCurrentInput() { return [..._currentInput]; }

  function canSubmit() {
    return !_finished && _currentInput.length === _wordLength;
  }

  function getSubmitWord() {
    return _currentInput.join('');
  }

  function clearInput() {
    _currentInput = [];
  }

  function applyGuessResult(tiles, won, attemptsLeft) {
    const record = {
      word: tiles.map(t => t.letter).join(''),
      tiles,
    };
    _guesses.push(record);
    _currentRow++;
    _currentInput = [];

    tiles.forEach(({ letter, state }) => {
      const current = STATE_PRIORITY[_letterStates[letter]] || 0;
      if ((STATE_PRIORITY[state] || 0) > current) {
        _letterStates[letter] = state;
      }
    });

    if (won || attemptsLeft <= 0) {
      _finished = true;
      _won = won;
    }
  }

  function updateOtherPlayer(player_id, data) {
    if (!_otherPlayers[player_id]) {
      _otherPlayers[player_id] = { nickname: data.nickname || '?', tiles_history: [] };
    }
    Object.assign(_otherPlayers[player_id], {
      attempts_used: data.attempts_used,
      won: data.won,
      finished: data.finished,
      tiles_history: data.tiles_history || _otherPlayers[player_id].tiles_history,
    });
  }

  function addOtherPlayer(player) {
    if (!_otherPlayers[player.id]) {
      _otherPlayers[player.id] = {
        nickname: player.nickname,
        attempts_used: 0,
        won: false,
        finished: false,
        tiles_history: [],
      };
    }
  }

  function removeOtherPlayer(player_id) {
    delete _otherPlayers[player_id];
  }

  function getWordLength()    { return _wordLength; }
  function getMaxAttempts()   { return _maxAttempts; }
  function getCurrentRow()    { return _currentRow; }
  function getGuesses()       { return _guesses; }
  function isFinished()       { return _finished; }
  function didWin()           { return _won; }
  function getLetterStates()  { return { ..._letterStates }; }
  function getOtherPlayers()  { return { ..._otherPlayers }; }

  return {
    reset, initOtherPlayers,
    addLetter, deleteLetter, getCurrentInput, canSubmit, getSubmitWord, clearInput,
    applyGuessResult,
    updateOtherPlayer, addOtherPlayer, removeOtherPlayer,
    getWordLength, getMaxAttempts, getCurrentRow, getGuesses,
    isFinished, didWin, getLetterStates, getOtherPlayers,
  };
})();
