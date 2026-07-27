/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class JemiFloatingBot extends Component {
    static template = "odoo_studio_builder.JemiFloatingBotTemplate";

    setup() {
        this.state = useState({
            isOpen: true,
            isExpanded: false,
            inputMessage: "",
            messages: [
                {
                    sender: "bot",
                    text: "🤖 Jemi (AI Studio Assistant):\nHi! I am Jemi, your AI Studio Assistant powered by Google Gemini!\n\nAsk me anything (e.g. weather, account details, or custom app requirements)!"
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

    async sendMessage() {
        const text = this.state.inputMessage.strip ? this.state.inputMessage.strip() : this.state.inputMessage.trim();
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
                this.state.messages.push({ sender: "bot", text: res.response });
            } else {
                this.state.messages.push({ sender: "bot", text: "⚠️ No response received from Gemini API." });
            }
        } catch (error) {
            this.state.messages.push({
                sender: "bot",
                text: "⚠️ Connection Error: " + (error.message || "Failed to reach Odoo server.")
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
