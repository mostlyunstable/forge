import * as vscode from "vscode";
import { ForgeApiClient } from "./services/forge-api";
import { ChatPanel } from "./providers/webview";
import { MemoryTreeProvider } from "./providers/tree-view";

export function activate(context: vscode.ExtensionContext) {
  const api = new ForgeApiClient();

  const treeProvider = new MemoryTreeProvider(api);
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("forge-memories", treeProvider)
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forge.chat", () => {
      ChatPanel.createOrShow(context.extensionUri, api);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forge.explainFile", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage("No active file to explain.");
        return;
      }
      const content = editor.document.getText();
      const filePath = editor.document.fileName;
      const response = await api.sendMessage("Explain this file", content);
      ChatPanel.createOrShow(context.extensionUri, api);
      ChatPanel.currentPanel?.appendMessage("assistant", response);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forge.explainRepo", async () => {
      const response = await api.sendMessage("Explain this repository");
      ChatPanel.createOrShow(context.extensionUri, api);
      ChatPanel.currentPanel?.appendMessage("assistant", response);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forge.findSimilarBug", async () => {
      const description = await vscode.window.showInputBox({
        prompt: "Describe the bug",
        placeHolder: "e.g., JWT refresh token failure on timezone change",
      });
      if (!description) return;
      const response = await api.sendMessage(`Find similar bugs: ${description}`);
      ChatPanel.createOrShow(context.extensionUri, api);
      ChatPanel.currentPanel?.appendMessage("assistant", response);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forge.summarizeWork", async () => {
      const response = await api.sendMessage("Summarize today's work");
      ChatPanel.createOrShow(context.extensionUri, api);
      ChatPanel.currentPanel?.appendMessage("assistant", response);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forge.saveDecision", async () => {
      const title = await vscode.window.showInputBox({
        prompt: "Decision title",
        placeHolder: "e.g., Use FastAPI over Flask",
      });
      if (!title) return;
      const decision = await vscode.window.showInputBox({
        prompt: "What was decided?",
      });
      if (!decision) return;
      const reason = await vscode.window.showInputBox({
        prompt: "Why?",
      });
      await api.saveDecision(title, decision, reason || "");
      vscode.window.showInformationMessage(`Decision saved: ${title}`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forge.projectTimeline", async () => {
      const response = await api.sendMessage("Show project timeline");
      ChatPanel.createOrShow(context.extensionUri, api);
      ChatPanel.currentPanel?.appendMessage("assistant", response);
    })
  );
}

export function deactivate() {}
