/**
 * Real-time updates for authenticated pages.
 * - Chat: 1s JSON polling + instant send via API (text, images, videos, location)
 * - Other pages: soft reload every 5s unless user is typing
 * - Pings /api/ping/ every 30s to keep the "active now" status fresh
 */
(function () {
    const INTERVAL_MS = 5000;
    const CHAT_INTERVAL_MS = 1000;
    const PING_INTERVAL_MS = 30000;

    const chatEl = document.querySelector('[data-chat-match-id]');
    const chatMatchId = chatEl ? chatEl.dataset.chatMatchId : document.body.dataset.chatMatchId;
    const currentUserId = parseInt(document.body.dataset.userId || '0', 10);
    const autoRefresh = document.body.dataset.autoRefresh !== 'off';

    let paused = false;
    let lastMessageId = 0;
    let chatInitialized = false;
    let sending = false;

    function setPaused(value) {
        paused = value;
    }

    document.addEventListener('visibilitychange', function () {
        setPaused(document.hidden);
    });

    document.querySelectorAll('input, textarea, select').forEach(function (el) {
        el.addEventListener('focus', function () {
            if (!chatMatchId) setPaused(true);
        });
        el.addEventListener('blur', function () {
            if (!chatMatchId) setPaused(false);
        });
    });

    function getCsrfToken() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input) return input.value;
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : '';
    }

    // ── Online ping ──────────────────────────────────────────────────────────
    function pingOnline() {
        fetch('/api/ping/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': getCsrfToken(), Accept: 'application/json' },
        }).catch(function () {});
    }

    // ── Nav unread badge ─────────────────────────────────────────────────────
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

    // ── Dashboard stats ──────────────────────────────────────────────────────
    function pollDashboardStats() {
        return fetch('/api/dashboard/stats/', {
            credentials: 'same-origin',
            headers: { Accept: 'application/json' },
        })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                if (!data) return;
                updateNavUnread(data.unread_messages);
                ['matches_count', 'likes_received', 'likes_given', 'unread_messages'].forEach(function (key) {
                    document.querySelectorAll('[data-stat="' + key + '"]').forEach(function (el) {
                        el.textContent = data[key];
                    });
                });
            })
            .catch(function () {});
    }

    // ── HTML helpers ─────────────────────────────────────────────────────────
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function escapeAttr(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function formatTime(isoString) {
        try {
            return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch (e) { return ''; }
    }

    // ── Location message detection ───────────────────────────────────────────
    function isLocationMessage(content) {
        return content && content.startsWith('\uD83D\uDCCD ');
    }

    function renderLocationContent(content, isMine) {
        const url = content.slice(2).trim(); // strip the 📍 + space
        const linkClass = isMine ? 'text-white' : '';
        return '\uD83D\uDCCD <a href="' + escapeAttr(url) + '" target="_blank" rel="noopener" class="' + linkClass + '">View location on map</a>';
    }

    // ── Message rendering ────────────────────────────────────────────────────
    function renderMessageBody(msg, isMine) {
        let body = '';
        if (msg.media_url) {
            if (msg.media_type === 'image') {
                body += '<img src="' + escapeAttr(msg.media_url) + '" class="img-fluid rounded mb-1 chat-media" style="max-height:240px;" alt="Shared image">';
            } else if (msg.media_type === 'video') {
                body += '<video src="' + escapeAttr(msg.media_url) + '" class="rounded mb-1 chat-media" controls style="max-width:100%;max-height:240px;"></video>';
            }
        }
        if (msg.content) {
            if (isLocationMessage(msg.content)) {
                body += '<p class="mb-1">' + renderLocationContent(msg.content, isMine) + '</p>';
            } else {
                body += '<p class="mb-1">' + escapeHtml(msg.content) + '</p>';
            }
        }
        return body;
    }

    function buildMessageHtml(msg) {
        const isMine = msg.sender && msg.sender.id === currentUserId;
        const align = isMine ? 'justify-content-end' : 'justify-content-start';
        const bubbleClass = isMine ? 'bg-primary text-white' : 'bg-light';
        const timeClass = isMine ? 'text-white-50' : 'text-muted';
        return (
            '<div class="d-flex ' + align + ' mb-2" data-message-id="' + msg.id + '">' +
            '<div class="rounded-3 px-3 py-2 ' + bubbleClass + '" style="max-width:72%;">' +
            renderMessageBody(msg, isMine) +
            '<small class="' + timeClass + '">' + formatTime(msg.created_at) + '</small>' +
            '</div></div>'
        );
    }

    function scrollChatToBottom(container, force) {
        const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 80;
        if (force || atBottom) container.scrollTop = container.scrollHeight;
    }

    function syncLastMessageId(container) {
        const nodes = container.querySelectorAll('[data-message-id]');
        if (nodes.length) {
            const lastId = parseInt(nodes[nodes.length - 1].dataset.messageId, 10);
            if (lastId > lastMessageId) lastMessageId = lastId;
        }
    }

    function renderChatMessages(messages, incremental) {
        const container = document.getElementById('chat-messages');
        if (!container) return;

        if (!messages.length && !incremental) {
            container.innerHTML = '<div class="text-center text-muted py-5"><p>No messages yet. Say hello!</p></div>';
            lastMessageId = 0;
            return;
        }

        if (incremental) {
            messages.forEach(function (msg) {
                if (container.querySelector('[data-message-id="' + msg.id + '"]')) return;
                const isMine = msg.sender && msg.sender.id === currentUserId;
                container.insertAdjacentHTML('beforeend', buildMessageHtml(msg));
                if (msg.id > lastMessageId) lastMessageId = msg.id;
            });
            scrollChatToBottom(container, true);
            return;
        }

        const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 80;
        container.innerHTML = messages.map(function (m) { return buildMessageHtml(m); }).join('');
        messages.forEach(function (msg) { if (msg.id > lastMessageId) lastMessageId = msg.id; });
        scrollChatToBottom(container, atBottom);
    }

    function appendOptimisticMessage(msg) {
        const container = document.getElementById('chat-messages');
        if (!container) return;
        const empty = container.querySelector('.text-center.text-muted');
        if (empty) container.innerHTML = '';
        if (container.querySelector('[data-message-id="' + msg.id + '"]')) return;
        container.insertAdjacentHTML('beforeend', buildMessageHtml(msg));
        scrollChatToBottom(container, true);
    }

    // ── Chat polling ─────────────────────────────────────────────────────────
    function pollChat(incremental) {
        if (!chatMatchId) return Promise.resolve();
        let url = '/api/chat/' + chatMatchId + '/';
        if (incremental && lastMessageId > 0) url += '?after=' + lastMessageId;
        return fetch(url, { credentials: 'same-origin', headers: { Accept: 'application/json' } })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                if (data && data.messages) renderChatMessages(data.messages, !!data.incremental);
            })
            .catch(function () {});
    }

    // ── Chat send ────────────────────────────────────────────────────────────
    function clearMediaPreview() {
        const preview = document.getElementById('chat-media-preview');
        const mediaInput = document.getElementById('chat-media-input');
        if (preview) { preview.textContent = ''; preview.classList.add('d-none'); }
        if (mediaInput) mediaInput.value = '';
    }

    function sendChatMessage(event) {
        if (event) event.preventDefault();
        if (!chatMatchId || sending) return;

        const contentInput = document.getElementById('chat-content-input');
        const mediaInput = document.getElementById('chat-media-input');
        const sendBtn = document.getElementById('chat-send-btn');
        const content = contentInput ? contentInput.value.trim() : '';
        const mediaFile = mediaInput && mediaInput.files.length ? mediaInput.files[0] : null;

        if (!content && !mediaFile) return;

        sending = true;
        if (sendBtn) sendBtn.disabled = true;

        const formData = new FormData();
        if (content) formData.append('content', content);
        if (mediaFile) formData.append('media', mediaFile);

        fetch('/api/chat/' + chatMatchId + '/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { Accept: 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: formData,
        })
            .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
            .then(function (result) {
                if (!result.ok) {
                    alert((result.data && result.data.error) || 'Failed to send message.');
                    return;
                }
                if (contentInput) contentInput.value = '';
                clearMediaPreview();
                appendOptimisticMessage(result.data);
                if (result.data.id > lastMessageId) lastMessageId = result.data.id;
                pollDashboardStats();
            })
            .catch(function () { alert('Failed to send. Please try again.'); })
            .finally(function () {
                sending = false;
                if (sendBtn) sendBtn.disabled = false;
                if (contentInput) contentInput.focus();
            });
    }

    function initChatForm() {
        const form = document.getElementById('chat-form');
        const attachBtn = document.getElementById('chat-attach-btn');
        const mediaInput = document.getElementById('chat-media-input');
        const preview = document.getElementById('chat-media-preview');
        const contentInput = document.getElementById('chat-content-input');

        if (form) form.addEventListener('submit', sendChatMessage);

        if (attachBtn && mediaInput) {
            attachBtn.addEventListener('click', function () { mediaInput.click(); });
            mediaInput.addEventListener('change', function () {
                if (!preview) return;
                if (mediaInput.files.length) {
                    preview.textContent = 'Attached: ' + mediaInput.files[0].name;
                    preview.classList.remove('d-none');
                } else {
                    preview.textContent = '';
                    preview.classList.add('d-none');
                }
            });
        }

        if (contentInput) {
            contentInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendChatMessage();
                }
            });
        }
    }

    // ── Main tick ────────────────────────────────────────────────────────────
    function tick() {
        if (paused) return;
        pollDashboardStats();
        if (chatMatchId) {
            pollChat(chatInitialized);
        } else if (autoRefresh) {
            window.location.reload();
        }
    }

    if (chatMatchId || autoRefresh) {
        setTimeout(function () {
            pollDashboardStats();
            pingOnline();
            if (chatMatchId) {
                const container = document.getElementById('chat-messages');
                if (container) syncLastMessageId(container);
                initChatForm();
                pollChat(false).then(function () { chatInitialized = true; });
            }
        }, 200);

        setInterval(tick, chatMatchId ? CHAT_INTERVAL_MS : INTERVAL_MS);
        setInterval(pingOnline, PING_INTERVAL_MS);
    }
})();
