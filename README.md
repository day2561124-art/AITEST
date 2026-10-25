# AITEST｜GPT-6 × NVIDIA Nemotron 3.5 Bolt E4B

此專案使用 GitHub Actions 免費公開儲存庫 CPU Runner、llama.cpp 與 NVIDIA Nemotron 3.5 Bolt E4B（Q4_K_M）。
GPT 負責原作研究、角色記憶、正式世界線、場景規劃與成稿審核；
E4B 負責撰寫人物實際台詞、動作與旁白。

## ChatGPT 原生 GitHub 連接器入口

ChatGPT GitHub 連接器目前能建立 Issue、讀取 Issue 留言，但不提供直接啟動 workflow_dispatch 的功能。
所以用 owner-only Issue 啟動同一條 Actions 工作流程：

1. GPT 使用 GitHub 連接器建立一筆新 Issue，標題以 [E4B SCENE] 開頭。
2. Issue 內文直接是有效 JSON：根物件具有 scene 及可選的 max_tokens。
3. Runner 從 GITHUB_EVENT_PATH 安全讀取事件 payload，驗證建立者是 repository owner。
4. 檢查場景大小、簡單的憑證特徵、角色陣列、max_tokens 數值。
5. 使用既有模型快取與 llama.cpp 產生台詞、動作、旁白。
6. E4B 成功後將成稿與量測資料留言到同一 Issue；GPT 透過 GitHub 連接器讀回。
7. GPT 核對 Google Drive 已定稿正文、正式世界線、人物動態記憶及原作角色能力，再決定是否寫入正式小說與記憶。

Issue 標題範例：[E4B SCENE] 《原創作品》場景 1
Issue 內文範例（必須是純 JSON，無 Markdown 程式碼框）：

~~~json
{
  "max_tokens": 720,
  "scene": {
    "title": "放學後的車站",
    "setting": "傍晚的車站月台。",
    "characters": [
      {"name": "小葵", "personality": "說話直接", "known": "知道末班車即將到站"},
      {"name": "阿澈", "personality": "愛開玩笑", "known": "不知道末班車時間"}
    ],
    "plot_beats": [
      "小葵提醒末班車時間",
      "兩人聊今天發生的事",
      "到站後一起上車"
    ],
    "constraints": "繁體中文，自然口語，不得新增陰謀或新角色。"
  }
}
~~~

- [E4B DEMO] 開頭的 Issue 仍會固定跑 samples/test-scene.json，不使用 Issue 內文。
- Issue 只在首次建立時觸發，不會因編輯舊 Issue 自動重新推論。
- max_tokens 限 64–1000（預設 720），每個 scene JSON 小於 12 KiB。
- llama.cpp context size 已設定 4096；長小說請拆成連續場景，僅傳輸本場涉及的必要記憶。
- GitHub Actions 模型快取沿用之前已成功的快取鍵與 SHA-256 驗證。
- 成果除了 Issue 留言，還會以 artifact 保留七天。GitHub Actions 仍可使用 workflow_dispatch 手動跑公開場景。
- 外部 CLI scripts/github_bridge.py 使用 GH_TOKEN 或 GITHUB_TOKEN 呼叫 workflow_dispatch；不需要這個 CLI 也能在 ChatGPT 內完成 Issue 模式。

## 重要安全界線

此儲存庫是 PUBLIC；按照使用者已確認的選擇，小說內容可在公開 Issue 以及公開結果留言中傳送，無須額外加密。
這不代表資料私密。GitHub Issue、Actions 日誌與 artifact 不是機密資料保存區。
不要送出密碼、API Token、私鑰、財務或身分證明等資料。程式只會攔截部分明顯憑證格式，不能保證偵測所有機密。

GitHub Actions 留言使用短效 GITHUB_TOKEN，工作流程權限僅 contents: read 與 issues: write。
不把 Issue body 注入 shell 命令，而是由 Python 直接解析 GitHub event JSON。

## 創作分工與正式定稿

GPT 必須先閱讀既有 Google Drive 正式正文、世界線、角色卡與個別動態記憶，整理場景交接包。
E4B 只負責實際演出，不得自己決定世界線、主角重要行動或將新事件當已發生事實。
GPT 取得 E4B 輸出後進行劇情、連續性、角色原作智力與能力的最終審核。
只有通過後才可依每部作品既有規則，將正文寫入 Google Drive；人物動態記憶和正式世界線也須以已採納事實為準。

## 專案測試

~~~bash
python3 -m unittest discover -s tests -v
~~~

既有成功紀錄：
- workflow_dispatch CPU 推論 run 40190247479（快取命中、繁體中文生成）。
- Issue 公開示範 round-trip run 40191465796（16 項測試、快取命中、Issue 自動回傳）。
- ✅ 自訂場景 Issue #3 / run 40192897622 已成功：19 項 Python 測試、Cache hit、SHA-256 校驗、E4B 撰寫 279 字元並自動回傳 GPT。

## 核心檔案

- .github/workflows/e4b-cpu-test.yml：Actions CPU 啟動、快取、E4B 推論與 Issue 自動留言。
- scripts/prepare_scene.py：Issue/Dispatch JSON 解析、請求驗證與 scene.json 產生。
- scripts/run_scene.py：llama.cpp / Ollama 生成與效能統計。
- scripts/comment_demo.py：將場景成稿與執行連結回覆至 Issue。
- scripts/github_bridge.py：授權環境可用的 REST API 觸發與 artifact 下載工具。
