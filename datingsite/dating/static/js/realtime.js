/**
 * Real-time updates every 5 seconds for authenticated pages.
 * - Chat: polls JSON API (no full page reload)
 * - Other pages: soft reload unless user is typing
 */
(function () {
    const INTERVAL_MS = 5000;
    const chatEl = document.querySelector('[data-chat-match-id]');
    const chatMatchId = chatEl ? chatEl.dataset.chatMatchId : document.body.dataset.chatMatchId;
    const currentUserId = parseInt(document.body.dataset.userId || '0', 10);
    const autoRefresh = document.body.dataset.autoRefresh !== 'off';

    let paused = false;
    let lastMessageCount = 0;

    function setPaused(value) {
        paused = value;
    }

    document.addEventListener('visibilitychange', function () {
        setPaused(document.hidden);
    });

    document.querySelectorAll('input, textarea, select').forEach(function (el) {
        el.addEventListener('focus', function () {
            setPaused(true);
        });
        el.addEventListener('blur', function () {
            setPaused(false);
        });
    });

    function updateLiveIndicator() {
        const el = document.getElementById('live-indicator');
        if (el) {
            el.title = 'Last sync: ' + new Date().toLocaleTimeString();
        }
    }

    function updateNavUnread(count) {
        const badge = document.getElementById('nav-unread-badge');
        if (!badge) return;
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.classList.remove('d-none');
        } else {
            badge.classList.add('d-none');
        }
    }

    function pollDashboardStats() {
        return fetch('/api/dashboard/stats/', { credentials: 'same-origin', headers: { Accept: 'application/json' } })
            .then(function (r) {
                if (!r.ok) return null;
                return r.json();
            })
            .then(function (data) {
                if (!data) return;
                updateNavUnread(data.unread_messages);
                document.querySelectorAll('[data-stat="matches_count"]').forEach(function (el) {
                    el.textContent = data.matches_count;
                });
                document.querySelectorAll('[data-stat="likes_received"]').forEach(function (el) {
                    el.textContent = data.likes_received;
                });
                document.querySelectorAll('[data-stat="likes_given"]').forEach(function (el) {
                    el.textContent = data.likes_given;
                });
                document.querySelectorAll('[data-stat="unread_messages"]').forEach(function (el) {
                    el.textContent = data.unread_messages;
                });
            })
            .catch(function () {});
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatTime(isoString) {
        try {
            const d = new Date(isoString);
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return '';
        }
    }

    function renderChatMessages(messages) {
        const container = document.getElementById('chat-messages');
        if (!container) return;

        if (!messages.length) {
            container.innerHTML =
                '<div class="text-center text-muted py-5"><p>No messages yet. Start the conversation!</p></div>';
            return;
        }

        const html = messages
            .map(function (msg) {
                const isMine = msg.sender && msg.sender.id === currentUserId;
                const align = isMine ? 'justify-content-end' : 'justify-content-start';
                const cardClass = isMine ? 'bg-primary text-white' : 'bg-light';
                const timeClass = isMine ? 'text-white-50' : 'text-muted';
                return (
                    '<div class="d-flex ' +
                    align +
                    ' mb-3" data-message-id="' +
                    msg.id +
                    '">' +
                    '<div class="card ' +
                    cardClass +
                    '" style="max-width: 70%;">' +
                    '<div class="card-body py-2 px-3">' +
                    '<p class="mb-1">' +
                    escapeHtml(msg.content) +
                    '</p>' +
                    '<small class="' +
                    timeClass +
                    '">' +
                    formatTime(msg.created_at) +
                    '</small></div></div></div>'
                );
            })
            .join('');

        const atBottom =
            container.scrollHeight - container.scrollTop - container.clientHeight < 80;

        container.innerHTML = html;

        if (atBottom || messages.length > lastMessageCount) {
            container.scrollTop = container.scrollHeight;
        }
        lastMessageCount = messages.length;
    }

    function pollChat() {
        if (!chatMatchId) return Promise.resolve();
        return fetch('/api/chat/' + chatMatchId + '/', {
            credentials: 'same-origin',
            headers: { Accept: 'application/json' },
        })
            .then(function (r) {
                if (!r.ok) return null;
                return r.json();
            })
            .then(function (data) {
                if (data && data.messages) {
                    renderChatMessages(data.messages);
                }
            })
            .catch(function () {});
    }

    function tick() {
        if (paused) return;
        updateLiveIndicator();
        pollDashboardStats();

        if (chatMatchId) {
            pollChat();
        } else if (autoRefresh) {
            window.location.reload();
        }
    }

    if (chatMatchId || autoRefresh) {
        setTimeout(function () {
            pollDashboardStats();
            if (chatMatchId) {
                const container = document.getElementById('chat-messages');
                if (container) {
                    lastMessageCount = container.querySelectorAll('[data-message-id]').length;
                }
                pollChat();
            }
        }, 500);

        setInterval(tick, INTERVAL_MS);
    }
})();
