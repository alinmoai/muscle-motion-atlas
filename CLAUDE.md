# 給 Claude 的工作規則

這個專案的錯誤通常「看起來是對的」，所以規則都在避免靠目測判斷。

## 座標
- 公尺；+Z 往上，−Y 往前（anterior），−X 是受試者的右側。右側肢體在 x < 0，+X 是內側（medial）。
- 只有右側（名稱結尾 `.r`）能動；`trunk` 是固定不動的其餘骨頭。

## 不要相信模型的名稱
- Z-Anatomy 的名稱和附著區（`.o*` / `.e*`）有錯。用到一條肌肉前，先用位置確認（例如外側頭的 x 要比內側頭小）。
- 名稱錯誤記在 `pipeline/names.py` 的 `NAME_FIX`；附著點錯誤記在 `pipeline/bind.py` 的 `OVERRIDES`，每筆都要寫 `why`。

## 方向和長度用量的
- 每個角度的正負號由 `verify_kinematics.py` 量地標位移決定，不要手動改 `signs`，也不要用截圖判斷方向。
- 改了關節或綁定，跑完要確認 `reports/muscles.txt` 是 N/N，`node site/src/test_kin.mjs` 差值為 0。
- 新增動作或部位時，先在 `verify_muscles.py` 的 `TESTS` 寫下教科書預期，再改程式。

## 所有修正都要寫進程式
- 不要直接改 `build/` 裡的中間檔。之前有兩個修正是直接改中間 JSON，結果從頭重跑就壞了。
- `./run_all.sh` 必須能從原始 FBX 一路重建到網頁。

## 兩份一樣的算法
- `pipeline/kin.py`（Python，驗證用）和 `site/src/kin.js`（網頁用）是同一套正向運動學和肌肉長度計算，要一起改。

## 發布
- 網頁在 GitHub Pages：https://alinmoai.github.io/muscle-motion-atlas/ 。push 到 `main` 後由 `.github/workflows/pages.yml` 發布 `site/dist/`。
- `site/dist/` 有進 git。改了 `site/src/` 或重跑 pipeline 後，跑 `python3 site/build.py`，把 `site/dist/` 一起 commit。
- `build/artifact/` 是 Claude Artifact 版本（模型轉成 base64，因為 Artifact 不收 `.glb`），只在使用者要求時發布。

## 授權
- 程式碼 MIT；模型和由模型算出的資料（`.glb`、`model.json`）是 Z-Anatomy 的改作，CC BY-SA 4.0。網頁「說明」分頁裡的出處聲明不要拿掉。
