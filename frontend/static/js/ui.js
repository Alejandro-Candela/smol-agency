/**
 * UI module for handling DOM interactions and updates
 */

const ui = {
    /**
     * Initialize UI event listeners
     */
    init: () => {
        // Element references
        ui.elements = {
            chatbox: document.getElementById('chatbox'),
            messageInput: document.getElementById('message-input'),
            sendButton: document.getElementById('send-button'),
            fileUpload: document.getElementById('file-upload'),
            fileList: document.getElementById('file-list'),
            themeToggle: document.getElementById('theme-toggle-btn'),
            typingIndicator: document.getElementById('typing-indicator'),
            inputTokens: document.getElementById('input-tokens'),
            outputTokens: document.getElementById('output-tokens'),
            // Templates
            userMessageTemplate: document.getElementById('user-message-template'),
            agentMessageTemplate: document.getElementById('agent-message-template'),
            toolCallTemplate: document.getElementById('tool-call-template')
        };

        // Setup event listeners
        ui.setupEventListeners();
        
        // Auto-resize textarea
        ui.elements.messageInput.addEventListener('input', (e) => {
            utils.autoResizeTextarea(e.target);
        });
    },

    /**
     * Setup all UI event listeners
     */
    setupEventListeners: () => {
        // Send message on button click
        ui.elements.sendButton.addEventListener('click', ui.handleSendMessage);
        
        // Send message on Enter key (but not with Shift+Enter)
        ui.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                ui.handleSendMessage();
            }
        });
        
        // File upload handler
        ui.elements.fileUpload.addEventListener('change', ui.handleFileUpload);
        
        // Theme toggle
        ui.elements.themeToggle.addEventListener('click', ui.toggleTheme);
    },

    /**
     * Handle sending a message
     */
    handleSendMessage: async () => {
        const message = ui.elements.messageInput.value.trim();
        if (!message) return;
        
        // Get uploaded files
        const fileElements = document.querySelectorAll('.file-item');
        const uploadedFiles = [];
        fileElements.forEach(fileEl => {
            const fileId = fileEl.dataset.fileId;
            if (fileId && window.uploadedFiles && window.uploadedFiles[fileId]) {
                uploadedFiles.push(window.uploadedFiles[fileId]);
            }
        });
        
        // Add user message to chat
        ui.addUserMessage(message, uploadedFiles.map(f => f.name));
        
        // Clear input and file list
        ui.elements.messageInput.value = '';
        ui.elements.messageInput.style.height = 'auto';
        ui.elements.fileList.innerHTML = '';
        window.uploadedFiles = {};
        
        // Show typing indicator
        ui.showTypingIndicator();
        
        // Send message to the server
        try {
            // If there are files, first upload them
            if (uploadedFiles.length > 0) {
                await api.uploadFiles(uploadedFiles);
            }
            
            // Start streaming response
            const responseStream = await api.streamResponse(message, uploadedFiles);
            
            // Process the stream
            const reader = responseStream.getReader();
            const decoder = new TextDecoder();
            
            // Create a new agent message container
            const agentMessageId = utils.generateId();
            const agentMessageEl = ui.createAgentMessage('', agentMessageId);
            ui.elements.chatbox.appendChild(agentMessageEl);
            
            let currentToolCall = null;
            let responseText = '';
            let currentMessageEl = agentMessageEl;
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                
                // Split chunks by newline to properly handle multiple JSON objects
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (!line.trim()) continue;
                    
                    try {
                        // Parse the line as JSON
                        const data = JSON.parse(line);
                        
                        // Update token counts if available
                        if (data.input_tokens) {
                            ui.elements.inputTokens.textContent = data.input_tokens;
                        }
                        if (data.output_tokens) {
                            ui.elements.outputTokens.textContent = data.output_tokens;
                        }
                        
                        // Handle different types of messages
                        switch (data.type) {
                            case 'text':
                                // For regular text, add to the current message
                                responseText += data.content;
                                const textEl = currentMessageEl.querySelector('.message-text');
                                textEl.innerHTML = utils.markdownToHtml(responseText);
                                break;
                                
                            case 'step_number':
                                // For step numbers, create a new message with the step info
                                const stepEl = ui.addAgentMessage(data.content);
                                currentMessageEl = stepEl;
                                responseText = data.content;
                                break;
                                
                            case 'token_info':
                                // For token information, add as metadata
                                const metadataEl = currentMessageEl.querySelector('.message-metadata');
                                if (metadataEl) {
                                    metadataEl.innerHTML = data.content;
                                }
                                break;
                                
                            case 'separator':
                                // Add a separator line
                                const separatorEl = document.createElement('hr');
                                separatorEl.className = 'message-separator';
                                ui.elements.chatbox.appendChild(separatorEl);
                                // Reset for the next message
                                responseText = '';
                                break;
                                
                            case 'tool_start':
                                // Create a new tool call container
                                currentToolCall = ui.createToolCall(data.tool_name);
                                const toolTextEl = currentMessageEl.querySelector('.message-text');
                                toolTextEl.appendChild(currentToolCall);
                                break;
                                
                            case 'tool_content':
                                // Add content to the current tool call
                                if (currentToolCall) {
                                    const contentEl = currentToolCall.querySelector('.tool-content');
                                    contentEl.innerHTML += utils.markdownToHtml(data.content);
                                }
                                break;
                                
                            case 'tool_result':
                                // Add result to the current tool call and mark as done
                                if (currentToolCall) {
                                    const resultEl = currentToolCall.querySelector('.tool-result');
                                    resultEl.innerHTML = utils.markdownToHtml(data.content);
                                    resultEl.classList.remove('hidden');
                                    
                                    const statusEl = currentToolCall.querySelector('.tool-status');
                                    statusEl.textContent = 'Completado';
                                    statusEl.classList.remove('pending');
                                    statusEl.classList.add('done');
                                    
                                    currentToolCall = null;
                                }
                                break;
                                
                            case 'tool_error':
                                // Add error to the current tool call
                                if (currentToolCall) {
                                    const resultEl = currentToolCall.querySelector('.tool-result');
                                    resultEl.innerHTML = `<span class="error-text">Error: ${data.content}</span>`;
                                    resultEl.classList.remove('hidden');
                                    
                                    const statusEl = currentToolCall.querySelector('.tool-status');
                                    statusEl.textContent = 'Error';
                                    statusEl.classList.remove('pending');
                                    statusEl.classList.add('error');
                                    
                                    currentToolCall = null;
                                }
                                break;
                                
                            case 'error':
                                // Display any general errors
                                ui.addAgentMessage(`Error: ${data.content}`);
                                break;
                        }
                    } catch (e) {
                        console.error('Error parsing chunk:', e, line);
                    }
                }
                
                // Scroll to bottom
                ui.scrollToBottom();
            }
            
            // Hide typing indicator when done
            ui.hideTypingIndicator();
            
            // Add a new chat entry to the history
            chat.addMessage(responseText, 'assistant');
            
        } catch (error) {
            console.error('Error processing response:', error);
            ui.addAgentMessage(`Error: ${error.message}`);
            ui.hideTypingIndicator();
        }
    },

    /**
     * Handle file upload
     * @param {Event} e - The change event
     */
    handleFileUpload: (e) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;
        
        // Store uploaded files
        if (!window.uploadedFiles) {
            window.uploadedFiles = {};
        }
        
        Array.from(files).forEach(file => {
            const fileId = utils.generateId();
            window.uploadedFiles[fileId] = file;
            
            // Create file item
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.dataset.fileId = fileId;
            
            // Add file icon
            const fileIcon = document.createElement('span');
            fileIcon.className = 'file-icon';
            fileIcon.textContent = utils.getFileIcon(file.name);
            fileItem.appendChild(fileIcon);
            
            // Add file name
            const fileName = document.createElement('span');
            fileName.className = 'file-name';
            fileName.textContent = file.name;
            fileItem.appendChild(fileName);
            
            // Add file size
            const fileSize = document.createElement('span');
            fileSize.className = 'file-size';
            fileSize.textContent = utils.formatFileSize(file.size);
            fileItem.appendChild(fileSize);
            
            // Add remove button
            const removeBtn = document.createElement('span');
            removeBtn.className = 'file-remove';
            removeBtn.textContent = '❌';
            removeBtn.addEventListener('click', () => {
                fileItem.remove();
                delete window.uploadedFiles[fileId];
            });
            fileItem.appendChild(removeBtn);
            
            ui.elements.fileList.appendChild(fileItem);
        });
        
        // Reset file input
        e.target.value = '';
    },

    /**
     * Toggle between light and dark theme
     */
    toggleTheme: () => {
        const currentTheme = utils.getTheme();
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        utils.setTheme(newTheme);
    },

    /**
     * Add a user message to the chat
     * @param {string} message - The message content
     * @param {Array} fileNames - Array of file names attached to the message
     */
    addUserMessage: (message, fileNames = []) => {
        // Clone template
        const template = ui.elements.userMessageTemplate.content.cloneNode(true);
        const messageEl = template.querySelector('.user-message');
        
        // Set message content
        const textEl = messageEl.querySelector('.message-text');
        textEl.textContent = message;
        
        // Add files if any
        if (fileNames.length > 0) {
            const filesEl = messageEl.querySelector('.message-files');
            fileNames.forEach(fileName => {
                const fileItem = document.createElement('div');
                fileItem.className = 'message-file';
                
                const fileIcon = document.createElement('span');
                fileIcon.textContent = utils.getFileIcon(fileName);
                fileItem.appendChild(fileIcon);
                
                const fileNameSpan = document.createElement('span');
                fileNameSpan.textContent = fileName;
                fileItem.appendChild(fileNameSpan);
                
                filesEl.appendChild(fileItem);
            });
        }
        
        // Add timestamp
        const timeEl = messageEl.querySelector('.message-time');
        timeEl.textContent = utils.formatDate(new Date());
        
        // Add to chatbox
        ui.elements.chatbox.appendChild(messageEl);
        
        // Scroll to bottom
        ui.scrollToBottom();
    },

    /**
     * Create a new agent message element
     * @param {string} message - The message content
     * @param {string} id - Unique ID for the message
     * @returns {HTMLElement} - The agent message element
     */
    createAgentMessage: (message, id) => {
        // Clone template
        const template = ui.elements.agentMessageTemplate.content.cloneNode(true);
        const messageEl = template.querySelector('.agent-message');
        messageEl.dataset.id = id;
        
        // Set message content if provided
        if (message) {
            const textEl = messageEl.querySelector('.message-text');
            textEl.innerHTML = utils.markdownToHtml(message);
        }
        
        return messageEl;
    },

    /**
     * Add an agent message to the chat
     * @param {string} message - The message content
     * @returns {HTMLElement} - The agent message element
     */
    addAgentMessage: (message) => {
        const id = utils.generateId();
        const messageEl = ui.createAgentMessage(message, id);
        
        // Add to chatbox
        ui.elements.chatbox.appendChild(messageEl);
        
        // Scroll to bottom
        ui.scrollToBottom();
        
        return messageEl;
    },

    /**
     * Create a tool call element
     * @param {string} toolName - The name of the tool
     * @returns {HTMLElement} - The tool call element
     */
    createToolCall: (toolName) => {
        // Clone template
        const template = ui.elements.toolCallTemplate.content.cloneNode(true);
        const toolEl = template.querySelector('.tool-call');
        
        // Set tool name
        const nameEl = toolEl.querySelector('.tool-name');
        nameEl.textContent = toolName;
        
        return toolEl;
    },

    /**
     * Show the typing indicator
     */
    showTypingIndicator: () => {
        ui.elements.typingIndicator.classList.remove('hidden');
    },

    /**
     * Hide the typing indicator
     */
    hideTypingIndicator: () => {
        ui.elements.typingIndicator.classList.add('hidden');
    },

    /**
     * Scroll chat to the bottom
     */
    scrollToBottom: () => {
        ui.elements.chatbox.scrollTop = ui.elements.chatbox.scrollHeight;
    }
};

// Initialize UI when DOM is loaded
document.addEventListener('DOMContentLoaded', ui.init); 