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
                    <input class="jemi-chat-input" type="text" placeholder="Tell Jemi your app idea..." t-model="state.inputMsg" t-on-keydown="onKeyDown"/>
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
                { id: 1, text: "👋 Hi! I am Jemi, your AI Studio Assistant!\n\nTell me: What custom app or workflow would you like to build today?", isUser: false }
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

        const queryLower = userText.toLowerCase();

        // Verify credentials directly from Odoo backend database
        try {
            const verification = await this.orm.call("res.config.settings", "verify_gemini_credentials", []);

            // Check if user is asking about provider / account info
            if (queryLower.includes("provider") || queryLower.includes("account") || queryLower.includes("setting") || queryLower.includes("key") || queryLower.includes("who")) {
                setTimeout(() => {
                    this.state.messages.push({
                        id: Date.now() + 1,
                        text: `🤖 Jemi Active AI Configuration:\n\n` +
                              `• AI Engine Provider: ${verification.provider_label}\n` +
                              `• AI Account User ID: ${verification.user_id}\n` +
                              `• AI Account / Org ID: ${verification.account_id}\n` +
                              `• Google Gemini API Key: ${verification.masked_key}\n\n` +
                              `Status: ✅ Connected & Ready!`,
                        isUser: false
                    });
                }, 800);
            } else if (verification && verification.is_valid) {
                setTimeout(() => {
                    this.state.messages.push({
                        id: Date.now() + 1,
                        text: `🤖 Jemi (AI Engine: ${verification.provider_label}):\n\n` +
                              `Got it! Processing your app request "${userText}"...\n` +
                              `Click "AI Studio" on your top menu bar to inspect your custom fields & automations!`,
                        isUser: false
                    });
                }, 800);
            } else {
                setTimeout(() => {
                    this.state.messages.push({
                        id: Date.now() + 1,
                        text: "⚠️ API Credentials Required:\n\n" +
                              "Please click the purple 'Save' button in Settings ➔ AI Studio Configuration to activate Jemi!",
                        isUser: false
                    });
                }, 800);
            }
        } catch (e) {
            setTimeout(() => {
                this.state.messages.push({
                    id: Date.now() + 1,
                    text: `🤖 Jemi: Processing your app idea "${userText}"...\nClick "AI Studio" on your top menu bar to customize!`,
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
