/**
 * API module for communicating with the FastAPI backend
 */

const api = {
    /**
     * API base URL
     */
    baseUrl: '/api',
    
    /**
     * Send a chat message to the agent
     * @param {string} message - The message to send
     * @param {Array} files - Array of files to upload (optional)
     * @returns {Promise} - A promise that resolves with the agent's response
     */
    sendMessage: async (message, files = []) => {
        try {
            const formData = new FormData();
            formData.append('message', message);
            
            // Add files to form data if provided
            files.forEach(file => {
                formData.append('files', file);
            });
            
            const response = await fetch(`${api.baseUrl}/chat`, {
                method: 'POST',
                body: formData,
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return response;
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    },
    
    /**
     * Stream the agent's response
     * @param {string} message - The message to send
     * @param {Array} files - Array of files to upload (optional)
     * @returns {ReadableStream} - A stream of the agent's response
     */
    streamResponse: async (message, files = []) => {
        try {
            const formData = new FormData();
            formData.append('message', message);
            
            // Add files to form data if provided
            files.forEach(file => {
                formData.append('files', file);
            });
            
            const response = await fetch(`${api.baseUrl}/stream`, {
                method: 'POST',
                body: formData,
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return response.body;
        } catch (error) {
            console.error('Error streaming response:', error);
            throw error;
        }
    },
    
    /**
     * Upload files to the backend
     * @param {Array} files - Array of files to upload
     * @returns {Promise} - A promise that resolves with the uploaded file information
     */
    uploadFiles: async (files) => {
        try {
            const formData = new FormData();
            
            files.forEach(file => {
                formData.append('files', file);
            });
            
            const response = await fetch(`${api.baseUrl}/upload`, {
                method: 'POST',
                body: formData,
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return response.json();
        } catch (error) {
            console.error('Error uploading files:', error);
            throw error;
        }
    },
    
    /**
     * Reset the agent's conversation history
     * @returns {Promise} - A promise that resolves when the conversation is reset
     */
    resetConversation: async () => {
        try {
            const response = await fetch(`${api.baseUrl}/reset`, {
                method: 'POST',
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return response.json();
        } catch (error) {
            console.error('Error resetting conversation:', error);
            throw error;
        }
    },
    
    /**
     * Check if the agent is ready
     * @returns {Promise<boolean>} - A promise that resolves with the agent's readiness status
     */
    isReady: async () => {
        try {
            const response = await fetch(`${api.baseUrl}/status`, {
                method: 'GET',
            });
            
            if (!response.ok) {
                return false;
            }
            
            const data = await response.json();
            return data.status === 'ready';
        } catch (error) {
            console.error('Error checking agent status:', error);
            return false;
        }
    }
}; 