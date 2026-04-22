import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface MemoryItem {
    id: number;
    content: string;
    category: string;
    confidence: number;
    timestamp: string;
    source: string;
    tags?: string;
}

function getProjectName(): string {
    const config = vscode.workspace.getConfiguration('crossagentmemory');
    const configured = config.get<string>('project');
    if (configured && configured.trim()) {
        return configured;
    }
    const workspace = vscode.workspace.workspaceFolders?.[0];
    if (workspace) {
        return workspace.name;
    }
    return 'default';
}

function getCliPath(): string {
    const config = vscode.workspace.getConfiguration('crossagentmemory');
    const customPath = config.get<string>('cliPath');
    if (customPath && customPath.trim()) {
        return customPath;
    }
    return 'crossagentmemory';
}

async function runMemagent(args: string[]): Promise<string> {
    const project = getProjectName();
    const cli = getCliPath();
    const cmd = `${cli} ${args.join(' ')} --project "${project}"`;
    try {
        const { stdout } = await execAsync(cmd);
        return stdout;
    } catch (err: any) {
        const fallback = `python -m crossagentmemory.cli ${args.join(' ')} --project "${project}"`;
        const { stdout } = await execAsync(fallback);
        return stdout;
    }
}

async function checkInstallation(): Promise<boolean> {
    try {
        await runMemagent(['--version']);
        return true;
    } catch {
        return false;
    }
}

function escapeHtml(text: string): string {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

class MemoryTreeProvider implements vscode.TreeDataProvider<MemoryTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<MemoryTreeItem | undefined | void> = new vscode.EventEmitter<MemoryTreeItem | undefined | void>();
    readonly onDidChangeTreeData: vscode.Event<MemoryTreeItem | undefined | void> = this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: MemoryTreeItem): vscode.TreeItem {
        return element;
    }

    async getChildren(): Promise<MemoryTreeItem[]> {
        try {
            const result = await runMemagent(['recall', '--limit', '20']);
            const lines = result.split('\n').filter(l => l.trim());
            const items: MemoryTreeItem[] = [];

            for (const line of lines) {
                const match = line.match(/^\s*#?(\d+)\s+\[(\w+)\]\s+(.+?)(?:\s+\(confidence:\s*([\d.]+)\))?\s*$/i);
                if (match) {
                    const [, id, category, content, confidence] = match;
                    items.push(new MemoryTreeItem(
                        parseInt(id, 10),
                        content.trim(),
                        category,
                        parseFloat(confidence || '1'),
                        ''
                    ));
                }
            }
            return items;
        } catch {
            return [new MemoryTreeItem(0, 'Unable to load memories. Is crossagentmemory installed?', 'error', 0, '', true)];
        }
    }
}

class MemoryTreeItem extends vscode.TreeItem {
    constructor(
        public readonly memoryId: number,
        public readonly content: string,
        public readonly category: string,
        public readonly confidence: number,
        public readonly timestamp: string,
        public readonly isError: boolean = false
    ) {
        super(content.length > 60 ? content.substring(0, 60) + '...' : content, vscode.TreeItemCollapsibleState.None);
        this.id = String(memoryId);
        this.tooltip = `${content}\nCategory: ${category}\nConfidence: ${confidence.toFixed(2)}`;
        this.description = `${category} · ${confidence.toFixed(2)}`;
        this.contextValue = 'memory';

        const iconMap: Record<string, string> = {
            fact: 'notebook',
            decision: 'git-branch',
            action: 'run',
            preference: 'settings',
            error: 'error'
        };
        this.iconPath = new vscode.ThemeIcon(iconMap[category] || 'circle-outline');

        if (!isError) {
            this.command = {
                command: 'crossagentmemory.recall',
                title: 'Recall Memories'
            };
        }
    }
}

