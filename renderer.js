const statusPill = document.getElementById('statusPill');
const taskList = document.getElementById('taskList');
const promptInput = document.getElementById('promptInput');
const submitTask = document.getElementById('submitTask');
const assistantMessage = document.getElementById('assistantMessage');
const character = document.getElementById('character');
const approvalModal = document.getElementById('approvalModal');
const approvalText = document.getElementById('approvalText');
const approveAction = document.getElementById('approveAction');
const denyAction = document.getElementById('denyAction');

const safeActions = {
  'open-app': async ({ appName }) => {
    await window.electronAPI.openApp(appName);
  },
  'open-url': async ({ url }) => {
    await window.electronAPI.openUrl(url);
  },
  'open-folder': async ({ path }) => {
    await window.electronAPI.openFolder(path);
  }
};

let pendingAction = null;

const setCharacterState = (state) => {
  character.classList.remove('idle', 'working', 'thinking', 'happy');
  character.classList.add(state);
};

const setStatus = (text) => {
  statusPill.textContent = text;
};

const pushTask = (kind, text, status = 'neutral') => {
  const card = document.createElement('div');
  card.className = `task-card ${status}`;
  card.innerHTML = `
    <div class="task-badge">${kind}</div>
    <p>${text}</p>
  `;
  taskList.prepend(card);
};

const prettyActionText = (task) => {
  if (task.type === 'open-app') return `Open the approved app: ${task.payload.appName}`;
  if (task.type === 'open-url') return `Open URL: ${task.payload.url}`;
  if (task.type === 'open-folder') return `Open folder: ${task.payload.path}`;
  return task.description;
};

const parseTask = (rawText) => {
  const text = rawText.trim();

  if (!text) {
    return null;
  }

  const openAppMatch = text.match(/(?:open|launch|start)\s+([a-zA-Z0-9_.-]+)/i);
  if (openAppMatch) {
    return {
      type: 'open-app',
      description: `Open ${openAppMatch[1]}`,
      payload: { appName: openAppMatch[1] }
    };
  }

  const urlMatch = text.match(/(?:open|visit|browse|go to)\s+(https?:\/\/[^\s]+)/i) ||
    text.match(/(https?:\/\/[^\s]+)/i);
  if (urlMatch) {
    return {
      type: 'open-url',
      description: `Open ${urlMatch[1]}`,
      payload: { url: urlMatch[1] }
    };
  }

  const folderMatch = text.match(/(?:open|show)\s+(?:folder|directory)\s+([A-Za-z0-9_./-]+)/i);
  if (folderMatch) {
    return {
      type: 'open-folder',
      description: `Open folder ${folderMatch[1]}`,
      payload: { path: folderMatch[1] }
    };
  }

  return {
    type: 'unsupported',
    description: 'I can only safely help with approved app launches, browser URLs, or folder openings.',
    payload: {}
  };
};

const openApprovalModal = (task) => {
  approvalText.textContent = prettyActionText(task);
  approvalModal.classList.remove('hidden');
  approvalModal.setAttribute('aria-hidden', 'false');
  pendingAction = task;
};

const closeApprovalModal = () => {
  approvalModal.classList.add('hidden');
  approvalModal.setAttribute('aria-hidden', 'true');
  pendingAction = null;
};

const addTask = (task) => {
  pushTask(task.type === 'unsupported' ? 'SYSTEM' : 'TASK', task.description, 'pending');
  openApprovalModal(task);
};

const approveAndExecute = async () => {
  if (!pendingAction) {
    return;
  }

  const action = pendingAction;
  closeApprovalModal();
  setStatus('Working');
  setCharacterState('working');
  assistantMessage.textContent = `Starting: ${prettyActionText(action)}`;

  pushTask('APPROVAL', `Approved: ${prettyActionText(action)}`, 'approved');

  try {
    const executor = safeActions[action.type];
    if (!executor) {
      throw new Error('This action is not allowed in the safe execution list.');
    }

    await executor(action.payload);
    setCharacterState('happy');
    setStatus('Success');
    assistantMessage.textContent = `Completed safely: ${prettyActionText(action)}`;
    pushTask('RESULT', `Success: ${prettyActionText(action)}`, 'approved');
  } catch (error) {
    setCharacterState('thinking');
    setStatus('Blocked');
    assistantMessage.textContent = error.message || 'The action was blocked.';
    pushTask('BLOCKED', `Blocked: ${prettyActionText(action)}`, 'rejected');
  }
};

const denyActionRequest = () => {
  closeApprovalModal();
  setCharacterState('thinking');
  setStatus('Denied');
  assistantMessage.textContent = 'Action denied. No system changes or file removals were performed.';
  if (pendingAction) {
    pushTask('DENIED', `Denied: ${prettyActionText(pendingAction)}`, 'rejected');
  }
  pendingAction = null;
};

submitTask.addEventListener('click', () => {
  const raw = promptInput.value;
  if (!raw.trim()) return;

  const task = parseTask(raw);
  if (!task) return;

  if (task.type === 'unsupported') {
    assistantMessage.textContent = task.description;
    pushTask('SYSTEM', task.description, 'rejected');
    setCharacterState('thinking');
    setStatus('Needs direction');
    return;
  }

  promptInput.value = '';
  addTask(task);
  setCharacterState('thinking');
  setStatus('Pending approval');
  assistantMessage.textContent = `Review the action before I run it.`;
});

approveAction.addEventListener('click', approveAndExecute);
denyAction.addEventListener('click', denyActionRequest);

setCharacterState('idle');
setStatus('Idle');
