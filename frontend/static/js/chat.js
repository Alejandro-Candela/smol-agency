/**
 * Módulo de chat para gestionar el historial y las interacciones de chat
 */

const chat = {
    /**
     * Array del historial de chat
     */
    history: [],
    
    /**
     * Inicializar módulo de chat
     */
    init: () => {
        // Eliminar historial de chat al cargar la página
        localStorage.removeItem('chatHistory');
        chat.history = [];
        
        // No cargar el historial guardado, ya que queremos empezar con un chat vacío
        // cada vez que se refresca la página
    },
    
    /**
     * Añadir un mensaje al historial de chat
     * @param {string} content - El contenido del mensaje
     * @param {string} role - El rol del mensaje ('user' o 'assistant')
     * @param {Array} files - Array de nombres de archivos (solo para mensajes de usuario)
     */
    addMessage: (content, role, files = []) => {
        const message = {
            id: utils.generateId(),
            content,
            role,
            timestamp: new Date().toISOString()
        };
        
        if (role === 'user' && files.length > 0) {
            message.files = files;
        }
        
        chat.history.push(message);
        
        // Guardar en almacenamiento local
        localStorage.setItem('chatHistory', JSON.stringify(chat.history));
        
        return message;
    },
    
    /**
     * Limpiar el historial de chat
     */
    clearHistory: async () => {
        try {
            // Llamar a la API para reiniciar la conversación
            await api.resetConversation();
            
            // Limpiar historial local
            chat.history = [];
            localStorage.removeItem('chatHistory');
            
            // Limpiar la interfaz
            ui.elements.chatbox.innerHTML = '';
            
            // Añadir un mensaje de confirmación
            ui.addAgentMessage('El historial de chat ha sido borrado. ¿En qué puedo ayudarte?');
            
            return true;
        } catch (e) {
            console.error('Error al limpiar el historial de chat:', e);
            return false;
        }
    },
    
    /**
     * Exportar historial de chat como JSON
     * @returns {string} - String JSON del historial de chat
     */
    exportHistory: () => {
        return JSON.stringify(chat.history, null, 2);
    }
};

// Inicializar chat cuando se carga el DOM
document.addEventListener('DOMContentLoaded', chat.init); 