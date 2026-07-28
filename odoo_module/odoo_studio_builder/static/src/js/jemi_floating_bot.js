/** @odoo-module **/

import { Component, useState, onMounted, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class JemiFloatingBot extends Component {
    static template = xml`
        <div class="jemi-bot-container">
            <!-- Floating Launcher Button 🤖 -->
            <div class="jemi-floating-btn" t-on-click="toggleChat" title="Chat with Jemi (AI Studio Assistant)">
                🤖
            </div>

            <!-- Floating Chat Drawer Window -->
            <div t-if="state.isOpen" t-attf-class="jemi-chat-drawer #{state.isExpanded ? 'is-expanded' : ''}">
                <!-- Header -->
                <div class="jemi-chat-header">
                    <span>🤖 Jemi (AI Studio Assistant)</span>
                    <div class="jemi-chat-header-actions">
                        <button class="jemi-action-btn" t-on-click="toggleExpand" t-att-title="state.isExpanded ? 'Contract Window' : 'Expand Window'">
                            <t t-if="state.isExpanded">🗗</t>
                            <t t-else="">⤢</t>
                        </button>
                        <button class="jemi-action-btn" t-on-click="toggleChat" title="Close Window">
                            ✕
                        </button>
                    </div>
                </div>

                <!-- Chat Body -->
                <div class="jemi-chat-body">
                    <t t-foreach="state.messages" t-as="msg" t-key="msg_index">
                        <div t-attf-class="jemi-msg #{msg.sender == 'user' ? 'jemi-msg-user' : 'jemi-msg-bot'}">
                            <div class="jemi-msg-content">
                                <t t-out="msg.text"/>
                            </div>
                            <!-- Copy Button for Bot Responses -->
                            <div t-if="msg.sender == 'bot'" class="jemi-msg-actions">
                                <button class="jemi-copy-btn" t-on-click="() => this.copyToClipboard(msg.text, msg_index)">
                                    <t t-if="msg.copied">✓ Copied!</t>
                                    <t t-else="">📋 Copy Text</t>
                                </button>
                            </div>
                        </div>
                    </t>
                    <div t-if="state.isLoading" class="jemi-msg jemi-msg-bot">
                        🤖 Jemi is thinking... 💭
                    </div>
                </div>

                <!-- Input Footer -->
                <div class="jemi-chat-footer">
                    <input type="text"
                           class="jemi-input"
                           placeholder="Ask Jemi anything or describe your app idea..."
                           t-model="state.inputMessage"
                           t-on-keydown="onKeyPress"/>
                    <button class="jemi-send-btn" t-on-click="sendMessage">
                        ➔
                    </button>
                </div>
            </div>
        </div>
    `;

    setup() {
        this.state = useState({
            isOpen: true,
            isExpanded: false,
            inputMessage: "",
            messages: [
                {
                    sender: "bot",
                    text: "🤖 Jemi (AI Studio Assistant):\nHi! I am Jemi, your AI Studio Assistant powered by Google Gemini!\n\nAsk me anything (e.g. weather, account details, Sarawak food, or custom app requirements)!",
                    copied: false
                }
            ],
            isLoading: false
        });

        onMounted(() => {
            this.verifyAccountCredentials();
        });
    }

    async verifyAccountCredentials() {
        try {
            const res = await rpc("/web/dataset/call_kw/res.config.settings/verify_gemini_credentials", {
                model: "res.config.settings",
                method: "verify_gemini_credentials",
                args: [],
                kwargs: {}
            });
            if (res && res.is_valid) {
                console.log("[Jemi Bot] Account verified:", res);
            }
        } catch (e) {
            console.error("[Jemi Bot] RPC Verification error:", e);
        }
    }

    toggleChat() {
        this.state.isOpen = !this.state.isOpen;
    }

    toggleExpand() {
        this.state.isExpanded = !this.state.isExpanded;
    }

    copyToClipboard(text, msgIndex) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text);
        } else {
            const textarea = document.createElement("textarea");
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand("copy");
            document.body.removeChild(textarea);
        }
        if (this.state.messages[msgIndex]) {
            this.state.messages[msgIndex].copied = true;
            setTimeout(() => {
                if (this.state.messages[msgIndex]) {
                    this.state.messages[msgIndex].copied = false;
                }
            }, 2000);
        }
    }

    async sendMessage() {
        const text = this.state.inputMessage.trim ? this.state.inputMessage.trim() : this.state.inputMessage;
        if (!text || this.state.isLoading) return;

        this.state.messages.push({ sender: "user", text: text });
        this.state.inputMessage = "";
        this.state.isLoading = true;

        try {
            const res = await rpc("/web/dataset/call_kw/res.config.settings/action_chat_with_gemini", {
                model: "res.config.settings",
                method: "action_chat_with_gemini",
                args: [text],
                kwargs: {}
            });

            if (res && res.response) {
                this.state.messages.push({ sender: "bot", text: res.response, copied: false });
            } else {
                this.state.messages.push({ sender: "bot", text: "⚠️ No response received from Gemini API.", copied: false });
            }
        } catch (error) {
            this.state.messages.push({
                sender: "bot",
                text: "⚠️ Connection Error: " + (error.message || "Failed to reach Odoo server."),
                copied: false
            });
        } finally {
            this.state.isLoading = false;
        }
    }

    onKeyPress(ev) {
        if (ev.key === "Enter") {
            this.sendMessage();
        }
    }
}

registry.category("main_components").add("JemiFloatingBot", {
    Component: JemiFloatingBot,
});
