# 📤 GitHub 上傳快速指南

## 🎯 已為您準備的文件

✅ **README.md** - 完整的專案說明文件  
✅ **requirements.txt** - Python 依賴列表  
✅ **.gitignore** - Git 忽略文件  
✅ **LICENSE** - MIT 開源許可證  
✅ **install_dependencies.py** - 依賴安裝腳本  
✅ **upload_to_github.sh** - 自動上傳腳本  

## 🚀 三種上傳方式

### 方式一：自動化腳本（推薦）

```bash
# 執行自動上傳腳本
./upload_to_github.sh
```

腳本會自動：
- 檢查 Git 安裝
- 初始化 Git 倉庫  
- 檢查必要文件
- 詢問倉庫名稱和用戶名
- 提交所有文件
- 推送到 GitHub

### 方式二：手動 Git 操作

```bash
# 1. 初始化 Git 倉庫
git init

# 2. 添加所有文件
git add .

# 3. 提交變更
git commit -m "Initial commit: 添加 LD2412 深色GUI工具"

# 4. 添加遠端倉庫 (替換為您的用戶名和倉庫名)
git remote add origin https://github.com/您的用戶名/LD2412-Tools.git

# 5. 推送到 GitHub
git branch -M main
git push -u origin main
```

### 方式三：GitHub Desktop

1. 打開 GitHub Desktop
2. File → Add Local Repository
3. 選擇此專案資料夾
4. 輸入 Commit 信息
5. 點擊 "Commit to main"
6. 點擊 "Publish repository"

## 📋 上傳前準備清單

### 1. 在 GitHub 創建倉庫
- 登入 GitHub
- 點擊 "New repository"
- 倉庫名稱建議：`LD2412-Tools`
- 設為 Public（公開）
- ⚠️ **不要**勾選 "Add a README file"

### 2. 確認必要文件
```bash
# 檢查文件是否齊全
ls -la
```

應該看到：
- `README.md`
- `ld2412_dark_gui.py`
- `LD2412串口通信協議說明.md`
- `requirements.txt`
- `LICENSE`
- `.gitignore`
- `install_dependencies.py`
- `upload_to_github.sh`

### 3. 測試程式功能（可選）
```bash
# 安裝依賴
python install_dependencies.py

# 測試主程式
python ld2412_dark_gui.py
```

## 🔧 常見問題解決

### Q: 上傳失敗 "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/您的用戶名/LD2412-Tools.git
git push -u origin main
```

### Q: 需要認證
GitHub 現在需要使用 Personal Access Token：
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. 勾選 "repo" 權限
4. 使用 token 作為密碼

### Q: 推送被拒絕
```bash
# 強制推送（小心使用）
git push -f origin main
```

### Q: 文件太大
檢查 `.gitignore` 是否正確排除了大文件：
```bash
git status
```

## 📱 上傳後建議

### 1. 完善倉庫信息
- **描述**: "LD2412 24GHz毫米波雷達傳感器深色主題GUI工具"
- **Website**: 可以留空或填入相關連結
- **Topics**: `ld2412`, `radar`, `gui`, `python`, `matplotlib`, `tkinter`

### 2. 創建 Release
- 點擊 "Releases" → "Create a new release"
- Tag: `v2.6`
- Title: `LD2412 深色GUI工具 v2.6`
- 描述: 從 README 複製功能特色

### 3. 啟用 Issues 和 Discussions
在 Settings → Features 中啟用：
- ✅ Issues
- ✅ Discussions

### 4. 添加 GitHub Actions（進階）
可以添加自動化工作流程：
- 代碼檢查
- 自動測試
- 自動發布

## 🎉 完成！

上傳成功後，您的倉庫地址將是：
```
https://github.com/您的用戶名/LD2412-Tools
```

其他人可以這樣使用：
```bash
# 下載專案
git clone https://github.com/您的用戶名/LD2412-Tools.git
cd LD2412-Tools

# 安裝依賴
python install_dependencies.py

# 運行程式
python ld2412_dark_gui.py
```

## 📞 需要幫助？

如果遇到問題：
1. 檢查 Git 是否正確安裝
2. 確認網路連接
3. 驗證 GitHub 認證設定
4. 參考 Git 官方文檔

---

🌟 **祝您使用愉快！記得在 GitHub 給專案加個 Star ⭐** 