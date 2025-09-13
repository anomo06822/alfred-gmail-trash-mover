Alfred Workflow Stub
====================

This folder contains a minimal workflow definition for Alfred.

How to package and import
- Run `bash alfred/pack_workflow.sh` to generate `alfred/GmailTrashMover.alfredworkflow`.
- Double-click the generated `.alfredworkflow` to import into Alfred.
- In the Workflow’s variables, set `PROJECT_DIR` to your project path.

Workflow objects
- Keyword `gdel` → Run Script → Post Notification
- Keyword `gdel-dry` → Run Script (with `--dry-run`) → Post Notification

Notes
- This is a basic stub; you can further customize icons, names, and notifications in Alfred.

