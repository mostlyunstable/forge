import * as vscode from "vscode";
import { ForgeApiClient } from "../services/forge-api";

export class MemoryTreeProvider implements vscode.TreeDataProvider<MemoryItem> {
  private _onDidChangeTreeData =
    new vscode.EventEmitter<MemoryItem | undefined | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private api: ForgeApiClient) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: MemoryItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: MemoryItem): Promise<MemoryItem[]> {
    if (!element) {
      return [
        new MemoryItem("Decisions", vscode.TreeItemCollapsibleState.Expanded, "category"),
        new MemoryItem("Bugs", vscode.TreeItemCollapsibleState.Expanded, "category"),
        new MemoryItem("Preferences", vscode.TreeItemCollapsibleState.Expanded, "category"),
      ];
    }

    if (element.label === "Decisions") {
      const memories = await this.api.getMemories();
      const decisions = memories.filter((m: any) => m.type === "decision");
      return decisions.map(
        (d: any) =>
          new MemoryItem(d.title, vscode.TreeItemCollapsibleState.None, "decision")
      );
    }

    if (element.label === "Bugs") {
      const memories = await this.api.getMemories();
      const bugs = memories.filter((m: any) => m.type === "bug");
      return bugs.map(
        (b: any) =>
          new MemoryItem(b.title, vscode.TreeItemCollapsibleState.None, "bug")
      );
    }

    if (element.label === "Preferences") {
      return [
        new MemoryItem(
          "No preferences yet",
          vscode.TreeItemCollapsibleState.None,
          "empty"
        ),
      ];
    }

    return [];
  }
}

class MemoryItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly itemType: string
  ) {
    super(label, collapsibleState);
    this.contextValue = itemType;
  }
}
