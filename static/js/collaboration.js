/**
 * Widget Collaboration JavaScript
 * Handles real-time multi-user editing with cursor sync and chat
 */

let collaborationSession = null;
let socket = null;
let localUser = null;
let participants = [];
let remoteCursors = {};
let isCollaborating = false;

// User colors for cursor identification
const USER_COLORS = [
    '#FF5733', '#33FF57', '#3357FF', '#FF33F5',
    '#33FFF5', '#F5FF33', '#FF8C33', '#8C33FF'
];

/**
 * Initialize collaboration system
 */
function initializeCollaboration() {
    localUser = {
        id: 'user_' + Math.random().toString(36).substr(2, 9),
        name: 'User_' + Math.floor(Math.random() * 1000)
    };

    // Check if there's an active session to rejoin
    checkActiveSession();
}

/**
 * Check for active collaboration session
 */
function checkActiveSession() {
    const widgetId = window.currentWidgetId || 'widget_demo';

    fetch(`/api/widgets/${widgetId}/collaborate/active`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.sessions && data.sessions.length > 0) {
                // Show rejoin option
                showRejoinPrompt(data.sessions[0]);
            }
        })
        .catch(error => {
            console.log('No active session found');
        });
}

/**
 * Start collaboration
 */
function startCollaboration() {
    const modal = new bootstrap.Modal(document.getElementById('collaborationModal'));
    modal.show();
}

/**
 * Create collaboration session
 */
function createCollaborationSession() {
    const duration = parseInt(document.getElementById('sessionDuration').value);
    const widgetId = window.currentWidgetId || 'widget_demo';

    fetch(`/api/widgets/${widgetId}/collaborate/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration_hours: duration })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            collaborationSession = data.session;

            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('collaborationModal')).hide();

            // Join the session
            joinSession(collaborationSession.session_id);
        } else {
            alert('Error creating session: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error creating collaboration session');
    });
}

/**
 * Join collaboration session
 */
function joinSession(sessionId) {
    const widgetId = window.currentWidgetId || 'widget_demo';

    // Initialize Socket.IO connection if not already connected
    if (!socket) {
        socket = io();
        setupSocketHandlers();
    }

    // Join session via API
    fetch(`/api/widgets/${widgetId}/collaborate/${sessionId}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ socket_id: socket.id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            collaborationSession = data.session;
            isCollaborating = true;

            // Emit join event via WebSocket
            socket.emit('collaboration:join', {
                session_id: sessionId,
                widget_id: widgetId,
                user: localUser
            });

            // Update UI
            activateCollaborationMode();
        } else {
            alert('Error joining session: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error joining collaboration session');
    });
}

/**
 * Leave collaboration
 */
function leaveCollaboration() {
    if (!collaborationSession) return;

    const widgetId = window.currentWidgetId || 'widget_demo';

    // Emit leave event
    if (socket) {
        socket.emit('collaboration:leave', {
            session_id: collaborationSession.session_id,
            widget_id: widgetId
        });
    }

    // API call
    fetch(`/api/widgets/${widgetId}/collaborate/${collaborationSession.session_id}/leave`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        deactivateCollaborationMode();
    })
    .catch(error => {
        console.error('Error:', error);
        deactivateCollaborationMode();
    });
}

/**
 * Activate collaboration mode UI
 */
function activateCollaborationMode() {
    // Hide collaborate button, show status
    document.getElementById('collaborateBtn').classList.add('d-none');
    document.getElementById('collaborationStatus').classList.remove('d-none');

    // Show collaboration panel
    document.getElementById('collaborationPanel').classList.remove('d-none');

    // Update participants
    updateParticipantsList();

    // Enable cursor tracking
    enableCursorTracking();

    // Show notification
    showNotification('Collaboration session started', 'success');
}

/**
 * Deactivate collaboration mode UI
 */
function deactivateCollaborationMode() {
    isCollaborating = false;
    collaborationSession = null;

    // Show collaborate button, hide status
    document.getElementById('collaborateBtn').classList.remove('d-none');
    document.getElementById('collaborationStatus').classList.add('d-none');

    // Hide collaboration panel
    document.getElementById('collaborationPanel').classList.add('d-none');

    // Clear remote cursors
    clearRemoteCursors();

    // Disable cursor tracking
    disableCursorTracking();

    showNotification('Left collaboration session', 'info');
}

