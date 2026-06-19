import * as vscode from "vscode";
import { ForgeApiClient } from "../services/forge-api";

export class ChatPanel {
  public static currentPanel: ChatPanel | undefined;
  private readonly _panel: vscode.WebviewPanel;
  private readonly _api: ForgeApiClient;
  private _messages: { role: string; content: string }[] = [];

  public static createOrShow(uri: vscode.Uri, api: ForgeApiClient) {
    if (ChatPanel.currentPanel) {
      ChatPanel.currentPanel._panel.reveal(vscode.ViewColumn.Beside);
      return;
    }
    const panel = vscode.window.createWebviewPanel(
      "forgeChat",
      "Forge Chat",
      vscode.ViewColumn.Beside,
      { enableScripts: true }
    );
    ChatPanel.currentPanel = new ChatPanel(panel, api);
  }

  private constructor(panel: vscode.WebviewPanel, api: ForgeApiClient) {
    this._panel = panel;
    this._api = api;
    this._panel.webview.html = this._getHtml();
    this._panel.onDidDispose(() => (ChatPanel.currentPanel = undefined));

    this._panel.webview.onDidReceiveMessage(async (msg) => {
      if (msg.type === "chat") {
        this.appendMessage("user", msg.text);
        const response = await this._api.sendMessage(msg.text);
        this.appendMessage("assistant", response);
      }
    });
  }

  public appendMessage(role: string, content: string) {
    this._messages.push({ role, content });
    this._panel.webview.postMessage({
      type: "message",
      role,
      content,
    });
  }

  private _getHtml(): string {
    return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, sans-serif; background: #111; color: #e5e5e5; display: flex; flex-direction: column; height: 100vh; }
    #messages { flex: 1; overflow-y: auto; padding: 16px; }
    .msg { margin-bottom: 12px; padding: 8px 12px; border-radius: 4px; max-width: 90%; }
    .user { background: #1a1a2e; margin-left: auto; text-align: right; }
    .assistant { background: #1e1e1e; border-left: 2px solid #555; }
    .role { font-size: 11px; color: #888; margin-bottom: 4px; text-transform: uppercase; }
    .content { font-size: 13px; line-height: 1.5; white-space: pre-wrap; }
    #input-bar { display: flex; padding: 12px; border-top: 1px solid #333; }
    #input { flex: 1; background: #1a1a1a; border: 1px solid #333; color: #e5e5e5; padding: 8px 12px; border-radius: 4px; font-size: 13px; outline: none; }
    #send { margin-left: 8px; background: #333; color: #e5e5e5; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
    #send:hover { background: #444; }
  </style>
</head>
<body>
  <div id="messages"></div>
  <div id="input-bar">
    <input id="input" placeholder="Ask Forge..." />
    <button id="send">Send</button>
  </div>
  <script>
    const vscode = acquireVsCodeApi();
    const messages = document.getElementById('messages');
    const input = document.getElementById('input');
    const send = document.getElementById('send');

    function addMessage(role, content) {
      const div = document.createElement('div');
      div.className = 'msg ' + role;
      div.innerHTML = '<div class="role">' + role + '</div><div class="content">' + content.replace(/</g, '&lt;') + '</div>';
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    send.onclick = () => {
      const text = input.value.trim();
      if (!text) return;
      vscode.postMessage({ type: 'chat', text });
      input.value = '';
    };
    input.onkeydown = (e) => { if (e.key === 'Enter') send.onclick(); };

    window.addEventListener('message', (e) => {
      if (e.data.type === 'message') addMessage(e.data.role, e.data.content);
    });
  </script>
</body>
</html>`;
  }
}
