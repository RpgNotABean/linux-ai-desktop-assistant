const $ = (id) => document.getElementById(id);
const input = $('request');
const dialog = $('approval');
const pendingDescription = $('action-description');
const status = $('status');
const bot = $('bot');
const activity = $('activity');
let pending = null;

const appNames = ['firefox', 'chromium', 'chrome', 'nemo', 'xed', 'libreoffice', 'vlc', 'code'];
function parseRequest(text) {
  const value = text.trim();
  const url = value.match(/(?:open|visit|browse|go to)\s+(https?:\/\/\S+)|^(https?:\/\/\S+)$/i);
  if (url) {
    const address = (url[1] || url[2]).replace(/[),.!?]+$/, '');
    return { type: 'open-url', url: address, description: `Open this website in your default browser: ${address}` };
  }
  const app = value.match(/^(?:open|launch|start)\s+([a-z0-9_-]+)$/i);
  if (app && appNames.includes(app[1].toLowerCase())) {
    const name = app[1].toLowerCase();
    return { type: 'open-app', name, description: `Launch the installed app: ${name}` };
  }
  return null;
}
function addActivity(text) {
  const item = document.createElement('li');
  item.textContent = text;
  activity.prepend(item);
}
function setState(state, label, caption) {
  bot.className = `bot ${state}`;
  status.textContent = label;
  $('caption').textContent = caption;
}

$('send').addEventListener('click', () => {
  const action = parseRequest(input.value);
  if (!action) {
    setState('thinking', 'Unsupported', 'I can only open an allowed app or HTTP/HTTPS website.');
    addActivity('Not run: request is outside the safe action list.');
    return;
  }
  pending = action;
  pendingDescription.textContent = action.description;
  dialog.showModal();
});
input.addEventListener('keydown', (event) => { if (event.key === 'Enter') $('send').click(); });

dialog.addEventListener('close', async () => {
  if (!pending) return;
  const action = pending;
  pending = null;
  if (dialog.returnValue !== 'approve') {
    setState('idle', 'Denied', 'No action was taken.');
    addActivity(`Denied: ${action.description}`);
    return;
  }
  setState('working', 'Working', `Working on: ${action.description}`);
  addActivity(`Approved: ${action.description}`);
  try {
    const response = await fetch('/api/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Assistant-Token': document.querySelector('meta[name="assistant-token"]').content },
      body: JSON.stringify(action)
    });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.message || 'Action was blocked.');
    setState('happy', 'Done', result.message);
    addActivity(result.message);
  } catch (error) {
    setState('thinking', 'Blocked', error.message);
    addActivity(`Blocked: ${error.message}`);
  }
});
