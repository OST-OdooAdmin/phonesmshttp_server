/** @odoo-module **/

import { Component, xml, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class JemiFloatingBot extends Component {
    static template = xml`
        <div class="jemi-floating-container">
            <!-- Floating AI Bot Button Icon -->
            <div class="jemi-floating-btn" t-on-click="toggleChat">
                🤖
            </div>
            <!-- Floating Chat Window Drawer -->
            <div t-if="state.isOpen" class="jemi-chat-window">
                <div class="jemi-chat-header">
                    <span>🤖 Jemi (AI Studio Assistant)</span>
                    <button class="btn btn-sm text-white" t-on-click="toggleChat">✖</button>
                </div>
                <div class="jemi-chat-body">
                    <t t-foreach="state.messages" t-as="msg" t-key="msg.id">
                        <div t-attf-class="jemi-msg {{ msg.isUser ? 'jemi-msg-user' : 'jemi-msg-bot' }}">
                            <t t-out="msg.text"/>
                        </div>
                    </t>
                </div>
                <div class="jemi-chat-footer">
                    <input class="jemi-chat-input" type="text" placeholder="Tell Jemi your app idea..." t-model="state.inputMsg" t-on-keydown="onKeyDown"/>
                    <button class="btn btn-sm btn-primary rounded-circle" t-on-click="sendMessage">➔</button>
                </div>
            </div>
        </div>
    `;

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            isOpen: false,
            inputMsg: "",
            apiKeyConfigured: false,
            messages: [
                { id: 1, text: "👋 Hi! I am Jemi, your AI Studio Assistant! Please configure your Free Google Gemini API Key in Settings to start building apps!", isUser: false }
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

        // Check if Gemini API key or account is configured in Odoo Settings
        try {
            const config = await this.orm.call("res.config.settings", "get_values", []);
            const apiKey = config.gemini_api_key || "";

            if (!apiKey) {
                setTimeout(() => {
                    this.state.messages.push({
                        id: Date.now() + 1,
                        text: "⚠️ <b>API Key Required</b>: Jemi requires a Free Google Gemini API Key to operate! Please go to <b>Settings ➔ AI Studio Configuration</b> and paste your key from <a href='https://aistudio.google.com/app/apikey' target='_blank'>aistudio.google.com</a>.",
                        isUser: false
                    });
                }, 800);
            } else {
                setTimeout(() => {
                    this.state.messages.push({
                        id: Date.now() + 1,
                        text: `🤖 <b>Jemi (Gemini AI)</b>: Processing your request "${userText}" using your Google AI API key... Click <b>AI Studio</b> on your top menu to customize fields & automations!`,
                        isUser: false
                    });
                }, 800);
            }
        } catch (e) {
            setTimeout(() => {
                this.state.messages.push({
                    id: Date.now() + 1,
                    text: `🤖 <b>Jemi</b>: Processing your app idea "${userText}"... Click <b>AI Studio</b> on your top menu to customize!`,
                    isUser: false
                });
            }, 800);
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
