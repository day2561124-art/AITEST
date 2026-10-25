# NVIDIA E4B × GitHub Actions CPU 實測

按需啟動 NVIDIA Nemotron 3.5 Bolt E4B（Q4_K_M GGUF），產生**繁體中文人物對話及旁白**。

這是 **CPU 效能驗證專案**，不是 ChatGPT 與模型已自動串接的正式服務。

## 上傳到 AITEST（Windows PowerShell）

1. 下載並解壓 `e4b-AITEST-ready.zip` 到 `C:\Users\day25\AITEST`（確認 `.github` 在 AITEST 根目錄中）。
2. 在 PowerShell 輸入：

   ```powershell
   cd C:\Users\day25\AITEST
   git add .
   git commit -m "Deploy E4B CPU test"
   git push origin main
   ```

3. 開啟 https://github.com/day2561124-art/AITEST/actions，選擇 **E4B CPU dialogue and narration test** → **Run workflow**。
4. 執行完成後到本次執行的 **Artifacts** 下載 `e4b-cpu-result`。

## 檔案說明

- `.github/workflows/e4b-cpu-test.yml`：GitHub Actions 工作流程，手動觸發。
- `scripts/run_scene.py`：讀場景 JSON，呼叫模型，輸出文本及效能資料。
- `scripts/wait_for_server.py`：確認 llama.cpp API 模型已完成載入。
- `samples/test-scene.json`：完全虛構的測試場景，可直接公開。
- `tests/test_run_scene.py`：不下載模型的 Python 單元測試。
- `output/scene.md`：E4B 產生的台詞與旁白（Action 執行時產生）。
- `output/metrics.json`：生成耗時、token 數及速度（Action 執行時產生）。

## 先驗證有沒有跑得動

工作流程會先跑 Python 單元測試，再從 Hugging Face 官方 repo 下載約 **6.18 GB** 的 E4B GGUF 並驗證 SHA-256。

接著用 `ghcr.io/ggml-org/llama.cpp:server` Docker 映像透過 CPU 執行，不用 Ollama，不用 GPU。模型只在當次工作流程內執行，完成就結束。

如有失敗，到 Actions 展開紅色步驟，檢查下載空間、Docker / llama.cpp 模型相容性、RAM 或執行超時；這些問題需以真實執行結果判定。

**公開儲存庫注意事項：** 不要把私人小說正文、角色記憶、API 金鑰提交到 AITEST，測試時先使用內建的虛構場景。GitHub 工作日誌及 Artifact 也可能被其他人存取。後續若要讓 GPT 自動呼叫 E4B，仍需建立安全的私密資料傳輸管道與結果回傳。

## 本機 Ollama 比較

如果你已在本機使用 Ollama 管理 E4B，在 AITEST 根目錄輸入：

```powershell
ollama list
python scripts/run_scene.py --provider ollama --model "<以 ollama list 實際名稱取代>" --scene samples/test-scene.json --out output-local
```

最後可比較 `output-local/metrics.json` 與 Actions 的結果。

## 官方來源

- [NVIDIA E4B GGUF](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-4GB)
- [llama.cpp Docker](https://github.com/ggml-org/llama.cpp/blob/master/docs/docker.md)
- [GitHub-hosted runner 規格](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
