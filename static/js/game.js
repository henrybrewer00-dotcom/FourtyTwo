/**
 * GAME 42 - Main Game JavaScript
 * Handles game logic, WebSocket communication, and UI updates
 */

(function() {
    'use strict';

    // Game state
    let socket = null;
    let gameId = null;
    let myPosition = null;
    let isSpectator = false;
    let gameState = {};
    let currentUser = null;

    // DOM Elements - will be initialized after DOM ready
    let elements = {};

    // Position display names
    const positionNames = {
        'north': 'North',
        'south': 'South',
        'east': 'East',
        'west': 'West'
    };

    // Suit names for display
    const suitNames = ['Blanks', 'Ones', 'Twos', 'Threes', 'Fours', 'Fives', 'Sixes'];

    // Initialize
    function init() {
        // Get DOM elements
        elements = {
            gamePhase: document.getElementById('game-phase'),
            currentTurn: document.getElementById('current-turn'),
            team1Marks: document.getElementById('team1-marks'),
            team2Marks: document.getElementById('team2-marks'),
            team1Points: document.getElementById('team1-points'),
            team2Points: document.getElementById('team2-points'),
            trumpInfo: document.getElementById('trump-info'),
            trumpDisplay: document.getElementById('trump-display'),
            myHand: document.getElementById('my-hand'),
            myHandContainer: document.getElementById('my-hand-container'),
            biddingPanel: document.getElementById('bidding-panel'),
            trumpPanel: document.getElementById('trump-panel'),
            waitingPanel: document.getElementById('waiting-panel'),
            gameOverPanel: document.getElementById('game-over-panel'),
            highBidDisplay: document.getElementById('high-bid-display'),
            winningBid: document.getElementById('winning-bid'),
            playersStatus: document.getElementById('players-status'),
            startGameBtn: document.getElementById('start-game-btn'),
            addBotsBtn: document.getElementById('add-bots-btn'),
            waitingMessage: document.getElementById('waiting-message'),
            chatMessages: document.getElementById('chat-messages'),
            chatInput: document.getElementById('chat-input'),
            chatSend: document.getElementById('chat-send'),
            chatPanel: document.getElementById('chat-panel'),
            toast: document.getElementById('toast'),
            bidButtons: document.getElementById('bid-buttons')
        };

        const container = document.querySelector('.game-container');
        if (!container) {
            console.error('Game container not found');
            return;
        }
        gameId = container.dataset.gameId;

        // Connect to WebSocket
        socket = io();

        // Set up socket handlers
        setupSocketHandlers();

        // Set up UI handlers
        setupUIHandlers();

        // Load current user and join game
        loadCurrentUser();
    }

    async function loadCurrentUser() {
        try {
            const res = await fetch('/api/user');
            const data = await res.json();
            if (data.user) {
                currentUser = data.user;
                // Join game room
                socket.emit('join_game', { game_id: gameId });
            }
        } catch (err) {
            console.error('Failed to load user:', err);
            showToast('Failed to connect. Please refresh.', 'error');
        }
    }

    // WebSocket Handlers
    function setupSocketHandlers() {
        socket.on('connect', () => {
            console.log('Connected to server');
        });

        socket.on('connected', (data) => {
            console.log('User connected:', data.user);
        });

        socket.on('game_state', (state) => {
            console.log('Game state received:', state);
            gameState = state;
            myPosition = state.my_position || null;
            isSpectator = state.is_spectator || false;
            updateUI();
        });

        socket.on('player_joined', (data) => {
            showToast(`${data.username} joined as ${positionNames[data.position]}`);
            if (data.players) {
                gameState.players = data.players;
                gameState.phase = data.phase;
                updateUI();
            }
        });

        socket.on('player_left', (data) => {
            showToast(`${data.username} left the game`);
        });

        socket.on('bots_added', (data) => {
            showToast(data.message);
            if (data.players) {
                gameState.players = data.players;
                gameState.phase = data.phase;
                updateUI();
            }
        });

        socket.on('spectator_joined', (data) => {
            showToast(`${data.username} is now spectating`);
        });

        socket.on('game_started', (state) => {
            console.log('Game started:', state);
            gameState = state;
            myPosition = state.my_position;
            showToast('Game started! Time to bid.');
            updateUI();
        });

        socket.on('bid_update', (data) => {
            console.log('Bid update:', data);
            gameState.high_bid = data.high_bid;
            gameState.high_bidder = data.high_bidder;
            gameState.phase = data.phase;
            gameState.current_turn = data.current_turn;

            const playerName = gameState.players?.[data.position]?.username || data.position;
            if (data.bid > 0) {
                showToast(`${playerName} bid ${data.bid}`);
            } else {
                showToast(`${playerName} passed`);
            }

            // Mark player as passed or bid
            if (gameState.players && gameState.players[data.position]) {
                if (data.bid > 0) {
                    gameState.players[data.position].current_bid = data.bid;
                } else {
                    gameState.players[data.position].has_passed = true;
                }
            }

            updateUI();
        });

        socket.on('trump_selected', (data) => {
            console.log('Trump selected:', data);
            gameState.trump_suit = data.trump_suit;
            gameState.phase = data.phase;
            gameState.current_turn = data.current_turn;
            const leaderName = gameState.players[data.current_turn]?.username || 'Unknown';
            showToast(`Trump is ${suitNames[data.trump_suit]}! ${leaderName} leads.`);
            updateUI();
        });

        socket.on('domino_played', (data) => {
            console.log('Domino played:', data);

            // Update current trick
            gameState.current_trick = data.current_trick;
            gameState.lead_suit = data.lead_suit;
            gameState.phase = data.phase;
            gameState.current_turn = data.current_turn;

            // Show the played domino
            renderPlayedDomino(data.position, data.domino_id);

            if (data.trick_result) {
                // Trick is complete
                gameState.team1_tricks = data.team1_tricks;
                gameState.team2_tricks = data.team2_tricks;
                gameState.team1_hand_points = data.team1_hand_points;
                gameState.team2_hand_points = data.team2_hand_points;

                const winner = gameState.players[data.trick_result.winner];
                showToast(`${winner?.username} wins the trick! (${data.trick_result.points} pts)`);

                // Clear trick after delay and update UI
                setTimeout(() => {
                    clearPlayedDominoes();
                    updateUI();
                }, 1500);

                if (data.game_over) {
                    gameState.team1_marks = data.team1_marks;
                    gameState.team2_marks = data.team2_marks;
                    showGameOver(data.winner);
                }
            } else {
                // Update UI immediately for next player
                updateUI();
            }

            updateScores();
        });

        socket.on('hand_update', (data) => {
            if (myPosition && gameState.players && gameState.players[myPosition]) {
                gameState.players[myPosition].hand = data.hand;
                renderMyHand();
            }
        });

        socket.on('chat_message', (msg) => {
            appendChatMessage(msg);
        });

        socket.on('error', (data) => {
            console.error('Server error:', data);
            showToast(data.message, 'error');
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from server');
            showToast('Connection lost. Reconnecting...', 'error');
        });

        socket.on('reconnect', () => {
            console.log('Reconnected');
            showToast('Reconnected!', 'success');
            socket.emit('join_game', { game_id: gameId });
        });
    }

    // UI Handlers
    function setupUIHandlers() {
        // Bid buttons - use event delegation
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('bid-btn')) {
                const bid = parseInt(e.target.dataset.bid);
                console.log('Placing bid:', bid);
                socket.emit('place_bid', { game_id: gameId, bid: bid });
            }
        });

        // Pass button
        const passBtn = document.getElementById('pass-btn');
        if (passBtn) {
            passBtn.addEventListener('click', () => {
                console.log('Passing');
                socket.emit('place_bid', { game_id: gameId, bid: 0 });
            });
        }

        // Trump buttons - use event delegation
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('trump-btn')) {
                const suit = parseInt(e.target.dataset.suit);
                console.log('Selecting trump:', suit);
                socket.emit('select_trump', { game_id: gameId, suit: suit });
            }
        });

        // Start game button
        const startBtn = document.getElementById('start-game-btn');
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                console.log('Starting game');
                socket.emit('start_game', { game_id: gameId });
            });
        }

        // Add bots button
        const addBotsBtn = document.getElementById('add-bots-btn');
        if (addBotsBtn) {
            addBotsBtn.addEventListener('click', () => {
                console.log('Adding bots');
                socket.emit('add_bots', { game_id: gameId });
            });
        }

        // Chat
        const chatSend = document.getElementById('chat-send');
        const chatInput = document.getElementById('chat-input');
        if (chatSend) {
            chatSend.addEventListener('click', sendChatMessage);
        }
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendChatMessage();
            });
        }

        // Emoji buttons
        document.querySelectorAll('.emoji-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const emoji = btn.dataset.emoji;
                const input = document.getElementById('chat-input');
                if (input) {
                    input.value += emoji;
                    input.focus();
                }
            });
        });

        // Chat minimize toggle
        const chatToggle = document.getElementById('chat-toggle');
        if (chatToggle) {
            chatToggle.addEventListener('click', () => {
                const chatPanel = document.getElementById('chat-panel');
                if (chatPanel) {
                    chatPanel.classList.toggle('minimized');
                    chatToggle.textContent = chatPanel.classList.contains('minimized') ? '+' : '−';
                }
            });
        }
    }

    // Update UI
    function updateUI() {
        updatePhaseDisplay();
        updateScores();
        updatePlayers();
        updatePanels();
        renderMyHand();
        renderCurrentTrick();
        updateTrumpDisplay();
    }

    function updatePhaseDisplay() {
        const phaseNames = {
            'waiting': 'Waiting for players...',
            'dealing': 'Dealing...',
            'bidding': 'Bidding',
            'trump_selection': 'Select Trump',
            'playing': 'Playing',
            'scoring': 'Scoring...',
            'finished': 'Game Over'
        };

        if (elements.gamePhase) {
            elements.gamePhase.textContent = phaseNames[gameState.phase] || gameState.phase;
        }

        // Current turn
        if (elements.currentTurn) {
            if (gameState.current_turn && gameState.players) {
                const player = gameState.players[gameState.current_turn];
                if (player) {
                    const isMe = gameState.current_turn === myPosition;
                    elements.currentTurn.textContent = isMe ? 'Your turn!' : `${player.username}'s turn`;
                    elements.currentTurn.classList.toggle('my-turn', isMe);
                }
            } else {
                elements.currentTurn.textContent = '';
            }
        }
    }

    function updateTrumpDisplay() {
        const trumpDisplay = document.getElementById('trump-display');
        if (trumpDisplay) {
            if (gameState.trump_suit !== undefined && gameState.trump_suit !== null) {
                trumpDisplay.innerHTML = `
                    <div class="trump-label">TRUMP</div>
                    <div class="trump-domino">
                        <div class="trump-pip" data-pips="${gameState.trump_suit}"></div>
                    </div>
                    <div class="trump-name">${suitNames[gameState.trump_suit]}</div>
                `;
                trumpDisplay.style.display = 'block';
            } else {
                trumpDisplay.style.display = 'none';
            }
        }
    }

    function updateScores() {
        if (elements.team1Marks) elements.team1Marks.textContent = gameState.team1_marks || 0;
        if (elements.team2Marks) elements.team2Marks.textContent = gameState.team2_marks || 0;
        if (elements.team1Points) elements.team1Points.textContent = gameState.team1_hand_points || 0;
        if (elements.team2Points) elements.team2Points.textContent = gameState.team2_hand_points || 0;
    }

    function updatePlayers() {
        const positions = ['north', 'south', 'east', 'west'];

        positions.forEach(pos => {
            const playerArea = document.getElementById(`player-${pos}`);
            const nameEl = document.getElementById(`${pos}-name`);
            const handEl = document.getElementById(`${pos}-hand`);
            const bidEl = document.getElementById(`${pos}-bid`);

            if (!playerArea) return;

            const player = gameState.players?.[pos];

            if (player) {
                if (nameEl) nameEl.textContent = player.username;

                // Show hand for other players (face down)
                if (handEl && pos !== myPosition && !isSpectator) {
                    handEl.innerHTML = '';
                    const count = player.hand_count || 0;
                    for (let i = 0; i < count; i++) {
                        const back = document.createElement('div');
                        back.className = 'domino-back';
                        handEl.appendChild(back);
                    }
                } else if (handEl && isSpectator && player.hand) {
                    handEl.innerHTML = '';
                    player.hand.forEach(domino => {
                        handEl.appendChild(createDominoElement(domino, false, true));
                    });
                }

                // Show bid status
                if (bidEl) {
                    if (player.current_bid) {
                        bidEl.textContent = player.current_bid;
                        bidEl.className = 'player-bid has-bid';
                    } else if (player.has_passed) {
                        bidEl.textContent = 'Pass';
                        bidEl.className = 'player-bid passed';
                    } else {
                        bidEl.textContent = '';
                        bidEl.className = 'player-bid';
                    }
                }

                // Highlight current turn
                playerArea.classList.toggle('current-turn', gameState.current_turn === pos);
                playerArea.classList.toggle('is-me', pos === myPosition);
            } else {
                if (nameEl) nameEl.textContent = 'Waiting...';
                if (handEl) handEl.innerHTML = '';
                if (bidEl) {
                    bidEl.textContent = '';
                    bidEl.className = 'player-bid';
                }
                playerArea.classList.remove('current-turn', 'is-me');
            }
        });
    }

    function updatePanels() {
        // Hide all action panels first
        if (elements.biddingPanel) elements.biddingPanel.style.display = 'none';
        if (elements.trumpPanel) elements.trumpPanel.style.display = 'none';
        if (elements.waitingPanel) elements.waitingPanel.style.display = 'none';
        if (elements.gameOverPanel) elements.gameOverPanel.style.display = 'none';

        if (isSpectator) {
            if (elements.myHandContainer) elements.myHandContainer.style.display = 'none';
            return;
        }

        if (elements.myHandContainer) elements.myHandContainer.style.display = 'flex';

        console.log('Phase:', gameState.phase, 'Current turn:', gameState.current_turn, 'My position:', myPosition);

        switch (gameState.phase) {
            case 'waiting':
                showWaitingPanel();
                break;
            case 'bidding':
                // Always show bidding panel during bidding phase, highlight when it's your turn
                showBiddingPanel();
                break;
            case 'trump_selection':
                if (gameState.high_bidder === myPosition) {
                    showTrumpPanel();
                }
                break;
            case 'playing':
                // No special panel
                break;
            case 'finished':
                showGameOver();
                break;
        }
    }

    function showWaitingPanel() {
        if (!elements.waitingPanel) return;
        elements.waitingPanel.style.display = 'flex';

        const positions = ['north', 'south', 'east', 'west'];
        let html = '';
        let filledCount = 0;

        positions.forEach(pos => {
            const player = gameState.players?.[pos];
            if (player) {
                html += `<div class="player-slot filled">${positionNames[pos]}: ${player.username}</div>`;
                filledCount++;
            } else {
                html += `<div class="player-slot empty">${positionNames[pos]}: Empty</div>`;
            }
        });

        if (elements.playersStatus) elements.playersStatus.innerHTML = html;

        if (elements.waitingMessage) {
            elements.waitingMessage.textContent = filledCount >= 4 ?
                'Ready to start!' : `Waiting for players (${filledCount}/4)...`;
        }

        if (elements.startGameBtn) {
            elements.startGameBtn.style.display = filledCount >= 4 ? 'block' : 'none';
        }

        // Show "Fill with Bots" button when there are empty slots
        if (elements.addBotsBtn) {
            elements.addBotsBtn.style.display = filledCount < 4 ? 'block' : 'none';
        }
    }

    function showBiddingPanel() {
        if (!elements.biddingPanel) return;
        elements.biddingPanel.style.display = 'flex';

        const highBid = gameState.high_bid || 0;
        const isMyTurn = gameState.current_turn === myPosition;

        if (elements.highBidDisplay) {
            elements.highBidDisplay.textContent = highBid > 0 ? highBid : 'None';
        }

        // Update bid buttons
        document.querySelectorAll('.bid-btn').forEach(btn => {
            const bid = parseInt(btn.dataset.bid);
            const disabled = !isMyTurn || bid <= highBid;
            btn.disabled = disabled;
            btn.classList.toggle('available', !disabled);
        });

        // Update pass button
        const passBtn = document.getElementById('pass-btn');
        if (passBtn) {
            passBtn.disabled = !isMyTurn;
            passBtn.classList.toggle('available', isMyTurn);
        }

        // Show whose turn it is
        const turnIndicator = document.getElementById('bid-turn-indicator');
        if (turnIndicator) {
            if (isMyTurn) {
                turnIndicator.textContent = 'Your turn to bid!';
                turnIndicator.className = 'turn-indicator my-turn';
            } else if (gameState.current_turn && gameState.players) {
                const player = gameState.players[gameState.current_turn];
                turnIndicator.textContent = player ? `${player.username}'s turn` : 'Waiting...';
                turnIndicator.className = 'turn-indicator';
            }
        }
    }

    function showTrumpPanel() {
        if (!elements.trumpPanel) return;
        elements.trumpPanel.style.display = 'flex';
        if (elements.winningBid) {
            elements.winningBid.textContent = gameState.high_bid;
        }
    }

    function showGameOver(winner) {
        if (!elements.gameOverPanel) return;
        elements.gameOverPanel.style.display = 'flex';

        const winnerTeam = winner || (gameState.team1_marks >= 7 ? 1 : 2);
        const winnerMsg = document.getElementById('winner-message');
        if (winnerMsg) {
            winnerMsg.textContent = `Team ${winnerTeam} Wins!`;
        }

        const finalTeam1 = document.getElementById('final-team1');
        const finalTeam2 = document.getElementById('final-team2');
        if (finalTeam1) finalTeam1.textContent = gameState.team1_marks;
        if (finalTeam2) finalTeam2.textContent = gameState.team2_marks;
    }

    // Domino Rendering
    function createDominoElement(domino, clickable = true, small = false) {
        const div = document.createElement('div');
        div.className = 'domino' + (small ? ' small' : '');
        div.dataset.id = domino.id;

        if (domino.count_value > 0) {
            div.classList.add('count');
        }

        // Create left half (high)
        const leftHalf = document.createElement('div');
        leftHalf.className = 'domino-half';
        leftHalf.dataset.pips = domino.high;
        renderPips(leftHalf, domino.high);

        // Divider
        const divider = document.createElement('div');
        divider.className = 'domino-divider';

        // Create right half (low)
        const rightHalf = document.createElement('div');
        rightHalf.className = 'domino-half';
        rightHalf.dataset.pips = domino.low;
        renderPips(rightHalf, domino.low);

        div.appendChild(leftHalf);
        div.appendChild(divider);
        div.appendChild(rightHalf);

        if (clickable) {
            div.addEventListener('click', () => handleDominoClick(domino));
        }

        return div;
    }

    function renderPips(container, count) {
        // Create a 3x3 grid for pip positions
        const positions = getPipPositions(count);
        for (let i = 0; i < 9; i++) {
            const pip = document.createElement('div');
            pip.className = 'pip' + (positions.includes(i) ? ' visible' : '');
            container.appendChild(pip);
        }
    }

    function getPipPositions(count) {
        // Positions in a 3x3 grid: 0 1 2 / 3 4 5 / 6 7 8
        const layouts = {
            0: [],
            1: [4],
            2: [0, 8],
            3: [0, 4, 8],
            4: [0, 2, 6, 8],
            5: [0, 2, 4, 6, 8],
            6: [0, 2, 3, 5, 6, 8]
        };
        return layouts[count] || [];
    }

    function renderMyHand() {
        if (!elements.myHand) return;

        if (!myPosition || !gameState.players || !gameState.players[myPosition]) {
            elements.myHand.innerHTML = '<div class="hand-placeholder">Waiting for cards...</div>';
            return;
        }

        const hand = gameState.players[myPosition].hand;
        if (!hand || hand.length === 0) {
            elements.myHand.innerHTML = '<div class="hand-placeholder">No dominoes</div>';
            return;
        }

        elements.myHand.innerHTML = '';

        const isMyTurn = gameState.phase === 'playing' && gameState.current_turn === myPosition;
        const leadSuit = gameState.lead_suit;

        hand.forEach(domino => {
            const el = createDominoElement(domino, true);

            if (gameState.phase === 'playing') {
                if (isMyTurn) {
                    const canPlay = !leadSuit || dominoBelongsToSuit(domino, leadSuit) ||
                        !hand.some(d => dominoBelongsToSuit(d, leadSuit));

                    el.classList.toggle('playable', canPlay);
                    el.classList.toggle('disabled', !canPlay);
                }
            }

            elements.myHand.appendChild(el);
        });
    }

    function dominoBelongsToSuit(domino, suit) {
        return domino.high === suit || domino.low === suit;
    }

    function handleDominoClick(domino) {
        if (gameState.phase !== 'playing') {
            showToast('Wait for play phase', 'error');
            return;
        }
        if (gameState.current_turn !== myPosition) {
            showToast('Not your turn!', 'error');
            return;
        }

        const hand = gameState.players[myPosition].hand;
        const leadSuit = gameState.lead_suit;

        if (leadSuit !== null && leadSuit !== undefined) {
            const canFollowSuit = hand.some(d => dominoBelongsToSuit(d, leadSuit));
            if (canFollowSuit && !dominoBelongsToSuit(domino, leadSuit)) {
                showToast(`Must follow ${suitNames[leadSuit]}!`, 'error');
                return;
            }
        }

        console.log('Playing domino:', domino.id);
        socket.emit('play_domino', { game_id: gameId, domino_id: domino.id });
    }

    function renderCurrentTrick() {
        clearPlayedDominoes();

        if (!gameState.current_trick) return;

        gameState.current_trick.forEach(([pos, domino]) => {
            renderPlayedDomino(pos, domino.id, domino);
        });
    }

    function renderPlayedDomino(position, dominoId, dominoData = null) {
        const container = document.getElementById(`played-${position}`);
        if (!container) return;

        const domino = dominoData || parseDominoId(dominoId);
        const el = createDominoElement(domino, false);
        container.innerHTML = '';
        container.appendChild(el);
    }

    function parseDominoId(id) {
        const [high, low] = id.split('-').map(Number);
        return { id, high, low, count_value: getCountValue(high, low) };
    }

    function getCountValue(high, low) {
        const counts = { '5-0': 5, '4-1': 5, '3-2': 5, '6-4': 10, '5-5': 10 };
        return counts[`${high}-${low}`] || 0;
    }

    function clearPlayedDominoes() {
        ['north', 'south', 'east', 'west'].forEach(pos => {
            const container = document.getElementById(`played-${pos}`);
            if (container) container.innerHTML = '';
        });
    }

    // Chat
    function sendChatMessage() {
        const input = document.getElementById('chat-input');
        if (!input) return;

        const message = input.value.trim();
        if (!message) return;

        socket.emit('chat_message', { game_id: gameId, message: message });
        input.value = '';
    }

    function appendChatMessage(msg) {
        const container = document.getElementById('chat-messages');
        if (!container) return;

        const div = document.createElement('div');
        div.className = 'chat-message';

        const username = document.createElement('span');
        username.className = 'chat-username' + (msg.is_spectator ? ' spectator' : '');
        username.textContent = msg.username + ': ';

        const text = document.createElement('span');
        text.className = 'chat-text';
        text.textContent = msg.message;

        div.appendChild(username);
        div.appendChild(text);

        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    // Toast notifications
    function showToast(message, type = '') {
        const toast = document.getElementById('toast');
        if (!toast) return;

        toast.textContent = message;
        toast.className = 'toast show ' + type;

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
