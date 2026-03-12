const vscode = require('vscode');
const { exec } = require('child_process');
const path = require('path');

function activate(context) {
  console.log('PEX extension is now active!');

  context.subscriptions.push(
    vscode.commands.registerCommand('pex.run', () => runPEXCommand('run'))
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('pex.check', () => runPEXCommand('check'))
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('pex.ast', () => runPEXCommand('ast'))
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('pex.plan', () => runPEXCommand('plan'))
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('pex.lint', () => runPEXCommand('lint'))
  );
}

function runPEXCommand(command) {
  const editor = vscode.window.activeTextEditor;
  
  if (!editor) {
    vscode.window.showErrorMessage('No file is open');
    return;
  }

  const filePath = editor.document.fileName;
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  
  if (!workspaceFolder) {
    vscode.window.showErrorMessage('No workspace folder is open');
    return;
  }

  const ext = path.extname(filePath).toLowerCase();
  if (ext !== '.pi') {
    vscode.window.showErrorMessage('Not a PEX file (.pi)');
    return;
  }

  const pexCommand = `pex ${command} "${filePath}"`;
  
  const outputChannel = vscode.window.createOutputChannel(`PEX: ${command.toUpperCase()}`);
  outputChannel.show(true);
  
  outputChannel.appendLine(`🏃 Running: ${pexCommand}`);
  outputChannel.appendLine(`📁 File: ${filePath}`);
  outputChannel.appendLine('─'.repeat(50));

  exec(pexCommand, { cwd: workspaceFolder }, (error, stdout, stderr) => {
    if (stdout) {
      outputChannel.appendLine(stdout);
    }
    
    if (stderr) {
      outputChannel.appendLine(stderr);
    }
    
    if (error) {
      outputChannel.appendLine(`❌ Error: ${error.message}`);
      vscode.window.showWarningMessage(`PEX ${command} completed with errors. Check output.`);
    } else {
      vscode.window.showInformationMessage(`PEX ${command} completed successfully!`);
    }
  });
}

function deactivate() {}

module.exports = { activate, deactivate };
