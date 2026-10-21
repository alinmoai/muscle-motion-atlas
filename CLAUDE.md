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
- Artifact 連結：https://claude.ai/artifact/2tsDDLskCDpZzZhZkuGmQE
- 發布 `build/artifact/index.html`，附檔 `model.json`、`overview.b64.txt`、`region_arm.b64.txt`、`region_leg.b64.txt` 和三個 `*.plain.b64.txt`（Artifact 不收 `.glb`）。
- 從新的對話更新時，先 read 這個連結，再帶 `url` 發布。
