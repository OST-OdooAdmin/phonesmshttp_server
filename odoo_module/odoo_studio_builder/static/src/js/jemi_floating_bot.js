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
                            <!-- Image Attachment Preview if present -->
                            <div t-if="msg.imageUrl" class="jemi-img-attachment">
                                <img t-att-src="msg.imageUrl" alt="Uploaded Image" style="max-width: 100%; border-radius: 8px; margin-bottom: 8px;"/>
                            </div>
                            <div class="jemi-msg-content">
                                <t t-out="msg.text"/>
                            </div>
                            <!-- Copy Button for Bot Responses (Copies Question, Response & Diagnostic Logs) -->
                            <div t-if="msg.sender == 'bot'" class="jemi-msg-actions">
                                <button class="jemi-copy-btn" t-on-click="() => this.copyBothQuestionAndResponseWithLogs(msg_index)">
                                    <t t-if="msg.copied">✓ Copied Q&amp;A + Logs!</t>
                                    <t t-else="">📋 Copy Q&amp;A + Logs</t>
                                </button>
                            </div>
                        </div>
                    </t>
                    <div t-if="state.isLoading" class="jemi-msg jemi-msg-bot">
                        🤖 Jemi is analyzing your request... 💭
                    </div>
                </div>

                <!-- Image Selected Banner -->
                <div t-if="state.pendingImageUrl" class="jemi-pending-img-banner">
                    <span>📷 Image Attached:</span>
                    <img t-att-src="state.pendingImageUrl" style="height: 32px; border-radius: 4px; border: 1px solid #714B67;"/>
                    <button class="jemi-remove-img-btn" t-on-click="removePendingImage">✕</button>
                </div>

                <!-- Input Footer -->
                <div class="jemi-chat-footer">
                    <!-- Image Upload Button 📷 -->
                    <label class="jemi-upload-btn" title="Upload Image / Screenshot to Jemi AI">
                        📷
                        <input type="file" accept="image/*" t-on-change="onImageSelected" style="display: none;"/>
                    </label>
                    <input type="text"
                           class="jemi-input"
                           placeholder="Ask Jemi anything or analyze an image..."
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
            pendingImageBase64: null,
            pendingImageUrl: null,
            messages: [
                {
                    sender: "bot",
                    text: "🤖 Jemi (AI Studio Assistant):\nHi! I am Jemi, your AI Studio Assistant powered by Google Gemini!\n\nAsk me anything, upload images 📷, or describe your custom Odoo app requirements!",
                    copied: false,
                    logInfo: "Initial System Message [Engine: Google Antigravity AI Engine]"
                }
            ],
            isLoading: false,
            credentials: null
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
                this.state.credentials = res;
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

    onImageSelected(ev) {
        const file = ev.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            this.state.pendingImageUrl = e.target.result;
            this.state.pendingImageBase64 = e.target.result.split(",")[1];
        };
        reader.readAsDataURL(file);
    }

    removePendingImage() {
        this.state.pendingImageUrl = null;
        this.state.pendingImageBase64 = null;
    }

    copyBothQuestionAndResponseWithLogs(msgIndex) {
        let fullCombinedText = "";
        
        // 1. User Question
        if (msgIndex > 0 && this.state.messages[msgIndex - 1] && this.state.messages[msgIndex - 1].sender === "user") {
            fullCombinedText += "User Question: " + this.state.messages[msgIndex - 1].text + "\n\n";
        }
        
        // 2. Bot Response
        if (this.state.messages[msgIndex]) {
            fullCombinedText += this.state.messages[msgIndex].text + "\n\n";
        }

        // 3. Diagnostic Logs
        const now = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const cred = this.state.credentials || {};
        const logData = this.state.messages[msgIndex] ? (this.state.messages[msgIndex].logInfo || "Mode: Live AI Execution") : "";

        fullCombinedText += "--- DIAGNOSTIC SYSTEM LOG ---\n";
        fullCombinedText += `Timestamp: ${now}\n`;
        fullCombinedText += `AI Engine Provider: ${cred.provider_label || 'Google Antigravity AI Engine'}\n`;
        fullCombinedText += `Account User ID: ${cred.user_id || '1012374182157'}\n`;
        fullCombinedText += `Organization ID: ${cred.account_id || 'gen-lang-client-0177342458'}\n`;
        fullCombinedText += `API Key Masked: ${cred.masked_key || 'AQ.Ab8RN...7342458'}\n`;
        fullCombinedText += `Execution Status Log: ${logData}`;

        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(fullCombinedText);
        } else {
            const textarea = document.createElement("textarea");
            textarea.value = fullCombinedText;
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
        const imgUrl = this.state.pendingImageUrl;
        const imgBase64 = this.state.pendingImageBase64;

        if (!text && !imgBase64) return;
        if (this.state.isLoading) return;

        const userMsgText = text || "📷 Sent an image for AI analysis";
        this.state.messages.push({ sender: "user", text: userMsgText, imageUrl: imgUrl });
        
        this.state.inputMessage = "";
        this.state.pendingImageUrl = null;
        this.state.pendingImageBase64 = null;
        this.state.isLoading = true;

        try {
            const res = await rpc("/web/dataset/call_kw/res.config.settings/action_chat_with_gemini", {
                model: "res.config.settings",
                method: "action_chat_with_gemini",
                args: [userMsgText, imgBase64 || ""],
                kwargs: {}
            });

            if (res && res.response) {
                this.state.messages.push({
                    sender: "bot",
                    text: res.response,
                    copied: false,
                    logInfo: res.log_info || "Status 200 OK [Google Antigravity AI Engine]"
                });
            } else {
                this.state.messages.push({
                    sender: "bot",
                    text: "⚠️ No response received from Gemini API.",
                    copied: false,
                    logInfo: "Status: Empty Response"
                });
            }
        } catch (error) {
            this.state.messages.push({
                sender: "bot",
                text: "⚠️ Connection Error: " + (error.message || "Failed to reach Odoo server."),
                copied: false,
                logInfo: "Status: RPC Connection Error (" + (error.message || "Failed") + ")"
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
