# 肌骨動作圖譜

右側手臂（含肩胛骨）和右腳（到腳掌）的 3D 骨骼肌肉模型。轉動關節時，每條肌肉依長度變化即時上色：紅色是縮短，藍色是被拉長。

網頁：https://alinmoai.github.io/muscle-motion-atlas/

- 首頁是全身骨架（約 1 MB），點手臂或腿才下載那一區的肌肉（約 2.5 MB）
- 手臂 7 個角度、64 條肌肉；腿 7 個角度、58 條肌肉
- 每條肌肉的長度沿「附著點 + 繞過關節的滑車點」量，不是量變形後的網格

## 資料夾

| 路徑 | 內容 | 進 git |
|---|---|---|
| `pipeline/` | 從原始模型算出關節、綁肌肉、驗證、匯出的 Python 程式 | ✓ |
| `site/src/` | 網頁原始碼（`index.html`、`kin.js` 關節與肌肉長度計算） | ✓ |
| `site/dist/` | 建好的網頁和模型，GitHub Pages 發布的就是這個資料夾 | ✓ |
| `site/test/` | 無頭瀏覽器測試與截圖 | ✓ |
| `reports/` | 每次重建的驗證結果 | ✓ |
| `build/` | 下載的原始模型、中間資料、Claude Artifact 版本 | ✗（可重建） |

## 從頭重建

需要 Python 3.13（`bpy` 5.2 只有 3.13 的版本）和 Node.js。

```bash
pip install -r requirements.txt
npm install
./run_all.sh        # 約 20 分鐘
```

`run_all.sh` 會依序：

1. 下載 Z-Anatomy 的骨骼和肌肉 FBX（固定在某個 commit，並檢查 sha256）
2. 用 Blender（`bpy`）匯入，存成 numpy 陣列
3. `joints.py`：從骨頭形狀算關節中心和轉軸（球窩關節用球面擬合，鉸鏈關節用上髁或內外踝連線）
4. `rig.py` + `verify_kinematics.py --signs-only`：先決定每個角度正負號代表哪個方向
5. `refine.py`、`knee_track.py`：微調轉軸位置，讓關節面在轉動時保持貼合；膝蓋另外查表做前後滑動
6. `rig.py` + `verify_kinematics.py`：最終的關節定義，以及關節貼合度、骨頭穿透的檢查
7. `bind.py` + `verify_muscles.py`：把肌肉綁到骨頭、決定長度路徑，再對照教科書的主動肌／拮抗肌
8. `export.py`：輸出 glTF 和 `model.json`，用 gltf-transform 壓縮
9. 確認網頁的 JavaScript 和 Python 算出一樣的結果，組出網頁

任何一步驗證失敗，腳本會停下來。

## 驗證

- `reports/kinematics.txt`：每個角度的正負方向是量測地標的位移決定的；關節面間距和穿透點數
- `reports/muscles.txt`：14 個動作、113 項「這條肌肉應該縮短／拉長」的預期
- `reports/binding.txt`：每條肌肉的附著骨頭和長度路徑
- `node site/src/test_kin.mjs`：50 個隨機姿勢下，網頁的計算和 Python 的計算完全一致
- `python3 site/test/check.py`：在手機和桌面尺寸實際操作網頁、截圖（需要 playwright）
- `python3 site/test/playback.py`：來回播放的回歸測試（在動作姿勢上按播放要立刻動；播放中切換動作要繼續播放）

## 常見修改

- **肌肉附著點不對**：在 `pipeline/bind.py` 的 `OVERRIDES` 加一筆，寫清楚 `why`，再從第 7 步重跑
- **模型名稱標錯**：`pipeline/names.py` 的 `NAME_FIX`
- **中文名稱、肌群分類**：`pipeline/names.py`
- **新增教科書檢查**：`pipeline/verify_muscles.py` 的 `TESTS`
- **動作範例、介面**：`site/src/index.html`（`PRESETS`），改完跑 `python3 site/build.py`
- **關節計算**：`pipeline/kin.py` 和 `site/src/kin.js` 是同一套算法，兩邊要一起改，`test_kin.mjs` 會檢查

## 部署

**GitHub Pages。** 每次 push 到 `main`，`.github/workflows/pages.yml` 會把 `site/dist/` 發布到上面的網址。網頁沒有伺服器端，所有計算在瀏覽器裡做，three.js 從 jsDelivr 載入。

改了 `site/src/` 或重跑過 pipeline 之後，跑 `python3 site/build.py` 更新 `site/dist/`，一起 commit 再 push。

**Claude Artifact（可選）。** `build/artifact/` 是同一個網頁的 Artifact 版本：Artifact 不接受 `.glb`，所以模型轉成 base64 文字（`*.b64.txt`），在網頁裡解回來。想在 Claude 裡發布時用這個資料夾。

模型有兩個版本：`*.glb` 用 meshopt 壓縮，需要瀏覽器支援 WebAssembly；`*.plain.glb` 較大，WebAssembly 被擋時自動改用。

## 已知限制

- 只有右側能動
- 肩胛骨照固定比例跟著手臂轉（手臂抬高 3 度，肩胛骨上轉約 1 度），不能單獨控制
- 手指、腳趾內部的關節沒有做（腳趾五根一起動）
- 關節用固定轉軸近似，極端角度時骨頭可能有幾毫米的重疊或間隙；膝蓋屈曲上限 120°
- 手臂舉很高時，胸大肌和闊背肌這類大片肌肉的網格會被拉成帶狀
- 長度變化是幾何上的變化，不代表哪條肌肉在出力

## 原始模型修正紀錄

- 斜方肌上束和下束的名稱在原模型裡是反的，依位置改正（`names.py`）
- 原模型有些附著點標在只是貼著、沒有附著的骨頭上（例如股直肌標到股骨），依解剖學修正（`bind.py` 的 `OVERRIDES`，每筆附原因）

## 來源與授權

- **程式碼**（`pipeline/`、`site/src/`、`site/build.py`、`site/test/`、`run_all.sh`）：[MIT](LICENSE)，可自由使用、修改、商用，保留授權聲明即可。
- **模型與由模型算出的資料**（`site/dist/` 裡的 `.glb` 和 `model.json`，以及 `build/`）：改作自 [Z-Anatomy](https://github.com/LluisV/Z-Anatomy)（衍生自 BodyParts3D），授權 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。再散布時須標示出處，改作也須沿用同一授權。詳見 [LICENSE-models.md](LICENSE-models.md)。
