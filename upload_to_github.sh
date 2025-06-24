#!/bin/bash
# LD2412 工具 GitHub 上傳腳本
# 此腳本會幫助您將專案上傳到 GitHub

echo "🚀 LD2412 工具 GitHub 上傳腳本"
echo "================================"

# 檢查 git 是否安裝
if ! command -v git &> /dev/null; then
    echo "❌ 未找到 git 命令，請先安裝 Git"
    echo "📥 下載地址: https://git-scm.com/downloads"
    exit 1
fi

echo "✅ Git 已安裝"

# 檢查是否已經是 git 倉庫
if [ ! -d ".git" ]; then
    echo "📁 初始化 Git 倉庫..."
    git init
    echo "✅ Git 倉庫初始化完成"
else
    echo "✅ 已存在 Git 倉庫"
fi

# 檢查必要文件
echo "🔍 檢查必要文件..."
required_files=("README.md" "ld2412_dark_gui.py" "LD2412串口通信協議說明.md" "requirements.txt" "LICENSE" ".gitignore")

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ 缺失文件: $file"
        exit 1
    fi
done

# 詢問 GitHub 倉庫名稱
echo ""
read -p "📝 請輸入 GitHub 倉庫名稱 (預設: LD2412-Tools): " repo_name
repo_name=${repo_name:-LD2412-Tools}

# 詢問 GitHub 用戶名
echo ""
read -p "👤 請輸入您的 GitHub 用戶名: " github_username

if [ -z "$github_username" ]; then
    echo "❌ GitHub 用戶名不能為空"
    exit 1
fi

# 添加所有文件
echo ""
echo "📦 添加文件到 Git..."
git add .
echo "✅ 文件添加完成"

# 提交變更
echo ""
echo "💾 提交變更..."
git commit -m "Initial commit: 添加 LD2412 深色GUI工具和通信協議文檔

✨ 功能特色:
- 現代化深色主題界面
- 即時數據監控和圖表顯示  
- 完整的配置管理系統
- 詳細的通信協議文檔

📋 包含文件:
- ld2412_dark_gui.py: 主程序文件
- LD2412串口通信協議說明.md: 協議文檔
- README.md: 專案說明
- requirements.txt: 依賴列表
- install_dependencies.py: 安裝腳本"

echo "✅ 變更提交完成"

# 設置遠端倉庫
echo ""
echo "🔗 設置遠端倉庫..."
remote_url="https://github.com/${github_username}/${repo_name}.git"
git remote add origin "$remote_url" 2>/dev/null || git remote set-url origin "$remote_url"
echo "✅ 遠端倉庫設置完成: $remote_url"

# 推送到 GitHub
echo ""
echo "📤 推送到 GitHub..."
echo "⚠️  請確保您已在 GitHub 上創建了倉庫: $repo_name"
echo ""
read -p "🤔 是否繼續推送？[y/N]: " confirm

if [[ $confirm =~ ^[Yy]$ ]]; then
    git branch -M main
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 上傳成功！"
        echo "🔗 您的倉庫地址: https://github.com/${github_username}/${repo_name}"
        echo "📱 可以分享給其他人使用了！"
        echo ""
        echo "📋 後續建議:"
        echo "  1. 在 GitHub 上完善倉庫描述"
        echo "  2. 添加 Topics 標籤 (如: ld2412, radar, gui, python)"
        echo "  3. 創建 Release 版本"
        echo "  4. 啟用 GitHub Pages (如果需要)"
    else
        echo ""
        echo "❌ 上傳失敗！"
        echo "💡 可能的解決方案:"
        echo "  1. 確保在 GitHub 上已創建倉庫: $repo_name"
        echo "  2. 檢查網路連接"
        echo "  3. 確認 GitHub 認證 (可能需要 Personal Access Token)"
        echo "  4. 手動執行: git push -u origin main"
    fi
else
    echo ""
    echo "⏹️  推送已取消"
    echo "💡 您可以稍後手動推送:"
    echo "   git push -u origin main"
fi

echo ""
echo "📚 更多 Git 命令:"
echo "  git status          # 查看倉庫狀態"
echo "  git log --oneline   # 查看提交歷史"
echo "  git remote -v       # 查看遠端倉庫"
echo ""
echo "🔧 如需修改後重新上傳:"
echo "  git add ."
echo "  git commit -m \"更新說明\""
echo "  git push" 