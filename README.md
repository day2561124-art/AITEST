# AITEST E4B CPU v2｜模型快取 + 雲端批次呼叫介面

此專案已在 GitHub Actions 4 vCPU 測過 E4B（版本 v1，run #1 成功）。v2 保留可用的 llama.cpp 模型啟動設定，增加模型快取、可辨認請求 ID、測試場景輸入與呼叫腳本。

## 部署（Windows PowerShell，一次即可）

將此 ZIP 解壓到 `C:\Users\day25\AITEST` 根目錄，保留 `.github/workflows` 資料夾：

```powershell
cd C:\Users\day25\AITEST
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\e4b-AITEST-v2.zip" -DestinationPath . -Force
git add .
git commit -m "Add E4B model cache and GitHub bridge"
git push origin main
```

打開 https://github.com/day2561124-art/AITEST/actions/workflows/e4b-cpu-test.yml → **Run workflow**。留空 `scene_base64`，會自動使用 `samples/test-scene.json` 的公開測試場景。

## 快取如何運作

- 快取路徑：`models/Nemotron-3.5-Bolt-E4B-Q4_K_M.gguf`。
- 首次執行 v2 時：沒有快取，需要下載約 6 GB；工作成功後 `actions/cache@v4` 在清理階段上傳模型到 GitHub Cache。
- 下一次使用相同 cache key 時：優先還原快取，節省 Hugging Face 下載時間，但仍需從 GitHub Cache 傳輸檔案、校驗 SHA-256、載入模型。
- 快取不是永久儲存；GitHub 預設 10 GB 免費配額、超過 7 天未使用可被清除。快取儲存/還原效果和速度仍需兩次實測驗證。
- 此版不會沿用 v1 首次執行的模型檔；v1 當時沒有保存快取。

## 批次呼叫腳本

`scripts/github_bridge.py` 會透過 GitHub Actions REST API：啟動 workflow → 找出對應 run → 等待完成 → 下載 artifact → 擷取生成的 `scene.md` 和 `metrics.json`。

需使用授權的 `GH_TOKEN` 環境變數（**不要把 Token 加入 Git**），權限至少包含工作流程所需的 Actions write，以及讀取執行和 artifacts。

```powershell
# 範例：在已配置環境變數 GH_TOKEN 的執行環境啟動「公開測試場景」
python scripts/github_bridge.py --repo day2561124-art/AITEST --out output-github
```

**安全限制：** AITEST 目前是 **PUBLIC（公開）**。絕對不要把私密小說、角色動態記憶或真正的秘密寫進 `scene_base64`、檔案、輸出或 artifact。Base64 **不是加密**。`github_bridge.py` 會拒絕向公開儲存庫傳送自訂場景，只允許使用內建公開測試場景。

若未來採用私人儲存庫，也必須重新測試硬體：GitHub 標準私人儲存庫 Runner 的 CPU/RAM 規格可能低於公開儲存庫。真實小說仍須評估 API 權限、資料保護及 GitHub Runner 配額。

## GPT ↔ E4B 自動合作的真實進度

- ✅ GitHub Actions 能執行 E4B 並輸出文章（v1 已驗證）。
- ✅ v2 已實作快取、API 呼叫腳本與請求匹配機制（本地測試通過）。
- ⏳ v2 尚須推送 GitHub 並再跑兩次，才可確認首次 cache save 和第二次 cache hit。
- ⏳ 現有 ChatGPT GitHub 連接器目前 **不能直接呼叫 workflow_dispatch**，故此腳本本身**不代表本聊天室已能自動觸發它**。正式整合仍需能調用 GitHub API 的雲端橋接服務或連接器。
- ⏳ 目前無法安全傳遞正式小說私人資料到公開 AITEST。正式使用需建立保密的端到端流程。

### 資料流

GPT 提供人物資料和劇情場景 → *具備授權的外部橋接程式* 呼叫 GitHub Actions → E4B 完整撰寫所有角色台詞與旁白 → GitHub artifact 回傳 → GPT 取得結果、審核人物連續性 → 確認後更新 Google Drive。

## 本地測試

```powershell
python -m unittest discover -s tests -v
```

## 專案檔案

- `.github/workflows/e4b-cpu-test.yml`：E4B CPU 工作流程（快取＋按需執行）
- `scripts/prepare_scene.py`：處理公開測試場景的 Base64 JSON 安全解析
- `scripts/github_bridge.py`：GitHub REST API 觸發 / 下載（需外部環境提供 Token）
- `scripts/run_scene.py`：E4B 推論與效能量測
- `scripts/wait_for_server.py`：模型可用性檢測
- `samples/test-scene.json`：可公開測試的場景

## 參考文件

- https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching
- https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event
