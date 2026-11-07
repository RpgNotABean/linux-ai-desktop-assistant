# Linux AI Desktop Assistant

A Linux desktop app prototype for an assistant that:
- has an animated character with task-based motion states
- can open apps and browser tabs
- requires explicit user approval before each action
- blocks destructive or system-changing operations

## Safety rules

This project is intentionally restricted to safe operations only:
- allowed: open app, open browser URL, open folder
- denied: deleting files, modifying system settings, changing permissions, run as root
- every action requires user approval before execution

## Run it locally

```bash
npm install
npm start
```

## What it does

- The assistant accepts commands such as `open firefox`, `launch code`, or `open https://github.com`
- It converts those into a reviewable action request
- The approval modal shows the exact action before it runs
- The character animation changes to match the current action state

## Notes

This is a safe desktop assistant prototype. It does not auto-run destructive commands and does not mutate system configuration without approval.
