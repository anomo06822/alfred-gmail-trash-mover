
# agents.md

## 專案名稱
Alfred Gmail Trash Mover

## 目標（Goals）
- 透過 **Alfred Workflow**，使用者輸入 Gmail 查詢字串（Gmail Search Query）。
- 由 **Python 腳本**呼叫 **Gmail API**，根據查詢結果把符合的郵件**搬移到垃圾桶（TRASH）**。
- 支援 **乾跑（dry-run）** 顯示命中數量與示例，不進行實際搬移。
- 支援配額與錯誤回退、日誌輸出、最小權限原則。

## 主要功能（Scope）
1. Alfred Workflow：
   - Keyword：`gdel`（可調整）
   - 將 `{query}` 參數傳遞給 Python 腳本。
   - 執行完成後以 macOS 通知顯示結果（成功/錯誤/乾跑統計）。
2. Python 腳本：
   - 首次執行處理 OAuth 2.0，產生 `token.json`（**儲存在使用者 Home 下的專案資料夾**）。
   - 以 `users.messages.list` 搜尋符合查詢的 message IDs。
   - 以 `users.messages.batchModify` 將郵件加上 `TRASH` 標籤（即移至垃圾桶）。
   - 參數：
     - `--query "<gmail search>"`（必填）
     - `--dry-run`（選用）
     - `--limit N`（選用；測試時限制處理筆數）
     - `--log-level INFO|DEBUG`（選用）
   - 批次處理、指數回退、錯誤處理與整潔輸出。
3. 文件：
   - 安裝與設定教學（README）
   - 安全性建議與最小權限（SCOPES）
   - Alfred 導入與設定步驟

## 非目標（Out of Scope）
- **永久刪除（hard delete）**、標籤管理 UI、雲端部署、自動排程（可後續擴充）。
- 多帳號切換（初版支援單一 Google 帳號）。

## 目錄結構（Deliverables）
（略，請見主回覆）

## CLI 規格（src/gmail_trash.py）
- 參數
  - `--query`（str，必填）：Gmail 查詢語法
  - `--dry-run`（flag，預設 False）
  - `--limit`（int，選填）
  - `--log-level`（enum：`INFO`/`DEBUG`，預設 `INFO`）

（略，其餘與主回覆內容一致）

## 結語
此 agents.md 可交由 codexcli 執行自動產生專案，搭配 Alfred 可在 macOS 上快速建立 Gmail 自動垃圾桶清理工作流。