/**
 * Setup Socket.IO event handlers
 */
function setupSocketHandlers() {
    // User joined
    socket.on('collaboration:user_joined', function(data) {
        console.log('User joined:', data);
        addParticipant(data);
        showNotification(`${data.user_id} joined the session`, 'info');
    });

    // User left
    socket.on('collaboration:user_left', function(data) {
        console.log('User left:', data);
        removeParticipant(data.user_id);
        removeRemoteCursor(data.user_id);
        showNotification(`${data.user_id} left the session`, 'info');
    });

    // Session state (initial load)
    socket.on('collaboration:session_state', function(data) {
        console.log('Session state:', data);
        participants = data.session.participants;
        updateParticipantsList();
    });

    // Cursor update
    socket.on('collaboration:cursor_update', function(data) {
        updateRemoteCursor(data.user_id, data.cursor_position, getParticipantColor(data.user_id));
    });

    // Remote operation
    socket.on('collaboration:operation', function(data) {
        applyRemoteOperation(data.operation, data.user_id);
    });

    // Lock acquired
    socket.on('collaboration:lock_acquired', function(data) {
        showLockNotification(data.user_id, data.editor, data.line_range);
    });

    // Conflict
    socket.on('collaboration:conflict', function(data) {
        showConflictNotification(data.message, data.locked_by);
    });

    // Chat message
    socket.on('collaboration:chat_message', function(data) {
        addChatMessage(data.user_id, data.message, data.timestamp);
    });
}

/**
 * Update participants list
 */
function updateParticipantsList() {
    const list = document.getElementById('participantsList');
    const avatars = document.getElementById('collaborationAvatars');
    const count = document.getElementById('participantCount');

    if (!collaborationSession || !collaborationSession.participants) return;

    let listHtml = '';
    let avatarsHtml = '';

    collaborationSession.participants.forEach((p, index) => {
        const color = p.color || USER_COLORS[index % USER_COLORS.length];
        const isActive = true; // You can track activity status

        listHtml += `
            <div class="participant-item">
                <div class="participant-avatar" style="background-color: ${color};">
                    ${p.user_id.charAt(0).toUpperCase()}
                </div>
                <div class="participant-info">
                    <div class="participant-name">${p.user_id}</div>
                    <div class="participant-status ${isActive ? 'active' : 'idle'}">
                        <i class="fas fa-circle"></i>
                        ${isActive ? 'Active' : 'Idle'}
                    </div>
                </div>
            </div>
        `;

        // Small avatar for header
        avatarsHtml += `
            <div class="collab-avatar-sm" style="background-color: ${color};" title="${p.user_id}">
                ${p.user_id.charAt(0).toUpperCase()}
            </div>
        `;
    });

    list.innerHTML = listHtml;
    avatars.innerHTML = avatarsHtml;
    count.textContent = collaborationSession.participants.length;
}

/**
 * Add participant
 */
function addParticipant(data) {
    if (!collaborationSession) return;

    const exists = collaborationSession.participants.find(p => p.user_id === data.user_id);
    if (!exists) {
        collaborationSession.participants.push({
            user_id: data.user_id,
            color: data.color,
            joined_at: data.timestamp
        });
        updateParticipantsList();
    }
}

/**
 * Remove participant
 */
function removeParticipant(userId) {
    if (!collaborationSession) return;

    collaborationSession.participants = collaborationSession.participants.filter(
        p => p.user_id !== userId
    );
    updateParticipantsList();
}

/**
 * Get participant color
 */
function getParticipantColor(userId) {
    if (!collaborationSession) return USER_COLORS[0];

    const participant = collaborationSession.participants.find(p => p.user_id === userId);
    return participant ? participant.color : USER_COLORS[0];
}

/**
 * Enable cursor tracking
 */
function enableCursorTracking() {
    const canvas = document.getElementById('widgetCanvas');
    if (!canvas) return;

    canvas.addEventListener('mousemove', handleCursorMove);
    canvas.addEventListener('click', handleCursorClick);
}

/**
 * Disable cursor tracking
 */
function disableCursorTracking() {
    const canvas = document.getElementById('widgetCanvas');
    if (!canvas) return;

    canvas.removeEventListener('mousemove', handleCursorMove);
    canvas.removeEventListener('click', handleCursorClick);
}

