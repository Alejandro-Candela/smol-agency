/**
 * Utility functions for the Gradio UI
 */

const utils = {
    /**
     * Format a date to a readable string
     * @param {Date} date - The date to format
     * @returns {string} - The formatted date string
     */
    formatDate: (date) => {
        return new Intl.DateTimeFormat('default', {
            hour: 'numeric',
            minute: 'numeric',
            second: 'numeric',
            hour12: true
        }).format(date);
    },

    /**
     * Get the file size in a readable format
     * @param {number} bytes - The file size in bytes
     * @returns {string} - The formatted file size
     */
    formatFileSize: (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Get the file icon based on the file type
     * @param {string} fileName - The file name
     * @returns {string} - The icon for the file type
     */
    getFileIcon: (fileName) => {
        const extension = fileName.split('.').pop().toLowerCase();
        const icons = {
            pdf: '📄',
            doc: '📄',
            docx: '📄',
            txt: '📝',
            csv: '📊',
            xls: '📊',
            xlsx: '📊',
            ppt: '📊',
            pptx: '📊',
            jpg: '🖼️',
            jpeg: '🖼️',
            png: '🖼️',
            gif: '🖼️',
            mp4: '🎬',
            mp3: '🎵',
            wav: '🎵'
        };
        return icons[extension] || '📁';
    },

    /**
     * Escape HTML entities to prevent XSS
     * @param {string} html - The string to escape
     * @returns {string} - The escaped string
     */
    escapeHtml: (html) => {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    },

    /**
     * Enhanced markdown to HTML conversion
     * @param {string} markdown - The markdown to convert
     * @returns {string} - The HTML string
     */
    markdownToHtml: (markdown) => {
        if (!markdown) return '';
        
        // Preserve certain HTML elements that might be in the markdown (like spans with styling)
        const preservedHtml = [];
        markdown = markdown.replace(/<([^>]+)>([^<]*)<\/\1>/g, (match) => {
            preservedHtml.push(match);
            return `__PRESERVED_HTML_${preservedHtml.length - 1}__`;
        });
        
        // Handle code blocks with language specification
        let html = markdown.replace(/```(\w+)?\s*([\s\S]*?)```/g, (match, lang, code) => {
            const language = lang ? ` class="language-${lang}"` : '';
            return `<pre><code${language}>${utils.escapeHtml(code.trim())}</code></pre>`;
        });
        
        // Handle inline code
        html = html.replace(/`([^`]+)`/g, (match, p1) => {
            return `<code>${utils.escapeHtml(p1)}</code>`;
        });
        
        // Handle headings (h1 to h6)
        html = html.replace(/^(#{1,6})\s+(.+)$/gm, (match, hashes, content) => {
            const level = hashes.length;
            return `<h${level}>${content.trim()}</h${level}>`;
        });
        
        // Handle bold text
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');
        
        // Handle italic text
        html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        html = html.replace(/_([^_]+)_/g, '<em>$1</em>');
        
        // Handle links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        
        // Handle unordered lists
        html = html.replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>');
        
        // Handle ordered lists
        html = html.replace(/^\s*(\d+)\.\s+(.+)$/gm, '<li>$2</li>');
        
        // Group list items
        let inList = false;
        let listType = '';
        const lines = html.split('\n');
        html = lines.map(line => {
            if (line.startsWith('<li>')) {
                if (!inList) {
                    inList = true;
                    listType = line.match(/^\s*(\d+)\./) ? 'ol' : 'ul';
                    return `<${listType}>${line}`;
                }
                return line;
            } else if (inList) {
                inList = false;
                return `</${listType}>${line}`;
            } else {
                return line;
            }
        }).join('\n');
        if (inList) {
            html += `</${listType}>`;
        }
        
        // Handle horizontal rules
        html = html.replace(/^(-{3,}|_{3,}|\*{3,})$/gm, '<hr>');
        
        // Handle paragraphs (but avoid wrapping non-paragraph elements)
        html = html.split('\n\n').map(block => {
            if (block.trim() === '') return '';
            if (block.startsWith('<h') || 
                block.startsWith('<pre') || 
                block.startsWith('<ul') || 
                block.startsWith('<ol') || 
                block.startsWith('<li') || 
                block.startsWith('<hr') ||
                block.startsWith('<blockquote')) {
                return block;
            }
            return `<p>${block.trim()}</p>`;
        }).join('');
        
        // Handle blockquotes
        html = html.replace(/^>\s+(.+)$/gm, '<blockquote>$1</blockquote>');
        
        // Restore preserved HTML
        html = html.replace(/__PRESERVED_HTML_(\d+)__/g, (match, index) => {
            return preservedHtml[parseInt(index)];
        });
        
        return html;
    },

    /**
     * Set the theme (light or dark)
     * @param {string} theme - The theme to set ('light' or 'dark')
     */
    setTheme: (theme) => {
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    },

    /**
     * Get the current theme
     * @returns {string} - The current theme ('light' or 'dark')
     */
    getTheme: () => {
        return localStorage.getItem('theme') || 'light';
    },

    /**
     * Auto-resize a textarea based on its content
     * @param {HTMLTextAreaElement} textarea - The textarea to resize
     */
    autoResizeTextarea: (textarea) => {
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
    },

    /**
     * Create a uniqueId for elements
     * @returns {string} - A unique ID
     */
    generateId: () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }
};

// Initialize theme
document.addEventListener('DOMContentLoaded', () => {
    const currentTheme = utils.getTheme();
    utils.setTheme(currentTheme);
}); 