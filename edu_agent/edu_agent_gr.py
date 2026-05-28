import gradio as gr
from edu_agent import EduAgent


# ─────────────────────────────────────────────
#  SETUP
# ─────────────────────────────────────────────

async def setup(interview_mode: bool):
    agent = EduAgent(interview=interview_mode)
    await agent.setup()
    return agent, agent.get_initial_chat(), gr.update(
        value=f"*Mode: {'Interview' if interview_mode else 'Guide'}*"
    )


async def load_app():
    return await setup(True)


async def process_message(agent, message, success_criteria, history):
    if not message.strip():
        return history, agent
    results = await agent.run(message, success_criteria, history)
    return results, agent


async def switch_mode(agent, interview_mode: bool, history):
    """Switch agent mode without resetting conversation."""
    if agent:
        agent.set_mode(interview=interview_mode)
        mode_label = "Interview Mode" if interview_mode else "Guide Mode"
        return agent, gr.update(value=f"✅ Switched to **{mode_label}**"), history or agent.get_initial_chat()
    return agent, gr.update(value="⚠️ Agent not initialized yet."), history or []


async def reset(interview_mode: bool):
    new_agent = EduAgent(interview=interview_mode)
    await new_agent.setup()
    return "", "", new_agent.get_initial_chat(), new_agent, gr.update(
        value=f"*Mode: {'Interview' if interview_mode else 'Guide'}*"
    )


def free_resources(agent):
    try:
        if agent:
            agent.cleanup()
    except Exception as e:
        print(f"Cleanup error: {e}")


# ─────────────────────────────────────────────
#  UI
# ─────────────────────────────────────────────

with gr.Blocks(title="EduAgent") as ui:

    gr.Markdown("""
    # 🎓 EduAgent
    ### Autonomous AI Platform for German University Applications
    *Helping South Asian students navigate the German university application process*
    """)

    agent_state = gr.State(delete_callback=free_resources)

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="EduAgent",
                height=450,
                placeholder="EduAgent will greet you once initialized...",
            )

        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Agent Mode")

            interview_toggle = gr.Checkbox(
                label="Interview Mode",
                value=True,
                info="ON = structured intake interview | OFF = free expert guide"
            )

            mode_status = gr.Markdown("*Mode: Interview*")

            gr.Markdown("---")
            gr.Markdown("### 📋 Session")
            success_criteria = gr.Textbox(
                label="Success Criteria (optional)",
                placeholder="Leave blank for smart defaults",
                lines=3,
            )

            gr.Markdown("---")
            gr.Markdown("""
            **Interview Mode**
            Agent collects your full profile step by step — one question at a time.
            
            **Guide Mode**  
            Ask anything about German university applications freely.
            """)

    with gr.Row():
        message = gr.Textbox(
            show_label=False,
            placeholder="Type your message here...",
            scale=4,
        )
        go_button = gr.Button("Send →", variant="primary", scale=1)

    with gr.Row():
        switch_button = gr.Button("Switch Mode", variant="secondary")
        reset_button = gr.Button("Reset Session", variant="stop")

    # ── EVENT HANDLERS ───────────────────────────

    ui.load(load_app, inputs=[], outputs=[agent_state, chatbot, mode_status])

    # Update mode status label when toggle changes
    interview_toggle.change(
        lambda v: f"*Mode: {'Interview' if v else 'Guide'}*",
        inputs=[interview_toggle],
        outputs=[mode_status]
    )

    go_button.click(
        process_message,
        inputs=[agent_state, message, success_criteria, chatbot],
        outputs=[chatbot, agent_state],
    ).then(lambda: "", outputs=[message])

    message.submit(
        process_message,
        inputs=[agent_state, message, success_criteria, chatbot],
        outputs=[chatbot, agent_state],
    ).then(lambda: "", outputs=[message])

    switch_button.click(
        switch_mode,
        inputs=[agent_state, interview_toggle, chatbot],
        outputs=[agent_state, mode_status, chatbot],
    )

    reset_button.click(
        reset,
        inputs=[interview_toggle],
        outputs=[message, success_criteria, chatbot, agent_state, mode_status],
    )


ui.launch(
    inbrowser=True,
    theme=gr.themes.Default(primary_hue="blue", neutral_hue="slate"),
    css="""
    .mode-badge { font-size: 0.85rem; padding: 4px 10px; border-radius: 8px; }
    .header-title { font-size: 1.6rem; font-weight: 700; }
    """,
)
