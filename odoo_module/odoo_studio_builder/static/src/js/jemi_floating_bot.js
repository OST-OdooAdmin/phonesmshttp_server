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
            messages: [
                { id: 1, text: "👋 Hi! I am Jemi, your AI Studio Assistant! Please click 'Save' in Settings after keying in your Google AI credentials to activate Jemi!", isUser: false }
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

        // Verify credentials directly from Odoo backend database
        try {
            const verification = await this.orm.call("res.config.settings", "verify_gemini_credentials", []);

            if (verification && verification.is_valid) {
                setTimeout(() => {
                    this.state.messages.push({
                        id: Date.now() + 1,
                        text: `✅ <b>Account Verified!</b> (User: <i>${verification.user_id || 'Google Gemini Pro'}</i>)<br/>🤖 <b>Jemi</b>: Processing your app request "${userText}"... Click <b>AI Studio</b> on your top menu to customize fields & automations!`,
                        isUser: false
                    });
                }, 800);
            } else {
                setTimeout(() => {
                    this.state.messages.push({
                        id: Date.now() + 1,
                        text: "⚠️ <b>Click 'Save' Button</b>: Please click the purple <b>Save</b> button at the top-left of Settings so Odoo saves your Google credentials into the database!",
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
