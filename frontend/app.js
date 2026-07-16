/**
 * CSUCI Student Success Navigator - Frontend Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const modeMockBtn = document.getElementById('mode-mock');
    const modeLiveBtn = document.getElementById('mode-live');
    const liveSettings = document.getElementById('live-settings');
    const apiUrlInput = document.getElementById('api-url');
    const connectionStatusText = document.getElementById('connection-status-text');
    const statusIndicator = document.querySelector('.status-indicator');
    const sessionIdVal = document.getElementById('session-id-val');
    const responseTypeVal = document.getElementById('response-type-val');
    const clearSessionBtn = document.getElementById('clear-session-btn');
    
    // Citation overlay
    const citationOverlay = document.getElementById('citation-overlay');
    const citationBody = document.getElementById('citation-body');
    const closeCitationBtn = document.getElementById('close-citation-btn');

    // App State
    let currentMode = 'mock'; // 'mock' or 'live'
    let sessionId = generateUUID();
    let currentResponseType = 'None';
    let typingTimer = null;

    // Load saved API URL from localStorage if exists
    const savedApiUrl = localStorage.getItem('csuci_api_url') || 'http://localhost:5000/chat';
    apiUrlInput.value = savedApiUrl;

    // Initial session display
    sessionIdVal.textContent = sessionId;

    // Mode switching handlers
    modeMockBtn.addEventListener('click', () => {
        currentMode = 'mock';
        modeMockBtn.classList.add('active');
        modeLiveBtn.classList.remove('active');
        liveSettings.classList.add('hidden');
        updateStatus();
    });

    modeLiveBtn.addEventListener('click', () => {
        currentMode = 'live';
        modeLiveBtn.classList.add('active');
        modeMockBtn.classList.remove('active');
        liveSettings.classList.remove('hidden');
        updateStatus();
    });

    // Save API URL on edit
    apiUrlInput.addEventListener('input', () => {
        localStorage.setItem('csuci_api_url', apiUrlInput.value.trim());
    });

    // Clear session / New conversation handler
    clearSessionBtn.addEventListener('click', () => {
        sessionId = generateUUID();
        sessionIdVal.textContent = sessionId;
        setResponseType('None');
        
        // Clear chat area except the initial greeting
        chatMessages.innerHTML = `
            <div class="message system-message">
                <div class="message-avatar">⚓</div>
                <div class="message-content">
                    <p>Session restarted. Welcome back! I can help you with registration deadlines, advising appointments, financial aid, or campus support resources. What is your question today?</p>
                    <div class="timestamp">Just now</div>
                </div>
            </div>
        `;
    });

    // Close citation overlay
    closeCitationBtn.addEventListener('click', () => {
        citationOverlay.classList.add('hidden');
    });

    // Quick suggestions triggers
    document.querySelectorAll('.suggest-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.getAttribute('data-query');
            if (query) {
                chatInput.value = query;
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    });

    // Majors Accordion Toggle
    const majorsHeaderToggle = document.getElementById('majors-header-toggle');
    const majorsContent = document.getElementById('majors-content');
    const majorsCaret = document.getElementById('majors-caret');

    if (majorsHeaderToggle && majorsContent && majorsCaret) {
        majorsHeaderToggle.addEventListener('click', () => {
            const isHidden = majorsContent.classList.contains('hidden');
            if (isHidden) {
                majorsContent.classList.remove('hidden');
                majorsCaret.style.transform = 'rotate(180deg)';
            } else {
                majorsContent.classList.add('hidden');
                majorsCaret.style.transform = 'rotate(0deg)';
            }
        });
    }

    // Majors links triggers
    document.querySelectorAll('.major-link-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.getAttribute('data-query');
            if (query) {
                chatInput.value = query;
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    });

    // Form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const messageText = chatInput.value.trim();
        if (!messageText) return;

        // Clear input field
        chatInput.value = '';

        // Add user bubble
        appendMessage('user', messageText);

        // Scroll down
        scrollToBottom();

        // Show typing indicator
        const typingIndicator = showTypingIndicator();
        scrollToBottom();

        try {
            let response;
            if (currentMode === 'mock') {
                response = await getMockResponse(messageText);
            } else {
                response = await getLiveResponse(messageText);
            }

            // Remove typing indicator
            hideTypingIndicator(typingIndicator);

            // Add bot bubble
            appendMessage('system', response.answer, response.sources, response.type);
            setResponseType(response.type);

        } catch (error) {
            console.error('Error fetching response:', error);
            hideTypingIndicator(typingIndicator);
            appendMessage('system', `❌ Error: ${error.message || 'Failed to contact the server.'}`, [], 'error');
            setResponseType('Error');
        }

        scrollToBottom();
    });

    // Helper: update status indicators
    function updateStatus() {
        if (currentMode === 'mock') {
            statusIndicator.className = 'status-indicator mock';
            connectionStatusText.textContent = 'Mock Server Active';
        } else {
            const hasUrl = !!apiUrlInput.value.trim();
            statusIndicator.className = hasUrl ? 'status-indicator online' : 'status-indicator offline';
            connectionStatusText.textContent = hasUrl ? 'Live API Active' : 'No Endpoint Configured';
        }
    }

    // Helper: set response type badge
    function setResponseType(type) {
        currentResponseType = type;
        responseTypeVal.textContent = type;
        responseTypeVal.className = 'badge';

        if (type === 'crisis') {
            responseTypeVal.classList.add('badge-crisis');
        } else if (type === 'escalation') {
            responseTypeVal.classList.add('badge-escalation');
        } else if (type === 'normal') {
            responseTypeVal.classList.add('badge-success');
        } else {
            responseTypeVal.classList.add('badge-neutral');
        }
    }

    // Helper: generate session UUID
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // Helper: scroll chat container to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Helper: create and append messages
    function appendMessage(sender, text, sources = [], type = 'normal') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.textContent = sender === 'user' ? '🧑‍🎓' : '⚓';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        let displayText = text;
        let flowchartData = null;

        if (sender === 'system') {
            const flowchartRegex = /```json-flowchart\s*([\s\S]*?)\s*```/;
            const match = text.match(flowchartRegex);
            if (match) {
                try {
                    flowchartData = JSON.parse(match[1].trim());
                    displayText = text.replace(flowchartRegex, '').trim();
                } catch (e) {
                    console.error("Failed to parse flowchart JSON from LLM:", e);
                }
            }
        }

        const textPara = document.createElement('p');
        textPara.innerHTML = formatMarkdown(displayText);
        contentDiv.appendChild(textPara);

        // If flowchart data was parsed, render the interactive Opt-In button
        if (flowchartData) {
            const btnContainer = document.createElement('div');
            btnContainer.style.marginTop = '12px';
            
            const viewBtn = document.createElement('button');
            viewBtn.className = 'secondary-btn';
            viewBtn.style.borderColor = 'var(--primary)';
            viewBtn.style.color = '#fca5a5';
            viewBtn.style.fontSize = '12px';
            viewBtn.style.display = 'flex';
            viewBtn.style.alignItems = 'center';
            viewBtn.style.gap = '6px';
            viewBtn.style.padding = '8px 14px';
            viewBtn.innerHTML = `<span>📊 View Custom Generated Flowchart</span>`;
            
            viewBtn.addEventListener('click', () => {
                localStorage.setItem('csuci_custom_flowchart', JSON.stringify(flowchartData));
                window.open('flowchart.html', '_blank');
            });
            
            btnContainer.appendChild(viewBtn);
            contentDiv.appendChild(btnContainer);
        }

        // Append Sources if any
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources-container';
            
            const titleSpan = document.createElement('span');
            titleSpan.className = 'sources-title';
            titleSpan.textContent = 'Retrieved Sources:';
            sourcesDiv.appendChild(titleSpan);

            const tagsDiv = document.createElement('span');
            tagsDiv.className = 'sources-tags';

            sources.forEach(src => {
                const srcName = typeof src === 'string' ? src : src.title;
                const srcUrl = typeof src === 'string' ? '#' : src.url;

                const tag = document.createElement('button');
                tag.className = 'source-tag';
                tag.innerHTML = `📄 ${srcName}`;
                tag.addEventListener('click', () => {
                    showCitation(srcName, srcUrl);
                });
                tagsDiv.appendChild(tag);
            });
            
            sourcesDiv.appendChild(tagsDiv);
            contentDiv.appendChild(sourcesDiv);
        }

        const timeDiv = document.createElement('div');
        timeDiv.className = 'timestamp';
        const now = new Date();
        timeDiv.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        contentDiv.appendChild(timeDiv);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        chatMessages.appendChild(messageDiv);
    }

    // Helper: show typing indicator
    function showTypingIndicator() {
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'message system-message typing-indicator-container';
        
        indicatorDiv.innerHTML = `
            <div class="message-avatar">⚓</div>
            <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
        chatMessages.appendChild(indicatorDiv);
        return indicatorDiv;
    }

    // Helper: remove typing indicator
    function hideTypingIndicator(indicatorEl) {
        if (indicatorEl && indicatorEl.parentNode) {
            indicatorEl.parentNode.removeChild(indicatorEl);
        }
    }

    // Helper: show citation popup
    function showCitation(name, url) {
        citationBody.innerHTML = `
            <div class="citation-source-title">📄 Source Document: <strong>${name}</strong></div>
            <div class="citation-source-desc">
                This answer was verified against official CSUCI records. You can view or download the original source document here:
                <br/><br/>
                <a href="${url === '#' ? 'https://www.csuci.edu' : url}" target="_blank" style="color: #93c5fd; text-decoration: underline;">
                    Open ${name} in a new tab &rarr;
                </a>
            </div>
        `;
        citationOverlay.classList.remove('hidden');
    }

    // Helper: simple text to markdown-like parser (handles links, lists, bold)
    function formatMarkdown(text) {
        // Bullet points
        let formatted = text.replace(/^[•*]\s+(.*)$/gm, '• $1');
        
        // Line breaks
        formatted = formatted.replace(/\n/g, '<br/>');

        // Bold text
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Links: [text](url)
        formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color: #93c5fd; text-decoration: underline;">$1</a>');

        return formatted;
    }

    // --- Mock Engine ---
    async function getMockResponse(query) {
        return new Promise((resolve) => {
            // Simulate variable latency
            const delay = 600 + Math.random() * 800;
            
            setTimeout(() => {
                const lower = query.toLowerCase();

                // 1. Crisis Filter check
                const crisisKeywords = ["suicide", "suicidal", "self-harm", "selfharm", "kill myself", "end my life", "i want to die"];
                const isCrisis = crisisKeywords.some(kw => lower.includes(kw)) || /\b(hurt myself|cut myself)\b/i.test(query);

                if (isCrisis) {
                    resolve({
                        answer: "I'm really concerned about what you've shared, and I want to make sure you get the support you need right away.\n\n**If you are in immediate danger, please call 911.**\n\nHere are resources available to you:\n\n• **988 Suicide & Crisis Lifeline** — Call or text **988** (available 24/7)\n• **CSUCI Counseling Services (CAPS)** — Call **(805) 437-2088** or **(805) 437-8232** (Mon–Fri 8 AM – 5 PM)\n• **Crisis Text Line** — Text **HOME** to **741741**\n\nYou are not alone, and there are people who care about you. Please reach out to one of these resources as soon as possible.",
                        sources: [],
                        sessionId: sessionId,
                        type: 'crisis'
                    });
                    return;
                }

                // 2. Escalation Filter check
                const escalationKeywords = ["talk to a person", "talk to human", "advisor", "real person", "escalate", "advisor", "counselor", "staff", "human"];
                const isEscalation = escalationKeywords.some(kw => lower.includes(kw)) || /connect me to/i.test(query) || /speak with/i.test(query);

                if (isEscalation) {
                    resolve({
                        answer: "I'll connect you with a human advisor. A staff member has been notified and will reach out to you shortly. In the meantime, you can contact the Advising Center at **(805) 437-8500**, email advisor@csuci.edu, or visit Bell Tower room 1548.",
                        sources: [],
                        sessionId: sessionId,
                        type: 'escalation'
                    });
                    return;
                }

                // 3. Flowchart / Roadmap requests
                if (lower.includes('flowchart') || lower.includes('roadmap') || lower.includes('curriculum') || lower.includes('major map') || lower.includes('major') || lower.includes('emphasizing') || lower.includes('emphasis') || lower.includes('courses') || lower.includes('concentration') || lower.includes('class map')) {
                    let majorName = "Computer Science";
                    let catalogYear = "2026";
                    let totalUnits = 120;
                    let semesters = [];
                    let notes = [];
                    let checklist = {};

                    if (lower.includes('account')) {
                        majorName = "Business Administration (Accounting Option)";
                        semesters = [
                            {
                                term: "Semester 1",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "ACCT 210", title: "Financial Accounting", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "ECON 110", title: "Principles of Microeconomics", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "GE Area A2", title: "Written Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area C1", title: "Arts", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area E", title: "Lifelong Learning", units: 3, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 2",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "ACCT 220", title: "Managerial Accounting", units: 3, category: "Major Preparation", prereqs: "ACCT 210" },
                                    { code: "ECON 111", title: "Principles of Macroeconomics", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "MATH 140", title: "Business Calculus", units: 3, category: "Major Preparation", prereqs: "Placement" },
                                    { code: "GE Area A1", title: "Oral Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area A3", title: "Critical Thinking", units: 3, category: "GE", prereqs: "GE Area A2" }
                                ]
                            },
                            {
                                term: "Semester 3",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 210", title: "Business Law", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "MATH 329", title: "Applied Statistics for Business", units: 3, category: "Major Preparation", prereqs: "MATH 140" },
                                    { code: "GE Area B1", title: "Physical Science", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area B3", title: "Science Lab Component", units: 1, category: "GE", prereqs: "None" },
                                    { code: "GE Area C2", title: "Humanities", units: 5, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 4",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 310", title: "Business Communications", units: 3, category: "Major Core", prereqs: "GE Area A2" },
                                    { code: "GE Area B2", title: "Life Science", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area D", title: "Social Sciences", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area F", title: "Ethnic Studies", units: 3, category: "GE", prereqs: "None" },
                                    { code: "Elective", title: "Lower-Division Business Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 5",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "FIN 300", title: "Business Finance", units: 3, category: "Major Core", prereqs: "ACCT 220, MATH 140" },
                                    { code: "MKT 310", title: "Principles of Marketing", units: 3, category: "Major Core", prereqs: "ECON 110" },
                                    { code: "MGT 307", title: "Management Theory & Practice", units: 3, category: "Major Core", prereqs: "None" },
                                    { code: "UD GE Area C", title: "Upper-Division Humanities", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "ACCT 300", title: "Applied Managerial Accounting", units: 3, category: "Option", prereqs: "ACCT 220" }
                                ]
                            },
                            {
                                term: "Semester 6",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 320", title: "Operations Management", units: 3, category: "Major Core", prereqs: "MATH 329" },
                                    { code: "MIS 310", title: "Management Information Systems", units: 3, category: "Major Core", prereqs: "None" },
                                    { code: "UD GE Area D", title: "Upper-Division Social Sciences", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "ACCT 310", title: "Intermediate Accounting", units: 3, category: "Option", prereqs: "ACCT 220" },
                                    { code: "ACCT 320", title: "Accounting Info Systems & Data Analytics", units: 3, category: "Option", prereqs: "ACCT 220" }
                                ]
                            },
                            {
                                term: "Semester 7",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 490", title: "Business Internship / Project", units: 3, category: "Major Core", prereqs: "Senior Standing" },
                                    { code: "ACCT 330", title: "Federal Taxation", units: 3, category: "Option", prereqs: "ACCT 220" },
                                    { code: "ACCT 420", title: "Auditing & Analytics", units: 3, category: "Option", prereqs: "ACCT 310, ACCT 320" },
                                    { code: "UD GE Area B", title: "Upper-Division Science/Math", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 8",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 499", title: "Strategic Management Capstone", units: 3, category: "Major Core", prereqs: "Senior Standing, FIN 300, MKT 310, MGT 307" },
                                    { code: "ACCT 430", title: "Advanced Accounting", units: 3, category: "Option", prereqs: "ACCT 310" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            }
                        ];
                        notes = [
                            "Prerequisites must be completed with a C- or better.",
                            "Course sequence designed to prepare students for the CPA exam."
                        ];
                        checklist = {
                            major_prep: ["ACCT 210", "ACCT 220", "ECON 110", "ECON 111", "MATH 140", "BUS 210", "MATH 329"],
                            major_core: ["BUS 310", "FIN 300", "MKT 310", "MGT 307", "BUS 320", "MIS 310", "BUS 490", "BUS 499"],
                            upper_division_ge: ["UD GE Area B", "UD GE Area C", "UD GE Area D"],
                            other_requirements: ["Accounting Option Courses (18 units)", "120 Total Units"]
                        };
                    } else if (lower.includes('finance')) {
                        majorName = "Business Administration (Finance Option)";
                        semesters = [
                            {
                                term: "Semester 1",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "ACCT 210", title: "Financial Accounting", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "ECON 110", title: "Principles of Microeconomics", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "GE Area A2", title: "Written Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area C1", title: "Arts", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area E", title: "Lifelong Learning", units: 3, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 2",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "ACCT 220", title: "Managerial Accounting", units: 3, category: "Major Preparation", prereqs: "ACCT 210" },
                                    { code: "ECON 111", title: "Principles of Macroeconomics", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "MATH 140", title: "Business Calculus", units: 3, category: "Major Preparation", prereqs: "Placement" },
                                    { code: "GE Area A1", title: "Oral Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area A3", title: "Critical Thinking", units: 3, category: "GE", prereqs: "GE Area A2" }
                                ]
                            },
                            {
                                term: "Semester 3",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 210", title: "Business Law", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "MATH 329", title: "Applied Statistics for Business", units: 3, category: "Major Preparation", prereqs: "MATH 140" },
                                    { code: "GE Area B1", title: "Physical Science", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area B3", title: "Science Lab Component", units: 1, category: "GE", prereqs: "None" },
                                    { code: "GE Area C2", title: "Humanities", units: 5, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 4",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 310", title: "Business Communications", units: 3, category: "Major Core", prereqs: "GE Area A2" },
                                    { code: "GE Area B2", title: "Life Science", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area D", title: "Social Sciences", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area F", title: "Ethnic Studies", units: 3, category: "GE", prereqs: "None" },
                                    { code: "Elective", title: "Lower-Division Business Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 5",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "FIN 300", title: "Business Finance", units: 3, category: "Major Core", prereqs: "ACCT 220, MATH 140" },
                                    { code: "MKT 310", title: "Principles of Marketing", units: 3, category: "Major Core", prereqs: "ECON 110" },
                                    { code: "MGT 307", title: "Management Theory & Practice", units: 3, category: "Major Core", prereqs: "None" },
                                    { code: "UD GE Area C", title: "Upper-Division Humanities", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "ACCT 300", title: "Applied Managerial Accounting", units: 3, category: "Major Core", prereqs: "ACCT 220" }
                                ]
                            },
                            {
                                term: "Semester 6",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 320", title: "Operations Management", units: 3, category: "Major Core", prereqs: "MATH 329" },
                                    { code: "MIS 310", title: "Management Information Systems", units: 3, category: "Major Core", prereqs: "None" },
                                    { code: "UD GE Area D", title: "Upper-Division Social Sciences", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "FIN 410", title: "Financial Markets and Institutions", units: 3, category: "Option", prereqs: "FIN 300" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 7",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 490", title: "Business Internship / Project", units: 3, category: "Major Core", prereqs: "Senior Standing" },
                                    { code: "FIN 411", title: "Corporate Financial Management", units: 3, category: "Option", prereqs: "FIN 300" },
                                    { code: "FIN 413", title: "Investment Analysis", units: 3, category: "Option", prereqs: "FIN 300" },
                                    { code: "UD GE Area B", title: "Upper-Division Science/Math", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 8",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 499", title: "Strategic Management Capstone", units: 3, category: "Major Core", prereqs: "Senior Standing, FIN 300, MKT 310, MGT 307" },
                                    { code: "FIN 412", title: "International Financial Management", units: 3, category: "Option", prereqs: "FIN 300" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            }
                        ];
                        notes = [
                            "Prerequisites must be completed with a C- or better.",
                            "FIN 300 is a prerequisite for all 400-level finance option courses."
                        ];
                        checklist = {
                            major_prep: ["ACCT 210", "ACCT 220", "ECON 110", "ECON 111", "MATH 140", "BUS 210", "MATH 329"],
                            major_core: ["BUS 310", "FIN 300", "MKT 310", "MGT 307", "BUS 320", "MIS 310", "BUS 490", "BUS 499"],
                            upper_division_ge: ["UD GE Area B", "UD GE Area C", "UD GE Area D"],
                            other_requirements: ["Finance Option Courses (12 units)", "120 Total Units"]
                        };
                    } else if (lower.includes('market')) {
                        majorName = "Business Administration (Marketing Option)";
                        semesters = [
                            {
                                term: "Semester 1",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "ACCT 210", title: "Financial Accounting", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "ECON 110", title: "Principles of Microeconomics", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "GE Area A2", title: "Written Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area C1", title: "Arts", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area E", title: "Lifelong Learning", units: 3, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 2",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "ACCT 220", title: "Managerial Accounting", units: 3, category: "Major Preparation", prereqs: "ACCT 210" },
                                    { code: "ECON 111", title: "Principles of Macroeconomics", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "MATH 140", title: "Business Calculus", units: 3, category: "Major Preparation", prereqs: "Placement" },
                                    { code: "GE Area A1", title: "Oral Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area A3", title: "Critical Thinking", units: 3, category: "GE", prereqs: "GE Area A2" }
                                ]
                            },
                            {
                                term: "Semester 3",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 210", title: "Business Law", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "MATH 329", title: "Applied Statistics for Business", units: 3, category: "Major Preparation", prereqs: "MATH 140" },
                                    { code: "GE Area B1", title: "Physical Science", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area B3", title: "Science Lab Component", units: 1, category: "GE", prereqs: "None" },
                                    { code: "GE Area C2", title: "Humanities", units: 5, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 4",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 310", title: "Business Communications", units: 3, category: "Major Core", prereqs: "GE Area A2" },
                                    { code: "GE Area B2", title: "Life Science", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area D", title: "Social Sciences", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area F", title: "Ethnic Studies", units: 3, category: "GE", prereqs: "None" },
                                    { code: "Elective", title: "Lower-Division Business Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 5",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "FIN 300", title: "Business Finance", units: 3, category: "Major Core", prereqs: "ACCT 220, MATH 140" },
                                    { code: "MKT 310", title: "Principles of Marketing", units: 3, category: "Major Core", prereqs: "ECON 110" },
                                    { code: "MGT 307", title: "Management Theory & Practice", units: 3, category: "Major Core", prereqs: "None" },
                                    { code: "UD GE Area C", title: "Upper-Division Humanities", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "ACCT 300", title: "Applied Managerial Accounting", units: 3, category: "Major Core", prereqs: "ACCT 220" }
                                ]
                            },
                            {
                                term: "Semester 6",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 320", title: "Operations Management", units: 3, category: "Major Core", prereqs: "MATH 329" },
                                    { code: "MIS 310", title: "Management Information Systems", units: 3, category: "Major Core", prereqs: "None" },
                                    { code: "UD GE Area D", title: "Upper-Division Social Sciences", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "MKT 311", title: "Consumer Behavior", units: 3, category: "Option", prereqs: "MKT 310" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 7",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 490", title: "Business Internship / Project", units: 3, category: "Major Core", prereqs: "Senior Standing" },
                                    { code: "MKT 410", title: "Social Media Marketing", units: 3, category: "Option", prereqs: "MKT 310" },
                                    { code: "MKT 420", title: "Market Research", units: 3, category: "Option", prereqs: "MKT 310, MATH 329" },
                                    { code: "UD GE Area B", title: "Upper-Division Science/Math", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 8",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 499", title: "Strategic Management Capstone", units: 3, category: "Major Core", prereqs: "Senior Standing, FIN 300, MKT 310, MGT 307" },
                                    { code: "MKT 430", title: "Marketing Strategy", units: 3, category: "Option", prereqs: "MKT 310, Senior Standing" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            }
                        ];
                        notes = [
                            "Prerequisites must be completed with a C- or better.",
                            "MKT 310 is a prerequisite for all marketing option courses."
                        ];
                        checklist = {
                            major_prep: ["ACCT 210", "ACCT 220", "ECON 110", "ECON 111", "MATH 140", "BUS 210", "MATH 329"],
                            major_core: ["BUS 310", "FIN 300", "MKT 310", "MGT 307", "BUS 320", "MIS 310", "BUS 490", "BUS 499"],
                            upper_division_ge: ["UD GE Area B", "UD GE Area C", "UD GE Area D"],
                            other_requirements: ["Marketing Option Courses (12 units)", "120 Total Units"]
                        };
                    } else if (lower.includes('management') || lower.includes('mgt') || lower.includes('leadership')) {
                        majorName = "Business Administration (Management Option)";
                        semesters = [
                            {
                                term: "Semester 1",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "ACCT 210", title: "Financial Accounting", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "ECON 110", title: "Principles of Microeconomics", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "GE Area A2", title: "Written Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area C1", title: "Arts", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area E", title: "Lifelong Learning", units: 3, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 2",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "ACCT 220", title: "Managerial Accounting", units: 3, category: "Major Preparation", prereqs: "ACCT 210" },
                                    { code: "ECON 111", title: "Principles of Macroeconomics", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "MATH 140", title: "Business Calculus", units: 3, category: "Major Preparation", prereqs: "Placement" },
                                    { code: "GE Area A1", title: "Oral Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area A3", title: "Critical Thinking", units: 3, category: "GE", prereqs: "GE Area A2" }
                                ]
                            },
                            {
                                term: "Semester 3",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 210", title: "Business Law", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "MATH 329", title: "Applied Statistics for Business", units: 3, category: "Major Preparation", prereqs: "MATH 140" },
                                    { code: "GE Area B1", title: "Physical Science", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area B3", title: "Science Lab Component", units: 1, category: "GE", prereqs: "None" },
                                    { code: "GE Area C2", title: "Humanities", units: 5, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 4",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 310", title: "Business Communications", units: 3, category: "Major Core", prereqs: "GE Area A2" },
                                    { code: "GE Area B2", title: "Life Science", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area D", title: "Social Sciences", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area F", title: "Ethnic Studies", units: 3, category: "GE", prereqs: "None" },
                                    { code: "Elective", title: "Lower-Division Business Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 5",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "FIN 300", title: "Business Finance", units: 3, category: "Major Core", prereqs: "ACCT 220, MATH 140" },
                                    { code: "MKT 310", title: "Principles of Marketing", units: 3, category: "Major Core", prereqs: "ECON 110" },
                                    { code: "MGT 307", title: "Management Theory & Practice", units: 3, category: "Major Core", prereqs: "None" },
                                    { code: "UD GE Area C", title: "Upper-Division Humanities", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "ACCT 300", title: "Applied Managerial Accounting", units: 3, category: "Major Core", prereqs: "ACCT 220" }
                                ]
                            },
                            {
                                term: "Semester 6",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 320", title: "Operations Management", units: 3, category: "Major Core", prereqs: "MATH 329" },
                                    { code: "MIS 310", title: "Management Information Systems", units: 3, category: "Major Core", prereqs: "None" },
                                    { code: "UD GE Area D", title: "Upper-Division Social Sciences", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "MGT 410", title: "Management of International Business", units: 3, category: "Option", prereqs: "MGT 307" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 7",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 490", title: "Business Internship / Project", units: 3, category: "Major Core", prereqs: "Senior Standing" },
                                    { code: "MGT 421", title: "Human Resource Management", units: 3, category: "Option", prereqs: "MGT 307" },
                                    { code: "MGT 424", title: "Organizational Behavior", units: 3, category: "Option", prereqs: "MGT 307" },
                                    { code: "UD GE Area B", title: "Upper-Division Science/Math", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 8",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 499", title: "Strategic Management Capstone", units: 3, category: "Major Core", prereqs: "Senior Standing, FIN 300, MKT 310, MGT 307" },
                                    { code: "MGT UD Elective", title: "Upper-Division Management Course", units: 3, category: "Option", prereqs: "MGT 307" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            }
                        ];
                        notes = [
                            "Prerequisites must be completed with a C- or better.",
                            "MGT 307 is a prerequisite for all management option courses."
                        ];
                        checklist = {
                            major_prep: ["ACCT 210", "ACCT 220", "ECON 110", "ECON 111", "MATH 140", "BUS 210", "MATH 329"],
                            major_core: ["BUS 310", "FIN 300", "MKT 310", "MGT 307", "BUS 320", "MIS 310", "BUS 490", "BUS 499"],
                            upper_division_ge: ["UD GE Area B", "UD GE Area C", "UD GE Area D"],
                            other_requirements: ["Management Option Courses (12 units)", "120 Total Units"]
                        };
                    } else if (lower.includes('business')) {
                        majorName = "Business Administration";
                        semesters = [
                            {
                                term: "Semester 1",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "ACCT 210", title: "Financial Accounting", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "ECON 110", title: "Principles of Microeconomics", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "GE Area A2", title: "Written Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area C1", title: "Arts", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area E", title: "Lifelong Learning", units: 3, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 2",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "ACCT 220", title: "Managerial Accounting", units: 3, category: "Major Preparation", prereqs: "ACCT 210" },
                                    { code: "ECON 111", title: "Principles of Macroeconomics", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "MATH 140", title: "Business Calculus", units: 3, category: "Major Preparation", prereqs: "Placement" },
                                    { code: "GE Area A1", title: "Oral Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area A3", title: "Critical Thinking", units: 3, category: "GE", prereqs: "GE Area A2" }
                                ]
                            },
                            {
                                term: "Semester 3",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 210", title: "Business Law", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "MATH 329", title: "Applied Statistics for Business", units: 3, category: "Major Preparation", prereqs: "MATH 140" },
                                    { code: "GE Area B1", title: "Physical Science", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area B3", title: "Science Lab Component", units: 1, category: "GE", prereqs: "None" },
                                    { code: "GE Area C2", title: "Humanities", units: 5, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 4",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 310", title: "Business Communications", units: 3, category: "Major Core", prereqs: "GE Area A2" },
                                    { code: "GE Area B2", title: "Life Science", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area D", title: "Social Sciences", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area F", title: "Ethnic Studies", units: 3, category: "GE", prereqs: "None" },
                                    { code: "Elective", title: "Lower-Division Business Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 5",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "FIN 300", title: "Business Finance", units: 3, category: "Major Core", prereqs: "ACCT 220, MATH 140" },
                                    { code: "MKT 310", title: "Principles of Marketing", units: 3, category: "Major Core", prereqs: "ECON 110" },
                                    { code: "MGT 307", title: "Management Theory & Practice", units: 3, category: "Major Core", prereqs: "None" },
                                    { code: "UD GE Area C", title: "Upper-Division Humanities", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "Business Option 1", title: "Business Concentration Elective", units: 3, category: "Option", prereqs: "Varies" }
                                ]
                            },
                            {
                                term: "Semester 6",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 320", title: "Operations Management", units: 3, category: "Major Core", prereqs: "MATH 329" },
                                    { code: "MIS 310", title: "Management Information Systems", units: 3, category: "Major Core", prereqs: "None" },
                                    { code: "UD GE Area D", title: "Upper-Division Social Sciences", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "Business Option 2", title: "Business Concentration Elective", units: 3, category: "Option", prereqs: "Varies" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 7",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 490", title: "Business Internship / Project", units: 3, category: "Major Core", prereqs: "Senior Standing" },
                                    { code: "Business Option 3", title: "Business Concentration Elective", units: 3, category: "Option", prereqs: "Varies" },
                                    { code: "UD GE Area B", title: "Upper-Division Science/Math", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 8",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BUS 499", title: "Strategic Management Capstone", units: 3, category: "Major Core", prereqs: "Senior Standing, FIN 300, MKT 310, MGT 307" },
                                    { code: "Business Option 4", title: "Business Concentration Elective", units: 3, category: "Option", prereqs: "Varies" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            }
                        ];
                        notes = [
                            "Prerequisites must be completed with a C- or better.",
                            "MGT 307 and FIN 300 require junior-level standing."
                        ];
                        checklist = {
                            major_prep: ["ACCT 210", "ACCT 220", "ECON 110", "ECON 111", "MATH 140", "BUS 210", "MATH 329"],
                            major_core: ["BUS 310", "FIN 300", "MKT 310", "MGT 307", "BUS 320", "MIS 310", "BUS 490", "BUS 499"],
                            upper_division_ge: ["UD GE Area B", "UD GE Area C", "UD GE Area D"],
                            other_requirements: ["Business Concentration", "120 Total Units"]
                        };
                    } else if (lower.includes('biol') || lower.includes('bio') || lower.includes('medicine') || lower.includes('health') || lower.includes('nurs')) {
                        majorName = "Biology";
                        semesters = [
                            {
                                term: "Semester 1",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "BIOL 200", title: "Principles of Organismal Biology", units: 4, category: "Major Core", prereqs: "None" },
                                    { code: "CHEM 121", title: "General Chemistry I", units: 4, category: "Major Preparation", prereqs: "Placement" },
                                    { code: "GE Area A2", title: "Written Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area E", title: "Lifelong Learning", units: 4, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 2",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "BIOL 201", title: "Principles of Cell & Molecular Biol", units: 4, category: "Major Core", prereqs: "BIOL 200" },
                                    { code: "CHEM 122", title: "General Chemistry II", units: 4, category: "Major Preparation", prereqs: "CHEM 121" },
                                    { code: "MATH 150", title: "Calculus I", units: 4, category: "Major Preparation", prereqs: "Placement" },
                                    { code: "GE Area A1", title: "Oral Communication", units: 3, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 3",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "BIOL 202", title: "Biostatistics", units: 3, category: "Major Core", prereqs: "MATH 150" },
                                    { code: "CHEM 311", title: "Organic Chemistry I", units: 3, category: "Major Preparation", prereqs: "CHEM 122" },
                                    { code: "CHEM 312", title: "Organic Chemistry I Lab", units: 1, category: "Major Preparation", prereqs: "CHEM 311" },
                                    { code: "GE Area A3", title: "Critical Thinking", units: 3, category: "GE", prereqs: "GE Area A2" },
                                    { code: "GE Area C1", title: "Arts", units: 5, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 4",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "CHEM 314", title: "Organic Chemistry II", units: 3, category: "Major Preparation", prereqs: "CHEM 311" },
                                    { code: "CHEM 315", title: "Organic Chemistry II Lab", units: 1, category: "Major Preparation", prereqs: "CHEM 314" },
                                    { code: "GE Area C2", title: "Humanities", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area D", title: "Social Sciences", units: 5, category: "GE", prereqs: "None" },
                                    { code: "GE Area F", title: "Ethnic Studies", units: 3, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 5",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BIOL 300", title: "Cell Biology", units: 4, category: "Major Core", prereqs: "BIOL 201, CHEM 311" },
                                    { code: "BIOL 302", title: "Genetics", units: 4, category: "Major Core", prereqs: "BIOL 201, CHEM 122" },
                                    { code: "PHYS 100", title: "Introduction to Physics I", units: 4, category: "Major Preparation", prereqs: "MATH 150" },
                                    { code: "UD GE Area C", title: "Upper-Division Humanities", units: 3, category: "GE", prereqs: "Junior Standing" }
                                ]
                            },
                            {
                                term: "Semester 6",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BIOL 303", title: "Evolutionary Biology", units: 3, category: "Major Core", prereqs: "BIOL 302" },
                                    { code: "PHYS 101", title: "Introduction to Physics II", units: 4, category: "Major Preparation", prereqs: "PHYS 100" },
                                    { code: "Biology UD Elec 1", title: "Upper-Division Bio Elective w/ Lab", units: 4, category: "Option", prereqs: "Varies" },
                                    { code: "UD GE Area D", title: "Upper-Division Social Sciences", units: 4, category: "GE", prereqs: "Junior Standing" }
                                ]
                            },
                            {
                                term: "Semester 7",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BIOL 400", title: "Molecular Biology", units: 4, category: "Major Core", prereqs: "BIOL 300, BIOL 302" },
                                    { code: "Biology UD Elec 2", title: "Upper-Division Biology Course", units: 3, category: "Option", prereqs: "Varies" },
                                    { code: "UD GE Area B", title: "Upper-Division Science/Math", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "Elective", title: "General Elective", units: 5, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 8",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "BIOL 499", title: "Senior Capstone", units: 3, category: "Major Core", prereqs: "Senior Standing, BIOL 400" },
                                    { code: "Biology UD Elec 3", title: "Upper-Division Biology Course", units: 3, category: "Option", prereqs: "Varies" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            }
                        ];
                        notes = [
                            "Organic Chemistry series must be completed before Cell Biology.",
                            "A minimum GPA of 2.0 is required in all major coursework."
                        ];
                        checklist = {
                            major_prep: ["CHEM 121", "CHEM 122", "MATH 150", "CHEM 311", "CHEM 312", "CHEM 314", "CHEM 315", "PHYS 100", "PHYS 101"],
                            major_core: ["BIOL 200", "BIOL 201", "BIOL 202", "BIOL 300", "BIOL 302", "BIOL 303", "BIOL 400", "BIOL 499"],
                            upper_division_ge: ["UD GE Area B", "UD GE Area C", "UD GE Area D"],
                            other_requirements: ["Biology Electives", "120 Total Units"]
                        };
                    } else if (lower.includes('psych') || lower.includes('behavior') || lower.includes('counsel') || lower.includes('sociol')) {
                        majorName = "Psychology";
                        semesters = [
                            {
                                term: "Semester 1",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "PSY 100", title: "Introduction to Psychology", units: 3, category: "Major Preparation", prereqs: "None" },
                                    { code: "GE Area A2", title: "Written Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area C1", title: "Arts", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area E", title: "Lifelong Learning", units: 3, category: "GE", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 2",
                                standing: "Freshman",
                                recommended_units: 15,
                                courses: [
                                    { code: "PSY 213", title: "Developmental Psychology", units: 3, category: "Major Core", prereqs: "PSY 100" },
                                    { code: "MATH 105", title: "College Algebra", units: 4, category: "Major Preparation", prereqs: "Placement" },
                                    { code: "GE Area A1", title: "Oral Communication", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area A3", title: "Critical Thinking", units: 5, category: "GE", prereqs: "GE Area A2" }
                                ]
                            },
                            {
                                term: "Semester 3",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "PSY 202", title: "Research Methods in Psychology", units: 3, category: "Major Preparation", prereqs: "PSY 100" },
                                    { code: "PSY 300", title: "Statistical Methods in Psychology", units: 4, category: "Major Preparation", prereqs: "MATH 105" },
                                    { code: "GE Area B1", title: "Physical Science", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area B3", title: "Science Lab Component", units: 1, category: "GE", prereqs: "None" },
                                    { code: "GE Area C2", title: "Humanities", units: 4, category: "GE", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 4",
                                standing: "Sophomore",
                                recommended_units: 15,
                                courses: [
                                    { code: "PSY 220", title: "Physiological Psychology", units: 3, category: "Major Core", prereqs: "PSY 100" },
                                    { code: "GE Area B2", title: "Life Science", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area D", title: "Social Sciences", units: 3, category: "GE", prereqs: "None" },
                                    { code: "GE Area F", title: "Ethnic Studies", units: 3, category: "GE", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 5",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "PSY 310", title: "History and Systems of Psych", units: 3, category: "Major Core", prereqs: "PSY 100, PSY 202" },
                                    { code: "PSY 318", title: "Cognitive Psychology", units: 3, category: "Major Core", prereqs: "PSY 202" },
                                    { code: "UD GE Area C", title: "Upper-Division Humanities", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "Psych UD Elective 1", title: "Upper-Division Psych Elective", units: 3, category: "Option", prereqs: "Varies" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 6",
                                standing: "Junior",
                                recommended_units: 15,
                                courses: [
                                    { code: "PSY 312", title: "Social Psychology", units: 3, category: "Major Core", prereqs: "PSY 100" },
                                    { code: "PSY 317", title: "Theories of Personality", units: 3, category: "Major Core", prereqs: "PSY 100" },
                                    { code: "UD GE Area D", title: "Upper-Division Social Sciences", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "Psych UD Elective 2", title: "Upper-Division Psych Elective", units: 3, category: "Option", prereqs: "Varies" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 7",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "PSY 400", title: "Advanced Research Methods", units: 4, category: "Major Core", prereqs: "Senior Standing, PSY 300, PSY 202" },
                                    { code: "Psych UD Elective 3", title: "Upper-Division Psych Elective", units: 3, category: "Option", prereqs: "Varies" },
                                    { code: "UD GE Area B", title: "Upper-Division Science/Math", units: 3, category: "GE", prereqs: "Junior Standing" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 5, category: "Other", prereqs: "None" }
                                ]
                            },
                            {
                                term: "Semester 8",
                                standing: "Senior",
                                recommended_units: 15,
                                courses: [
                                    { code: "PSY 490", title: "Senior Seminar Capstone", units: 3, category: "Major Core", prereqs: "Senior Standing, PSY 400" },
                                    { code: "Psych UD Elective 4", title: "Upper-Division Psych Elective", units: 3, category: "Option", prereqs: "Varies" },
                                    { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" },
                                    { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                ]
                            }
                        ];
                        notes = [
                            "PSY 202 and PSY 300 are prerequisites for all 400-level coursework.",
                            "A grade of C or better is required in PSY 100, 202, and 300."
                        ];
                        checklist = {
                            major_prep: ["PSY 100", "PSY 202", "PSY 300", "MATH 105"],
                            major_core: ["PSY 213", "PSY 220", "PSY 310", "PSY 318", "PSY 312", "PSY 317", "PSY 400", "PSY 490"],
                            upper_division_ge: ["UD GE Area B", "UD GE Area C", "UD GE Area D"],
                            other_requirements: ["Psychology Electives", "120 Total Units"]
                        };
                    } else {
                        // Check if we can generate dynamically
                        const majorLookup = [
                            { keywords: ['political', 'pols'], name: 'Political Science', prefix: 'POLS' },
                            { keywords: ['anthropology', 'anth'], name: 'Anthropology', prefix: 'ANTH' },
                            { keywords: ['chicana', 'chicano'], name: 'Chicana/o Studies', prefix: 'CHS' },
                            { keywords: ['communication', 'comm'], name: 'Communication', prefix: 'COMM' },
                            { keywords: ['dance'], name: 'Dance Studies', prefix: 'DNCE' },
                            { keywords: ['economics', 'econ'], name: 'Economics', prefix: 'ECON' },
                            { keywords: ['english', 'engl'], name: 'English', prefix: 'ENGL' },
                            { keywords: ['global'], name: 'Global Studies', prefix: 'GLST' },
                            { keywords: ['history', 'hist'], name: 'History', prefix: 'HIST' },
                            { keywords: ['liberal studies'], name: 'Liberal Studies', prefix: 'LS' },
                            { keywords: ['performing arts'], name: 'Performing Arts', prefix: 'PA' },
                            { keywords: ['sociology', 'soc'], name: 'Sociology', prefix: 'SOC' },
                            { keywords: ['spanish', 'span'], name: 'Spanish', prefix: 'SPAN' },
                            { keywords: ['theatre'], name: 'Theatre and Performance Studies', prefix: 'PATH' },
                            { keywords: ['applied physics'], name: 'Applied Physics', prefix: 'PHYS' },
                            { keywords: ['chemistry', 'chem'], name: 'Chemistry', prefix: 'CHEM' },
                            { keywords: ['early childhood', 'ecs'], name: 'Early Childhood Studies', prefix: 'ECS' },
                            { keywords: ['environmental', 'esrm'], name: 'Environmental Science & Resource Management', prefix: 'ESRM' },
                            { keywords: ['information technology', 'it'], name: 'Information Technology', prefix: 'IT' },
                            { keywords: ['mathematics', 'math'], name: 'Mathematics', prefix: 'MATH' },
                            { keywords: ['mechatronics'], name: 'Mechatronics Engineering', prefix: 'EMEC' },
                            { keywords: ['physics'], name: 'Physics', prefix: 'PHYS' },
                            { keywords: ['health science', 'hlth'], name: 'Health Science', prefix: 'HLTH' },
                            { keywords: ['nursing', 'nurs'], name: 'Nursing', prefix: 'NURS' },
                            { keywords: ['art'], name: 'Art', prefix: 'ART' }
                        ];

                        let matchedMajor = null;
                        for (const item of majorLookup) {
                            if (item.keywords.some(k => lower.includes(k))) {
                                matchedMajor = item;
                                break;
                            }
                        }

                        if (matchedMajor) {
                            const p = matchedMajor.prefix;
                            majorName = matchedMajor.name;
                            semesters = [
                                {
                                    term: "Semester 1",
                                    standing: "Freshman",
                                    recommended_units: 15,
                                    courses: [
                                        { code: `${p} 100`, title: `Introduction to ${majorName}`, units: 3, category: "Major Preparation", prereqs: "None" },
                                        { code: "GE Area A2", title: "Written Communication", units: 3, category: "GE", prereqs: "None" },
                                        { code: "GE Area C1", title: "Arts", units: 3, category: "GE", prereqs: "None" },
                                        { code: "GE Area E", title: "Lifelong Learning", units: 3, category: "GE", prereqs: "None" },
                                        { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                    ]
                                },
                                {
                                    term: "Semester 2",
                                    standing: "Freshman",
                                    recommended_units: 15,
                                    courses: [
                                        { code: `${p} 150`, title: `Foundations of ${majorName}`, units: 3, category: "Major Preparation", prereqs: `${p} 100` },
                                        { code: "GE Area A1", title: "Oral Communication", units: 3, category: "GE", prereqs: "None" },
                                        { code: "GE Area A3", title: "Critical Thinking", units: 3, category: "GE", prereqs: "GE Area A2" },
                                        { code: "GE Area B4", title: "Quantitative Reasoning", units: 3, category: "GE", prereqs: "Placement" },
                                        { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                    ]
                                },
                                {
                                    term: "Semester 3",
                                    standing: "Sophomore",
                                    recommended_units: 15,
                                    courses: [
                                        { code: `${p} 200`, title: `Research Methods in ${majorName}`, units: 3, category: "Major Preparation", prereqs: `${p} 150` },
                                        { code: "GE Area B1", title: "Physical Science", units: 3, category: "GE", prereqs: "None" },
                                        { code: "GE Area B3", title: "Science Lab Component", units: 1, category: "GE", prereqs: "None" },
                                        { code: "GE Area C2", title: "Humanities", units: 3, category: "GE", prereqs: "None" },
                                        { code: "Elective", title: "General Elective", units: 5, category: "Other", prereqs: "None" }
                                    ]
                                },
                                {
                                    term: "Semester 4",
                                    standing: "Sophomore",
                                    recommended_units: 15,
                                    courses: [
                                        { code: `${p} 210`, title: `Intermediate Seminar in ${majorName}`, units: 3, category: "Major Core", prereqs: `${p} 200` },
                                        { code: "GE Area B2", title: "Life Science", units: 3, category: "GE", prereqs: "None" },
                                        { code: "GE Area D", title: "Social Sciences", units: 3, category: "GE", prereqs: "None" },
                                        { code: "GE Area F", title: "Ethnic Studies", units: 3, category: "GE", prereqs: "None" },
                                        { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                    ]
                                },
                                {
                                    term: "Semester 5",
                                    standing: "Junior",
                                    recommended_units: 15,
                                    courses: [
                                        { code: `${p} 300`, title: `Advanced Topics in ${majorName}`, units: 3, category: "Major Core", prereqs: `${p} 210` },
                                        { code: `${p} 310`, title: `${majorName} Theory`, units: 3, category: "Major Core", prereqs: `${p} 210` },
                                        { code: "UD GE Area C", title: "Upper-Division Humanities", units: 3, category: "GE", prereqs: "Junior Standing" },
                                        { code: "Option Course 1", title: `${majorName} Concentration Elective`, units: 3, category: "Option", prereqs: "Varies" },
                                        { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                    ]
                                },
                                {
                                    term: "Semester 6",
                                    standing: "Junior",
                                    recommended_units: 15,
                                    courses: [
                                        { code: `${p} 320`, title: "Applied Research Design", units: 3, category: "Major Core", prereqs: `${p} 300` },
                                        { code: `${p} 330`, title: "Specialized Seminar", units: 3, category: "Major Core", prereqs: `${p} 310` },
                                        { code: "UD GE Area D", title: "Upper-Division Social Sciences", units: 3, category: "GE", prereqs: "Junior Standing" },
                                        { code: "Option Course 2", title: `${majorName} Concentration Elective`, units: 3, category: "Option", prereqs: "Varies" },
                                        { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                    ]
                                },
                                {
                                    term: "Semester 7",
                                    standing: "Senior",
                                    recommended_units: 15,
                                    courses: [
                                        { code: `${p} 400`, title: `Advanced Seminar in ${majorName}`, units: 3, category: "Major Core", prereqs: "Senior Standing" },
                                        { code: `${p} 410`, title: `${majorName} Internship / Project`, units: 3, category: "Major Core", prereqs: "Senior Standing" },
                                        { code: "UD GE Area B", title: "Upper-Division Science/Math", units: 3, category: "GE", prereqs: "Junior Standing" },
                                        { code: "Option Course 3", title: `${majorName} Concentration Elective`, units: 3, category: "Option", prereqs: "Varies" },
                                        { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" }
                                    ]
                                },
                                {
                                    term: "Semester 8",
                                    standing: "Senior",
                                    recommended_units: 15,
                                    courses: [
                                        { code: `${p} 499`, title: `${majorName} Senior Capstone`, units: 3, category: "Major Core", prereqs: `${p} 400` },
                                        { code: "Option Course 4", title: `${majorName} Concentration Elective`, units: 3, category: "Option", prereqs: "Varies" },
                                        { code: "Elective", title: "Upper-Division General Elective", units: 3, category: "Other", prereqs: "None" },
                                        { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" },
                                        { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                    ]
                                }
                            ];
                            notes = [
                                `${p} courses require a grade of C- or better to count toward the major.`,
                                `Students should meet with their ${majorName} academic advisor each semester.`
                            ];
                            checklist = {
                                major_prep: [`${p} 100`, `${p} 150`, `${p} 200`],
                                major_core: [`${p} 210`, `${p} 300`, `${p} 310`, `${p} 320`, `${p} 400`, `${p} 410`, `${p} 499`],
                                upper_division_ge: ["UD GE Area B", "UD GE Area C", "UD GE Area D"],
                                other_requirements: ["4 Concentration Courses", "120 Total Units"]
                            };
                        } else {
                            // Default to Computer Science
                            majorName = "Computer Science";
                            semesters = [
                                {
                                    term: "Semester 1",
                                    standing: "Freshman",
                                    recommended_units: 14,
                                    courses: [
                                        { code: "COMP 150", title: "Object-Oriented Programming", units: 4, category: "Major Core", prereqs: "None" },
                                        { code: "MATH 150", title: "Calculus I", units: 4, category: "Major Preparation", prereqs: "None" },
                                        { code: "GE Area A2", title: "Written Communication", units: 3, category: "GE", prereqs: "None" },
                                        { code: "GE Area C1", title: "Arts", units: 3, category: "GE", prereqs: "None" }
                                    ]
                                },
                                {
                                    term: "Semester 2",
                                    standing: "Freshman",
                                    recommended_units: 15,
                                    courses: [
                                        { code: "COMP 162", title: "Data Structures", units: 4, category: "Major Core", prereqs: "COMP 150" },
                                        { code: "MATH 151", title: "Calculus II", units: 4, category: "Major Preparation", prereqs: "MATH 150" },
                                        { code: "GE Area A1", title: "Oral Communication", units: 3, category: "GE", prereqs: "None" },
                                        { code: "GE Area A3", title: "Critical Thinking", units: 4, category: "GE", prereqs: "GE Area A2" }
                                    ]
                                },
                                {
                                    term: "Semester 3",
                                    standing: "Sophomore",
                                    recommended_units: 15,
                                    courses: [
                                        { code: "COMP 232", title: "Computer Organization", units: 4, category: "Major Core", prereqs: "COMP 162" },
                                        { code: "MATH 230", title: "Discrete Mathematics", units: 3, category: "Major Preparation", prereqs: "MATH 150" },
                                        { code: "GE Area B1", title: "Physical Science", units: 3, category: "GE", prereqs: "None" },
                                        { code: "GE Area B3", title: "Science Lab Component", units: 1, category: "GE", prereqs: "None" },
                                        { code: "GE Area D", title: "Social Sciences", units: 4, category: "GE", prereqs: "None" }
                                    ]
                                },
                                {
                                    term: "Semester 4",
                                    standing: "Sophomore",
                                    recommended_units: 15,
                                    courses: [
                                        { code: "COMP 262", title: "Algorithms", units: 4, category: "Major Core", prereqs: "COMP 162" },
                                        { code: "COMP 362", title: "Operating Systems", units: 4, category: "Major Core", prereqs: "COMP 232" },
                                        { code: "GE Area B2", title: "Life Science", units: 3, category: "GE", prereqs: "None" },
                                        { code: "GE Area C2", title: "Humanities", units: 4, category: "GE", prereqs: "None" }
                                    ]
                                },
                                {
                                    term: "Semester 5",
                                    standing: "Junior",
                                    recommended_units: 16,
                                    courses: [
                                        { code: "COMP 350", title: "Software Engineering", units: 4, category: "Major Core", prereqs: "COMP 262" },
                                        { code: "COMP 370", title: "Database Systems", units: 3, category: "Major Core", prereqs: "COMP 162" },
                                        { code: "MATH 300", title: "Probability & Statistics", units: 3, category: "Major Preparation", prereqs: "MATH 151" },
                                        { code: "UD GE Area C", title: "Upper-Division Arts/Hum", units: 3, category: "GE", prereqs: "Junior Standing" },
                                        { code: "Option Course 1", title: "CS Concentration Elective", units: 3, category: "Option", prereqs: "COMP 262" }
                                    ]
                                },
                                {
                                    term: "Semester 6",
                                    standing: "Junior",
                                    recommended_units: 15,
                                    courses: [
                                        { code: "COMP 362", title: "Computer Architecture", units: 3, category: "Major Core", prereqs: "COMP 232" },
                                        { code: "Option Course 2", title: "CS Concentration Elective", units: 3, category: "Option", prereqs: "COMP 262" },
                                        { code: "UD GE Area D", title: "Upper-Division Social Sci.", units: 3, category: "GE", prereqs: "Junior Standing" },
                                        { code: "GE Area F", title: "Ethnic Studies", units: 3, category: "GE", prereqs: "None" },
                                        { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                    ]
                                },
                                {
                                    term: "Semester 7",
                                    standing: "Senior",
                                    recommended_units: 15,
                                    courses: [
                                        { code: "COMP 491", title: "Capstone Project I", units: 3, category: "Major Core", prereqs: "COMP 350" },
                                        { code: "Option Course 3", title: "Advanced CS Elective", units: 3, category: "Option", prereqs: "COMP 362" },
                                        { code: "UD GE Area B", title: "Upper-Division Science/Math", units: 3, category: "GE", prereqs: "Junior Standing" },
                                        { code: "Elective", title: "Upper-Division Elective", units: 3, category: "Other", prereqs: "None" },
                                        { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                    ]
                                },
                                {
                                    term: "Semester 8",
                                    standing: "Senior",
                                    recommended_units: 15,
                                    courses: [
                                        { code: "COMP 499", title: "Capstone Project II", units: 3, category: "Major Core", prereqs: "COMP 491" },
                                        { code: "Option Course 4", title: "Advanced CS Elective", units: 3, category: "Option", prereqs: "None" },
                                        { code: "Elective", title: "Upper-Division Elective", units: 3, category: "Other", prereqs: "None" },
                                        { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" },
                                        { code: "Elective", title: "General Elective", units: 3, category: "Other", prereqs: "None" }
                                    ]
                                }
                            ];
                            notes = [
                                "Minimum C- grade required in COMP 150 & COMP 162.",
                                "COMP 162 is a pre-requisite for all 300-level core courses."
                            ];
                            checklist = {
                                major_prep: ["COMP 150", "COMP 162", "MATH 150", "MATH 151", "MATH 230", "MATH 300"],
                                major_core: ["COMP 232", "COMP 262", "COMP 362", "COMP 350", "COMP 370", "COMP 491", "COMP 499"],
                                upper_division_ge: ["UD GE Area B", "UD GE Area C", "UD GE Area D"],
                                other_requirements: ["Senior Capstone", "120 Total Units", "40 Upper-Division Units"]
                            };
                        }
                    }

                    const generatedJson = JSON.stringify({
                        major_name: majorName,
                        catalog_year: catalogYear,
                        total_units: totalUnits,
                        semesters: semesters,
                        notes: notes,
                        checklist: checklist
                    }, null, 2);

                    resolve({
                        answer: `Here is a custom advising flowchart generated by the LLM for a **${majorName}** major.

\`\`\`json-flowchart
${generatedJson}
\`\`\`

You can click the button below to display and interact with this roadmap visually.`,
                        sources: [],
                        sessionId: sessionId,
                        type: 'normal'
                    });
                    return;
                }

                // 4. Normal queries
                if (lower.includes('register') || lower.includes('registration') || lower.includes('class')) {
                    resolve({
                        answer: "You can register for classes online via the **[myCI portal](https://myci.csuci.edu)**. Navigate to the **CI Records** system, check your enrollment appointment time under your Student Center, and then click **Add Classes**. For registration rules and course selections, refer to the **[CSUCI_Catalog_2025.pdf](https://catalog.csuci.edu/)** and **[Registration_Guide.pdf](https://www.csuci.edu/records-registration/index.htm)**.",
                        sources: [
                            { title: 'CSUCI_Catalog_2025.pdf', url: 'https://catalog.csuci.edu/' },
                            { title: 'Registration_Guide.pdf', url: 'https://www.csuci.edu/records-registration/index.htm' }
                        ],
                        sessionId: sessionId,
                        type: 'normal'
                    });
                } else if (lower.includes('deadline') || lower.includes('add') || lower.includes('drop')) {
                    resolve({
                        answer: "For the current semester, the last day to add or drop a course without instructor signature is the end of the **third week of instruction**. Dropping after this date requires a serious and compelling reason. Always check key milestones in the **[Academic_Calendar.pdf](https://www.csuci.edu/records-registration/academic-calendar.htm)** to avoid financial or academic penalties.",
                        sources: [
                            { title: 'Academic_Calendar.pdf', url: 'https://www.csuci.edu/records-registration/academic-calendar.htm' }
                        ],
                        sessionId: sessionId,
                        type: 'normal'
                    });
                } else if (lower.includes('financial') || lower.includes('aid') || lower.includes('scholarship') || lower.includes('summer')) {
                    resolve({
                        answer: "CSUCI offers financial aid support for summer semesters, but you must register for at least 6 units. Keep in mind that FAFSA or CADAA submissions must be updated. Reach out to the Financial Aid office in Sage Hall, call **(805) 437-8530**, or consult the **[Financial_Aid_Handbook.pdf](https://www.csuci.edu/financialaid/)**.",
                        sources: [
                            { title: 'Financial_Aid_Handbook.pdf', url: 'https://www.csuci.edu/financialaid/types-of-aid/index.htm' }
                        ],
                        sessionId: sessionId,
                        type: 'normal'
                    });
                } else {
                    resolve({
                        answer: "CSUCI provides numerous resources to support your path to graduation, including peer tutoring, writing support, and career counseling. You can coordinate your studies by accessing the major degree charts in the **[CSUCI_Catalog_2025.pdf](https://catalog.csuci.edu/)** or booking a check-in via your myCI portal.",
                        sources: [
                            { title: 'CSUCI_Catalog_2025.pdf', url: 'https://catalog.csuci.edu/' }
                        ],
                        sessionId: sessionId,
                        type: 'normal'
                    });
                }
            }, delay);
        });
    }

    // --- Live API Engine ---
    async function getLiveResponse(messageText) {
        const url = apiUrlInput.value.trim();
        if (!url) {
            throw new Error('Please configure a valid API Endpoint URL in the sidebar settings.');
        }

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: messageText,
                sessionId: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP Server Error (${response.status})`);
        }

        const data = await response.json();
        
        let answer = data.answer;
        let type = data.type || 'normal';

        if (!answer && data.escalation) {
            type = 'escalation';
            const esc = data.escalation;
            answer = `I couldn't find an answer to your question in our documents, so I am connecting you with a human advisor.\n\n**Escalated Office:** ${esc.office}\n**Phone:** ${esc.contact.phone}\n**Website:** [${esc.office} Website](${esc.contact.url})\n\nAn email/ticket has been routed to them with your query. You can also reach out to them directly.`;
        }

        if (!answer) {
            answer = 'No response details received.';
        }

        return {
            answer: answer,
            sources: data.sources || [],
            sessionId: data.sessionId || sessionId,
            type: type
        };
    }

    // Initialize Connection Status indicator
    updateStatus();
});
