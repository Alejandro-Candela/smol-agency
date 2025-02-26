/**
 * Punto de entrada principal para la aplicación
 */

// Verificar si el agente está listo cuando la página carga
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Comprobar si el backend del agente está listo
        const isReady = await api.isReady();
        
        if (!isReady) {
            // Si el agente no está listo, mostrar un mensaje
            const message = "El agente de IA se está inicializando. Por favor, espera un momento...";
            ui.addAgentMessage(message);
            
            // Verificar cada 2 segundos hasta que esté listo
            const checkInterval = setInterval(async () => {
                const ready = await api.isReady();
                if (ready) {
                    clearInterval(checkInterval);
                    ui.addAgentMessage("¡El agente de IA está listo! ¿En qué puedo ayudarte hoy?");
                }
            }, 2000);
        } else {
            // Si el agente está listo, mostrar un mensaje de bienvenida
            ui.addAgentMessage("¡Bienvenido! ¿En qué puedo ayudarte hoy?");
        }
    } catch (error) {
        console.error('Error al verificar el estado del agente:', error);
        ui.addAgentMessage("Hubo un error al conectar con el agente de IA. Por favor, intenta refrescar la página.");
    }
}); 