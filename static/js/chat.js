/* ==========================================================================
   Learnix AI Chat Client Logic
   ========================================================================== */

// Auto scroll on first load
document.addEventListener('DOMContentLoaded', () => {
    // Format historical assistant messages from database
    document.querySelectorAll('.bot-msg-bubble').forEach(bubble => {
        const rawText = bubble.textContent || bubble.innerText;
        bubble.innerHTML = simpleMarkdownParse(rawText);
    });
    scrollChatToBottom();
});

function scrollChatToBottom() {
    const feed = document.getElementById('chatHistoryFeed');
    if (feed) {
        feed.scrollTop = feed.scrollHeight;
    }
}

function sendSuggestedPrompt(text) {
    const input = document.getElementById('chatInputMessage');
    if (input) {
        input.value = text;
        // Trigger submit
        const form = document.getElementById('chatSubmitForm');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
}

function handleChatSubmit(event) {
    event.preventDefault();
    
    const input = document.getElementById('chatInputMessage');
    const messageText = input.value.trim();
    if (!messageText) return;
    
    // Clear Input
    input.value = '';
    
    const container = document.querySelector('.chatbot-workspace-container');
    const subjectId = container.getAttribute('data-subject-id');
    let convId = container.getAttribute('data-conv-id');
    
    // 1. Render User message bubble instantly in UI
    appendUserBubble(messageText);
    
    // Show typing loader and scroll
    const loader = document.getElementById('typingLoader');
    if (loader) {
        // Move loader to bottom of list
        const feed = document.getElementById('chatHistoryFeed');
        feed.appendChild(loader);
        loader.style.display = 'flex';
    }
    scrollChatToBottom();
    
    // API Call
    const payload = {
        subject_id: subjectId ? parseInt(subjectId) : null,
        conversation_id: convId ? parseInt(convId) : null,
        message: messageText
    };
    
    fetch('/api/chat/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('API server returned error code.');
        }
        return response.json();
    })
    .then(data => {
        // Hide loader
        if (loader) loader.style.display = 'none';
        
        if (data.success) {
            // 2. Render Bot message bubble
            appendBotBubble(data.answer, data.source);
            
            // If new conversation was created, update data state
            if (!convId && data.conversation_id) {
                container.setAttribute('data-conv-id', data.conversation_id);
                // Push history state to URL silently without reloading
                const newUrl = `${window.location.pathname}?subject_id=${subjectId}&conv_id=${data.conversation_id}`;
                window.history.pushState({ path: newUrl }, '', newUrl);
                
                // Alert first chat created to student
                showGlobalToast('success', `Started new chat session: "${data.conversation_title}"`);
            }
        } else {
            appendBotBubble(data.answer || '## Response\n\nI prepared a helpful answer — please try rephrasing your question.');
        }
        scrollChatToBottom();
    })
    .catch(err => {
        console.error('Chat sending error:', err);
        if (loader) loader.style.display = 'none';
        appendBotBubble('## Connection Issue\n\nYour message was saved. Please check your network and send again.');
        scrollChatToBottom();
    });
}

function generateQuizFromConversation() {
    const container = document.querySelector('.chatbot-workspace-container');
    if (!container) return;

    const subjectId = container.getAttribute('data-subject-id');
    const convId = container.getAttribute('data-conv-id');

    if (!convId) {
        showGlobalToast('warning', 'Start a conversation about a topic first, then generate a quiz.');
        sendSuggestedPrompt('Explain the key concepts of this subject');
        return;
    }

    const btn = document.getElementById('generateQuizBtn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    }

    const loader = document.getElementById('typingLoader');
    if (loader) {
        const feed = document.getElementById('chatHistoryFeed');
        feed.appendChild(loader);
        loader.style.display = 'flex';
    }
    scrollChatToBottom();

    fetch('/api/chat/generate-quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            conversation_id: parseInt(convId),
            subject_id: subjectId ? parseInt(subjectId) : null
        })
    })
    .then(r => r.json())
    .then(data => {
        if (loader) loader.style.display = 'none';
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-list-check"></i> Generate Quiz';
        }

        if (data.status === 'success') {
            const summary = data.summary || `## Quiz Ready\n\n**Topic:** ${data.topic}\n\n- Easy: ${data.easy_count}\n- Medium: ${data.medium_count}\n- Hard: ${data.hard_count}`;
            appendBotBubble(summary, 'ai');

            if (data.quiz_id) {
                const quizLink = document.createElement('div');
                quizLink.className = 'chat-msg-row msg-bot-row';
                quizLink.innerHTML = `
                    <div class="msg-bubble-wrapper">
                        <a href="/quiz/${data.quiz_id}" class="btn btn-primary" style="margin-top: 0.5rem;">
                            <i class="fas fa-play"></i> Take Quiz (${data.topic})
                        </a>
                    </div>`;
                document.getElementById('chatHistoryFeed').appendChild(quizLink);
            }
            showGlobalToast('success', `Quiz generated: ${data.topic}`);
        } else {
            showGlobalToast('warning', data.message || 'Could not generate quiz yet.');
            appendBotBubble(`## Quiz Generation\n\n${data.message || 'Discuss a topic first, then try again.'}`);
        }
        scrollChatToBottom();
    })
    .catch(err => {
        console.error('Quiz generation error:', err);
        if (loader) loader.style.display = 'none';
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-list-check"></i> Generate Quiz';
        }
        appendBotBubble('## Quiz\n\nI can still help — type **"Generate quiz"** after discussing a topic.');
        scrollChatToBottom();
    });
}

