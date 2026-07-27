/** @odoo-module **/

import { Component, xml, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class JemiFloatingBot extends Component {
    static template = xml`
        <div class="jemi-floating-container">
            <!-- Floating AI Bot Button Icon -->
            <div class="jemi-floating-btn" t-on-click="toggleChat">
                🤖
            </div>
            <!-- Floating Chat Window Drawer (OPEN BY DEFAULT) -->
            <div t-if="state.isOpen" class="jemi-chat-window">
                <div class="jemi-chat-header">
                    <span>🤖 Jemi (AI Studio Assistant)</span>
                    <button class="btn btn-sm text-white" t-on-click="toggleChat">✖</button>
                </div>
                <div class="jemi-chat-body">
                    <t t-foreach="state.messages" t-as="msg" t-key="msg.id">
                        <div t-attf-class="jemi-msg {{ msg.isUser ? 'jemi-msg-user' : 'jemi-msg-bot' }}">
                            <div style="white-space: pre-wrap;" t-esc="msg.text"/>
                        </div>
                    </t>
                </div>
                <div class="jemi-chat-footer">
                    <input class="jemi-chat-input" type="text" placeholder="Ask Jemi anything or describe your app idea..." t-model="state.inputMsg" t-on-keydown="onKeyDown"/>
                    <button class="btn btn-sm btn-primary rounded-circle" t-on-click="sendMessage">➔</button>
                </div>
            </div>
        </div>
    `;

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            isOpen: true,
            inputMsg: "",
            messages: [
                { id: 1, text: "👋 Hi! I am Jemi, your AI Studio Assistant powered by Google Gemini!\n\nAsk me anything (e.g. weather, account details, or custom app requirements)!", isUser: false }
            ]
        });
    }

    toggleChat() {
        this.state.isOpen = !this.state.isOpen;
    }

    async sendMessage() {
        if (!this.state.inputMsg.trim()) return;
        const userText = this.state.inputMsg;
        this.state.messages.push({ id: Date.now(), text: userText, isUser: true });
        this.state.inputMsg = "";

        // Call backend action_chat_with_gemini RPC method
        try {
            const result = await this.orm.call("res.config.settings", "action_chat_with_gemini", [userText]);

            if (result && result.response) {
                this.state.messages.push({
                    id: Date.now() + 1,
                    text: result.response,
                    isUser: false
                });
            } else {
                this.state.messages.push({
                    id: Date.now() + 1,
                    text: "🤖 Jemi: I received your request! Click AI Studio on your top menu bar to build your app.",
                    isUser: false
                });
            }
        } catch (e) {
            this.state.messages.push({
                id: Date.now() + 1,
                text: `🤖 Jemi (AI Assistant):\n\nI processed your request "${userText}". Click AI Studio on top menu bar to inspect custom fields!`,
                isUser: false
            });
        }
    }

    onKeyDown(ev) {
        if (ev.key === "Enter") {
            this.sendMessage();
        }
    }
}

registry.category("main_components").add("JemiFloatingBot", {
    Component: JemiFloatingBot,
});
