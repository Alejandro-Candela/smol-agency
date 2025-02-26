/**
 * Punto de entrada principal para la aplicación
 */

// Main application logic
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the UI
    ui.init();
    
    // Limpiar los archivos de la carpeta output al cargar la página
    clearOutputFiles();
    
    // Check if the agent is ready
    checkAgentStatus();
    
    // Set up the refresh button for files
    setupFilesRefresh();
});

/**
 * Limpiar todos los archivos de la carpeta output
 */
async function clearOutputFiles() {
    try {
        const response = await fetch('/api/clear_output_files');
        const data = await response.json();
        console.log('Output files cleared:', data.message);
    } catch (error) {
        console.error('Error clearing output files:', error);
    }
}

/**
 * Check if the agent is ready
 * Polls the agent status endpoint until it's ready
 */
async function checkAgentStatus() {
    let isReady = false;
    
    const statusCheckInterval = setInterval(async () => {
        try {
            isReady = await api.isReady();
            
            if (isReady) {
                clearInterval(statusCheckInterval);
                console.log('Agent is ready');
                ui.elements.messageInput.placeholder = 'Escribe tu mensaje...';
                ui.elements.messageInput.disabled = false;
                ui.elements.sendButton.disabled = false;
            }
        } catch (error) {
            console.error('Error checking agent status:', error);
        }
    }, 1000);
}

/**
 * Setup files refresh functionality
 */
function setupFilesRefresh() {
    // Get the refresh button
    const refreshButton = document.getElementById('refresh-files');
    
    if (refreshButton) {
        // Add event listener to the refresh button
        refreshButton.addEventListener('click', () => {
            console.log('Refreshing files');
            
            // Show loading indicator
            const filesContainer = document.getElementById('files-sidebar');
            if (filesContainer) {
                filesContainer.innerHTML = `
                    <div class="loading-files">
                        <p>Actualizando archivos disponibles...</p>
                    </div>
                `;
            }
            
            // Use the updateFilesList function from ui.js
            ui.updateFilesList();
        });
        
        // Refresh files on page load
        setTimeout(() => {
            // Trigger a click on the refresh button
            refreshButton.click();
        }, 1000);
        
        // Listen for events that might indicate new files
        document.addEventListener('filesGenerated', (event) => {
            console.log('Files generated event received in main.js:', event.detail);
            refreshButton.click();
        });
    }
} 