function appendUserBubble(text) {
    const feed = document.getElementById('chatHistoryFeed');
    if (!feed) return;
    
    // Remove welcome prompt on first message
    const welcome = feed.querySelector('.chat-welcome-prompt');
    if (welcome) welcome.remove();
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const row = document.createElement('div');
    row.className = 'chat-msg-row msg-user-row';
    
    row.innerHTML = `
        <div class="msg-bubble-wrapper">
            <div class="msg-bubble">${escapeHtml(text).replace(/\n/g, '<br>')}</div>
            <span class="msg-time">${time}</span>
        </div>
    `;
    
    feed.appendChild(row);
}

function appendBotBubble(text, source) {
    const feed = document.getElementById('chatHistoryFeed');
    if (!feed) return;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const row = document.createElement('div');
    row.className = 'chat-msg-row msg-bot-row';
    
    // Basic Markdown parser for simple elements (bold, lists, headers)
    const parsedText = simpleMarkdownParse(text);
    
    // Source badge HTML
    let sourceBadge = '';
    if (source) {
        if (source === 'knowledge_base') {
            sourceBadge = `<span class="source-badge" style="display: inline-block; margin-bottom: 0.5rem; padding: 0.25rem 0.75rem; border-radius: 999px; background: rgba(99, 102, 241, 0.2); color: #818cf8; font-size: 0.75rem; font-weight: 500;">📚 Knowledge Base</span>`;
        } else if (source === 'ai') {
            sourceBadge = `<span class="source-badge" style="display: inline-block; margin-bottom: 0.5rem; padding: 0.25rem 0.75rem; border-radius: 999px; background: rgba(139, 92, 246, 0.2); color: #a78bfa; font-size: 0.75rem; font-weight: 500;">🤖 AI Generated</span>`;
        }
    }

    row.innerHTML = `
        <div class="msg-bubble-wrapper">
            <div class="msg-bubble bot-msg-bubble">
                ${sourceBadge}
                <div style="margin-top: ${sourceBadge ? '0.25rem' : '0'}">
                    ${parsedText}
                </div>
            </div>
            <span class="msg-time">${time}</span>
        </div>
    `;
    
    feed.appendChild(row);
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/* Premium client-side markdown formatter with tables, code blocks, and list support */
function simpleMarkdownParse(text) {
    if (!text) return "";
    
    // 1. Escape HTML first to prevent injection in bot bubbles
    let html = escapeHtml(text);
    
    // 2. Code blocks: ```lang\ncode\n```
    const codeBlocks = [];
    html = html.replace(/```(\w*)\n([\s\S]*?)\n```/g, function(match, lang, code) {
        const placeholder = `__CODE_BLOCK_PLACEHOLDER_${codeBlocks.length}__`;
        codeBlocks.push({
            lang: lang,
            code: code
        });
        return placeholder;
    });

    // Inline code: `code`
    const inlineCodes = [];
    html = html.replace(/`([^`\n]+)`/g, function(match, code) {
        const placeholder = `__INLINE_CODE_PLACEHOLDER_${inlineCodes.length}__`;
        inlineCodes.push(code);
        return placeholder;
    });

    // 3. Tables
    const lines = html.split('\n');
    let inTable = false;
    let tableHtml = '';
    const processedLines = [];

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        // A markdown table line looks like | Cell 1 | Cell 2 |
        if (line.startsWith('|') && line.endsWith('|')) {
            // Check if it's a separator line like |---|---|
            if (line.replace(/[\s|:-]/g, '') === '') {
                inTable = true;
                continue;
            }

            const cells = line.split('|').slice(1, -1).map(c => c.trim());
            if (!inTable) {
                // Header row
                inTable = true;
                tableHtml = '<div class="table-container"><table class="markdown-table"><thead><tr>';
                cells.forEach(cell => {
                    tableHtml += `<th>${cell}</th>`;
                });
                tableHtml += '</tr></thead><tbody>';
            } else {
                // Body row
                tableHtml += '<tr>';
                cells.forEach(cell => {
                    tableHtml += `<td>${cell}</td>`;
                });
                tableHtml += '</tr>';
            }
        } else {
            if (inTable) {
                tableHtml += '</tbody></table></div>';
                processedLines.push(tableHtml);
                tableHtml = '';
                inTable = false;
            }
            processedLines.push(lines[i]);
        }
    }
    if (inTable) {
        tableHtml += '</tbody></table></div>';
        processedLines.push(tableHtml);
    }

    let body = processedLines.join('\n');

    // 4. Headers (multiline mode)
    body = body.replace(/^# (.*?)$/gm, '<h2 class="md-h1">$1</h2>');
    body = body.replace(/^## (.*?)$/gm, '<h3 class="md-h2">$1</h3>');
    body = body.replace(/^### (.*?)$/gm, '<h4 class="md-h3">$1</h4>');

    // 5. Bold: **text**
    body = body.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // 6. Unordered and Ordered Lists
    const listLines = body.split('\n');
    let inUnorderedList = false;
    let inOrderedList = false;
    const finalLines = [];

    for (let i = 0; i < listLines.length; i++) {
        let line = listLines[i];
        let trimmed = line.trim();

        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            if (inOrderedList) {
                finalLines.push('</ol>');
                inOrderedList = false;
            }
            if (!inUnorderedList) {
                finalLines.push('<ul class="md-ul">');
                inUnorderedList = true;
            }
            const content = trimmed.substring(2);
            finalLines.push(`<li>${content}</li>`);
        } else if (/^\d+\.\s/.test(trimmed)) {
            if (inUnorderedList) {
                finalLines.push('</ul>');
                inUnorderedList = false;
            }
            if (!inOrderedList) {
                finalLines.push('<ol class="md-ol">');
                inOrderedList = true;
            }
            const content = trimmed.replace(/^\d+\.\s/, '');
            finalLines.push(`<li>${content}</li>`);
        } else {
            if (inUnorderedList) {
                finalLines.push('</ul>');
                inUnorderedList = false;
            }
            if (inOrderedList) {
                finalLines.push('</ol>');
                inOrderedList = false;
            }
            finalLines.push(line);
        }
    }
    if (inUnorderedList) finalLines.push('</ul>');
    if (inOrderedList) finalLines.push('</ol>');

    body = finalLines.join('\n');

    // 7. Paragraph spacing and line breaks
    body = body.replace(/\n\n+/g, '<div class="md-spacing"></div>');
    body = body.replace(/\n/g, '<br>');

    // Clean up empty <br> tags adjacent to block element tags
    body = body.replace(/<(ul|ol|table|thead|tbody|tr|pre|div)[^>]*><br>/g, function(match) {
        return match.replace('<br>', '');
    });
    body = body.replace(/<br><\/(ul|ol|table|thead|tbody|tr|pre|div)>/g, function(match) {
        return match.replace('<br>', '');
    });
    body = body.replace(/<\/li><br>/g, '</li>');
    body = body.replace(/<\/tr><br>/g, '</tr>');
    body = body.replace(/<\/th><br>/g, '</th>');
    body = body.replace(/<\/td><br>/g, '</td>');

    // 8. Restore Code Blocks
    codeBlocks.forEach((block, index) => {
        const placeholder = `__CODE_BLOCK_PLACEHOLDER_${index}__`;
        const codeHtml = `<pre class="md-code-block"><code class="language-${block.lang}">${block.code}</code></pre>`;
        body = body.replace(placeholder, codeHtml);
    });

    // Restore Inline Code
    inlineCodes.forEach((code, index) => {
        const placeholder = `__INLINE_CODE_PLACEHOLDER_${index}__`;
        const inlineHtml = `<code class="md-inline-code">${code}</code>`;
        body = body.replace(placeholder, inlineHtml);
    });

    return body;
}
