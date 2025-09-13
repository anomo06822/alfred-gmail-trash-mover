# Alfred Gmail Trash Mover

使用 Alfred Workflow + Gmail API，根據 Gmail 查詢語法將郵件搬移至垃圾桶（加上 TRASH 標籤）。支援乾跑（dry-run）、OAuth2 首次授權、分頁查詢、批次搬移與重試回退。

注意：本工具不會永久刪除郵件（非 hard delete）。

## 先決條件
- macOS（Alfred 僅支援 mac）
- Python 3.9+
- 你已在自己的 GCP 專案啟用 Gmail API，並下載 OAuth Client 憑證 `credentials.json`

## 安裝
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 放置憑證
```
mkdir -p credentials data
# 將 OAuth 用戶端 JSON 放到：
# credentials/credentials.json
```

可選：使用 `.env` 覆寫預設路徑
```
# .env
CONFIG_DIR=data
# CREDENTIALS_PATH=credentials/credentials.json
# TOKEN_PATH=data/token.json
```

## 本地測試
- 乾跑（不搬移，顯示命中數與 3 筆示例）：
```
python src/gmail_trash.py --query "older_than:6m label:promotions" --dry-run
```

- 實際搬移（限制最多 500 封）：
```
python src/gmail_trash.py --query "label:promotions older_than:6m" --limit 500
```

CLI 參數：
- `--query`：必填，Gmail 查詢語法
- `--dry-run`：乾跑模式
- `--limit N`：限制處理筆數（測試用）
- `--log-level INFO|DEBUG`

結束碼：
- `0` 成功
- `1` 輸入錯誤（缺參或 query 空）
- `2` 認證失敗
- `3` API 錯誤/配額
- `4` 其他未預期錯誤

## Alfred Workflow 安裝
1. 在 Alfred 新增 Workflow，設定 Workflow 變數 `PROJECT_DIR` 指向此專案根目錄。
2. 新增 Keyword：`gdel`（可調整）。
3. 連到 Run Script（/bin/bash）：
```
/usr/bin/python3 "$PROJECT_DIR/src/gmail_trash.py" --query "{query}"
```
4. 可選：新增另一個 Keyword `gdel-dry`：
```
/usr/bin/python3 "$PROJECT_DIR/src/gmail_trash.py" --query "{query}" --dry-run
```
5. 將腳本輸出接到 Post Notification 顯示結果。

## 常見問題
- 首次執行會開啟瀏覽器進行 OAuth；授權完成後會在 `data/token.json` 儲存 token。
- 權限只需 `https://www.googleapis.com/auth/gmail.modify`。
- 遇到 `429/5xx` 會自動重試（最多 5 次）。

## 安全性建議
- `credentials/credentials.json` 與 `data/token.json` 請勿提交到版控。
- 使用者檔案權限保持預設（macOS）即可。

## 開發
單元測試（mock service）：
```
python -m unittest -q
```

---

本專案符合以下目標：
- 乾跑輸出命中數與 3 筆示例。
- 實跑將郵件移至垃圾桶（TRASH）。
- 首次執行完成 OAuth，後續免登入。
- 針對 429/5xx 自動重試，其他錯誤清楚輸出。
