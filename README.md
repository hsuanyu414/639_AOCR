# 639_AOCR

## 環境設置

```
git clone https://github.com/hsuanyu414/639_AOCR.git
cd 639_AOCR
```
- python 請使用 3.12.0
- 安裝相關套件
```
pip install -r requirements.txt
```

# 標記工具

## Usage

- 執行 main.py
```
python ./main.py
```

## 介面&操作說明

- 關於標記csv檔
  - **所有標記皆須透過 `Save to CSV` 按鈕進行存檔**
  - 程式預設的標記csv檔案存放路徑為`./mask_csv`資料夾
  - 若程式執行時同路徑下未有此資料夾，會自動創建
  - 標記csv檔案皆會儲存在`./mask_csv`，**若程式所在路徑有變動，儲存位置也會隨之改變，請特別留意**
- `Select Folder`: 選擇CT圖所在資料夾，檔案會顯示在右側 box 中
  - 點擊 box 中檔案，CT圖即會顯示在左側 view 中，若`./mask_csv`中有該圖相對應的標記檔案，程式將會自動載入，方便查看先前的標記結果

### Main View: 顯示CT圖三個視角

<img src="https://github.com/hsuanyu414/639_AOCR/blob/main/img/main_view.png" width="700" />

- **按住滑鼠左鍵並拖曳**黃色小視窗，視窗內放大圖會同步顯示於右側Focus View
- 利用**滑鼠滾輪**可以檢視同一視角下不同slice的狀態
- Focus View 下的 slider 可以分別對x, y, z方向調整顯示的slice

### Focus View: 顯示黃色視窗中的放大圖

<img src="https://github.com/hsuanyu414/639_AOCR/blob/main/img/focus_view_other.png" width="500" />

<img src="https://github.com/hsuanyu414/639_AOCR/blob/main/img/focus_view_mark.png" width="700" />

- **按住滑鼠左鍵並拖曳**可以在放大圖內進行標記，標記位置會呈現綠色，所標記的位置會記錄在右下方 `Coord List` box 中
- **按住滑鼠右鍵並拖曳**可以在放大圖內消除標記，右下 box 中的紀錄會同時變動
- **滑鼠滾輪**可以放大 / 縮小黃色小視窗，方便調整 Focus View 可見範圍
- `Window Size` slider 同樣可以調整黃色小視窗大小
- `Green Mask Alph` slider 可以調整綠色標記的透明度
- `Red Line Alph` slider 可以調整紅色十字線的透明度
- `Record Coord` 按鈕可以對目前紅十字線所在位置進行標記
- `Delete Coord` 按鈕可以刪除在`Coord List` box 內所選取的標記資料

### `Coord List` box: 顯示標記位置

<img src="https://github.com/hsuanyu414/639_AOCR/blob/main/img/coord_list.png" width="700" />

- **滑鼠點擊兩下** box 內座標可以在 Main/Focus View查看該座標位置圖像
- `Sort by ...` 按鈕可以選擇如何對 `Coord List` box 內座標進行排序
  - `sort by value`: 根據 (x, y, z) 值排序
  - `sort by add time`: 根據標記時間排序
- `Restore CSV` 按鈕會重新讀取該圖像的.csv 標記檔案，**須注意會清除所有為儲存的標記資料**
- `Save to CSV` 按鈕會將 box 內資料彙整為 csv 檔儲存至 `./mask_csv`，儲存成功會跳出視窗
- `Clear All` 按鈕會**清除目前 box 內所有資料**，並不會影響csv檔案

## 範例影片

[Youtube Link](https://www.youtube.com/watch?v=5Phf1KO9lXQ)

## 顯示參數

- window width: 400
- window level: 40

# 轉換工具
usage:
- 將資料放入 `./Data/` 資料夾中
- 執行 id2serial.py [--action ACTION] 
  - ACTION
    - to_serial: 將資料夾中的資料轉換成 serial number 編號
    - to_id: 將資料夾中的資料轉換成 id 編號
