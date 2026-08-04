import * as assert from "assert";
import * as vscode from "vscode";
import { ForgeApiClient } from "../services/forge-api";

suite("ForgeApiClient Test Suite", () => {
  vscode.window.showInformationMessage("Start all tests.");

  test("Instantiates correctly", () => {
    const api = new ForgeApiClient();
    assert.ok(api);
  });

  test("getMemories gracefully handles failure", async () => {
    const api = new ForgeApiClient();
    // Assuming backend is not running or we hit a mock, it should return [] instead of crashing
    const memories = await api.getMemories();
    assert.ok(Array.isArray(memories));
  });
});