export function activate(context: vscode.ExtensionContext) {
    const treeProvider = new MemoryTreeProvider();
    const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBar.text = '$(history) Memory';
    statusBar.tooltip = 'CrossAgentMemory: Click to recall';
    statusBar.command = 'crossagentmemory.recall';
    statusBar.show();

    // Update status bar with memory count
    async function updateStatusBar() {
        try {
            const result = await runMemagent(['stats']);
            const match = result.match(/total[\s:]+(\d+)/i);
            if (match) {
                statusBar.text = `$(history) ${match[1]} memories`;
            }
        } catch {
            statusBar.text = '$(history) Memory';
        }
    }
    updateStatusBar();

    // Check installation on activate
    checkInstallation().then(installed => {
        if (!installed) {
            vscode.window.showWarningMessage(
                'CrossAgentMemory CLI not found. Install with: pip install crossagentmemory',
                'Dismiss'
            );
        }
    });

    vscode.window.registerTreeDataProvider('crossagentmemory.memories', treeProvider);

    // Capture memory
    const capture = vscode.commands.registerCommand('crossagentmemory.capture', async () => {
        const editor = vscode.window.activeTextEditor;
        let defaultText = '';
        if (editor && !editor.selection.isEmpty) {
            defaultText = editor.document.getText(editor.selection);
        }

        const content = await vscode.window.showInputBox({
            prompt: 'Memory content',
            value: defaultText,
            placeHolder: 'What did you learn or decide?'
        });
        if (!content) { return; }

        const category = await vscode.window.showQuickPick(
            ['fact', 'decision', 'action', 'preference', 'error'],
            { placeHolder: 'Memory category' }
        );
        if (!category) { return; }

        try {
            const result = await runMemagent(['capture', content, '--category', category]);
            vscode.window.showInformationMessage(`Memory captured: ${result.trim()}`);
            treeProvider.refresh();
            updateStatusBar();
        } catch (err: any) {
            vscode.window.showErrorMessage(`Capture failed: ${err.message}`);
        }
    });

    // Capture selection directly
    const captureSelection = vscode.commands.registerCommand('crossagentmemory.captureSelection', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            vscode.window.showWarningMessage('No text selected');
            return;
        }
        const content = editor.document.getText(editor.selection);
        const category = await vscode.window.showQuickPick(
            ['fact', 'decision', 'action', 'preference', 'error'],
            { placeHolder: 'Memory category' }
        );
        if (!category) { return; }

        try {
            const result = await runMemagent(['capture', content, '--category', category, '--source', 'vscode-selection']);
            vscode.window.showInformationMessage(`Captured ${category}: ${result.trim()}`);
            treeProvider.refresh();
            updateStatusBar();
        } catch (err: any) {
            vscode.window.showErrorMessage(`Capture failed: ${err.message}`);
        }
    });

    // Recall memories
    const recall = vscode.commands.registerCommand('crossagentmemory.recall', async () => {
        try {
            const result = await runMemagent(['recall', '--limit', '50']);
            const lines = result.split('\n').filter(l => l.trim());

            let rows = '';
            for (const line of lines) {
                const match = line.match(/^\s*#?(\d+)\s+\[(\w+)\]\s+(.+?)(?:\s+\(confidence:\s*([\d.]+)\))?\s*$/i);
                if (match) {
                    const [, id, category, content, confidence] = match;
                    const badgeColor = {
                        fact: '#4ade80',
                        decision: '#facc15',
                        action: '#60a5fa',
                        preference: '#f472b6',
                        error: '#f87171'
                    }[category] || '#888';
                    rows += `<tr>
                        <td>#${id}</td>
                        <td><span class="badge" style="background:${badgeColor}20;color:${badgeColor};border:1px solid ${badgeColor}40;">${category}</span></td>
                        <td>${escapeHtml(content.trim())}</td>
                        <td>${confidence || '1.0'}</td>
                    </tr>`;
                } else {
                    rows += `<tr><td colspan="4" style="color:#888;padding:.5rem;">${escapeHtml(line)}</td></tr>`;
                }
            }

            const panel = vscode.window.createWebviewPanel(
                'crossagentmemoryRecall',
                'CrossAgentMemory — Recall',
                vscode.ViewColumn.One,
                {}
            );
            panel.webview.html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: system-ui, -apple-system, sans-serif; background: #0f0f23; color: #e0e0e0; margin: 0; padding: 1.5rem; }
  h2 { margin-top: 0; color: #4cc9f0; }
  table { width: 100%; border-collapse: collapse; font-size: .9rem; }
  th, td { text-align: left; padding: .6rem .8rem; border-bottom: 1px solid #333; }
  th { color: #888; text-transform: uppercase; font-size: .75rem; }
  .badge { display: inline-block; padding: .15rem .5rem; border-radius: 4px; font-size: .75rem; font-weight: 600; }
  tr:hover { background: #1a1a2e; }
</style>
</head>
<body>
<h2>Recent Memories — ${escapeHtml(getProjectName())}</h2>
<table>
  <tr><th>ID</th><th>Category</th><th>Content</th><th>Confidence</th></tr>
  ${rows}
</table>
</body>
</html>`;
        } catch (err: any) {
            vscode.window.showErrorMessage(`Recall failed: ${err.message}`);
        }
    });

    // Search memories
    const search = vscode.commands.registerCommand('crossagentmemory.search', async () => {
        const keyword = await vscode.window.showInputBox({
            prompt: 'Search memories',
            placeHolder: 'Keyword...'
        });
        if (!keyword) { return; }

        try {
            const result = await runMemagent(['search', keyword]);
            vscode.window.showInformationMessage(result.trim().substring(0, 200));
        } catch (err: any) {
            vscode.window.showErrorMessage(`Search failed: ${err.message}`);
        }
    });

    // Load context brief
    const load = vscode.commands.registerCommand('crossagentmemory.load', async () => {
        try {
            const result = await runMemagent(['load']);
            await vscode.env.clipboard.writeText(result);
            vscode.window.showInformationMessage('Context brief copied to clipboard! Paste into your agent.');
        } catch (err: any) {
            vscode.window.showErrorMessage(`Load failed: ${err.message}`);
        }
    });

    // Sync CLAUDE.md
    const sync = vscode.commands.registerCommand('crossagentmemory.sync', async () => {
        try {
            const result = await runMemagent(['sync']);
            vscode.window.showInformationMessage(`Synced: ${result.trim()}`);
        } catch (err: any) {
            vscode.window.showErrorMessage(`Sync failed: ${err.message}`);
        }
    });

    // Refresh tree
    const refresh = vscode.commands.registerCommand('crossagentmemory.refresh', async () => {
        treeProvider.refresh();
        updateStatusBar();
    });

    // Open dashboard
    const openDashboard = vscode.commands.registerCommand('crossagentmemory.openDashboard', async () => {
        try {
            await runMemagent(['dashboard']);
            vscode.window.showInformationMessage('Dashboard started at http://localhost:8745');
        } catch (err: any) {
            vscode.window.showErrorMessage(`Dashboard failed: ${err.message}`);
        }
    });

    // Auto-capture on save (if enabled)
    const saveListener = vscode.workspace.onDidSaveTextDocument(async (doc) => {
        const config = vscode.workspace.getConfiguration('crossagentmemory');
        if (!config.get<boolean>('autoCapture')) { return; }

        const relative = vscode.workspace.asRelativePath(doc.uri);
        if (relative.includes('node_modules') || relative.includes('__pycache__')) {
            return;
        }

        try {
            await runMemagent(['capture', `Edited ${relative}`, '--category', 'action', '--tags', 'vscode,auto']);
            treeProvider.refresh();
            updateStatusBar();
        } catch {
            // Silent fail for auto-capture
        }
    });

    context.subscriptions.push(
        capture, captureSelection, recall, search, load, sync, refresh, openDashboard,
        saveListener, statusBar
    );
}

export function deactivate() {}
