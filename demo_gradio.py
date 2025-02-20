import time


def demo_gradio(manager_agent, height=450, dark_mode=True):
    """
    Launches a simple Gradio-based chat interface.

    Parameters:
        height (int, optional): The height of the chatbot widget. Default is 450.
        dark_mode (bool, optional): Flag to enable dark mode. Default is True.
    """
    try:
        import gradio as gr
    except ImportError:
        raise Exception("Please install gradio: pip install gradio")

    js = """function () {
      gradioURL = window.location.href
      if (!gradioURL.endsWith('?__theme={theme}')) {
        window.location.replace(gradioURL + '?__theme={theme}');
      }
    }"""

    if dark_mode:
        js = js.replace("{theme}", "dark")
    else:
        js = js.replace("{theme}", "light")

    message_file_names = None

    with gr.Blocks(js=js) as demo:
        chatbot = gr.Chatbot(height=height)
        with gr.Row():
            with gr.Column(scale=9):
                msg = gr.Textbox(label="Your Message", lines=4)
            with gr.Column(scale=1):
                file_upload = gr.Files(label="Files", type="filepath")
        button = gr.Button(value="Send", variant="primary")

        def handle_file_upload(file_list):
            nonlocal message_file_names
            message_file_names = []
            if file_list:
                try:
                    for file_obj in file_list:
                        message_file_names.append(file_obj.name)
                    return "Files uploaded: " + ", ".join(message_file_names)
                except Exception as e:
                    print(f"Error: {e}")
                    return str(e)

            return "No files uploaded"

        def user(user_message, history):
            if not user_message:
                return user_message, history

            if history is None:
                history = []

            original_user_message = user_message
            user_message = f"👤 User: {user_message.strip()}"

            nonlocal message_file_names
            if message_file_names:
                user_message += "\n\n📎 Files:\n" + "\n".join(message_file_names)

            return original_user_message, history + [[user_message, None]]

        def bot(original_message, history):
            nonlocal message_file_names
            
            # Process the message using the agent
            response = manager_agent.chat(original_message)
            
            message_file_names = []
            history.append((None, response))
            return "", history

        button.click(
            user,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot]
        ).then(
            bot, [msg, chatbot], [msg, chatbot]
        )
        file_upload.change(handle_file_upload, file_upload)
        msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot, [msg, chatbot], [msg, chatbot]
        )

        demo.queue()

    demo.launch(share=True, debug=True)
    return demo