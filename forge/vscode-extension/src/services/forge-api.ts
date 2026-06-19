import * as vscode from "vscode";

export class ForgeApiClient {
  private baseUrl: string;
  private apiKey: string;

  constructor() {
    const config = vscode.workspace.getConfiguration("forge");
    this.baseUrl = config.get<string>("serverUrl", "http://localhost:8000");
    this.apiKey = config.get<string>("apiKey", "");
  }

  private headers(): Record<string, string> {
    const h: Record<string, string> = { "Content-Type": "application/json" };
    if (this.apiKey) {
      h["Authorization"] = `Bearer ${this.apiKey}`;
    }
    return h;
  }

  async sendMessage(message: string, fileContent?: string): Promise<string> {
    try {
      const body: Record<string, string> = { message };
      if (fileContent) {
        body.fileContent = fileContent;
      }
      const resp = await fetch(`${this.baseUrl}/api/v1/chat`, {
        method: "POST",
        headers: this.headers(),
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      return data.response || "No response from Forge.";
    } catch (err) {
      return `Error connecting to Forge: ${err}`;
    }
  }

  async saveDecision(
    title: string,
    decision: string,
    reason: string
  ): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/api/v1/memory/decisions`, {
        method: "POST",
        headers: this.headers(),
        body: JSON.stringify({ title, decision, reason, project_id: "default" }),
      });
    } catch (err) {
      vscode.window.showErrorMessage(`Failed to save decision: ${err}`);
    }
  }

  async getMemories(): Promise<any[]> {
    try {
      const resp = await fetch(`${this.baseUrl}/api/v1/memory/search?q=`, {
        headers: this.headers(),
      });
      const data = await resp.json();
      return data.results || [];
    } catch {
      return [];
    }
  }
}