/**
 * Handle cursor movement
 */
let cursorMoveThrottle = null;
function handleCursorMove(e) {
    if (!isCollaborating || !socket) return;

    // Throttle cursor updates (max 10 per second)
    if (cursorMoveThrottle) return;

    cursorMoveThrottle = setTimeout(() => {
        cursorMoveThrottle = null;
    }, 100);

    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    socket.emit('collaboration:cursor_move', {
        session_id: collaborationSession.session_id,
        cursor_position: {
            x: x,
            y: y,
            editor: 'canvas'
        }
    });
}

/**
 * Handle cursor click
 */
function handleCursorClick(e) {
    if (!isCollaborating) return;
    // Can be used for selection sync or other features
}

/**
 * Update remote cursor
 */
function updateRemoteCursor(userId, position, color) {
    if (!position || userId === localUser.id) return;

    let cursor = remoteCursors[userId];

    if (!cursor) {
        // Create new cursor
        cursor = document.createElement('div');
        cursor.className = 'remote-cursor';
        cursor.innerHTML = `
            <div class="cursor-pointer" style="border-color: ${color};"></div>
            <div class="cursor-label" style="background-color: ${color};">${userId}</div>
        `;
        document.getElementById('remoteCursorsContainer').appendChild(cursor);
        remoteCursors[userId] = cursor;
    }

    // Update position
    const canvas = document.getElementById('widgetCanvas');
    if (canvas) {
        const rect = canvas.getBoundingClientRect();
        const x = rect.left + (position.x / 100) * rect.width;
        const y = rect.top + (position.y / 100) * rect.height;

        cursor.style.left = x + 'px';
        cursor.style.top = y + 'px';
        cursor.style.display = 'block';
    }
}

/**
 * Remove remote cursor
 */
function removeRemoteCursor(userId) {
    if (remoteCursors[userId]) {
        remoteCursors[userId].remove();
        delete remoteCursors[userId];
    }
}

/**
 * Clear all remote cursors
 */
function clearRemoteCursors() {
    Object.values(remoteCursors).forEach(cursor => cursor.remove());
    remoteCursors = {};
}

/**
 * Apply remote operation
 */
function applyRemoteOperation(operation, userId) {
    console.log('Remote operation from', userId, ':', operation);

    // Apply the operation to the local state
    // This would integrate with your widget builder's data structure

    // Show brief notification
    showBriefNotification(`${userId} made changes`, 'info');
}

/**
 * Send chat message
 */
function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message || !socket || !collaborationSession) return;

    socket.emit('collaboration:chat', {
        session_id: collaborationSession.session_id,
        message: message
    });

    input.value = '';
}

/**
 * Add chat message
 */
function addChatMessage(userId, message, timestamp) {
    const chatMessages = document.getElementById('chatMessages');
    const isOwnMessage = userId === localUser.name;

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isOwnMessage ? 'own-message' : ''}`;

    const time = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    messageDiv.innerHTML = `
        <div class="message-header">
            <strong>${userId}</strong>
            <span class="message-time">${time}</span>
        </div>
        <div class="message-content">${escapeHtml(message)}</div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Remove empty state if exists
    const emptyState = chatMessages.querySelector('.text-center');
    if (emptyState) emptyState.remove();
}

/**
 * Show lock notification
 */
function showLockNotification(userId, editor, lineRange) {
    showBriefNotification(`${userId} locked ${editor} lines ${lineRange[0]}-${lineRange[1]}`, 'warning');
}

/**
 * Show conflict notification
 */
function showConflictNotification(message, lockedBy) {
    alert(`Conflict: ${message}\nLocked by: ${lockedBy}`);
}

/**
 * Toggle collaboration panel
 */
function toggleCollaborationPanel() {
    const panel = document.getElementById('collaborationPanel');
    panel.classList.toggle('collapsed');
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Simple notification - can be replaced with toast library
    console.log(`[${type.toUpperCase()}] ${message}`);

    // You can integrate with a toast library here
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
}

/**
 * Show brief notification (non-intrusive)
 */
function showBriefNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = 'brief-notification';
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => notification.classList.add('show'), 10);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

/**
 * Utility: Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Handle Enter key in chat
 */
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    // Initialize collaboration
    if (typeof io !== 'undefined') {
        initializeCollaboration();
    }
});
