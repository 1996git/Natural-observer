#!/bin/bash
# AWS Elastic Beanstalk へのデプロイスクリプト

set -e

# 環境変数の確認
: "${EB_APP_NAME:?EB_APP_NAME を設定してください}"
: "${EB_ENV_NAME:?EB_ENV_NAME を設定してください}"

echo "🚀 Natural Observer Backend を Elastic Beanstalk にデプロイ"
echo "アプリケーション: ${EB_APP_NAME}"
echo "環境: ${EB_ENV_NAME}"

# EB CLI がインストールされているか確認
if ! command -v eb &> /dev/null; then
    echo "❌ EB CLI がインストールされていません"
    echo "pip install awsebcli でインストールしてください"
    exit 1
fi

# zip パッケージを作成（.ebignore を使用）
echo "📦 デプロイパッケージを作成中..."
zip -r deploy.zip . -x "*.git*" "*.pyc" "__pycache__/*" "*.db" "venv/*" "*.log"

# Elastic Beanstalk にデプロイ
echo "📤 Elastic Beanstalk にデプロイ中..."
eb deploy ${EB_ENV_NAME}

echo "✅ デプロイ完了！"
echo "環境の状態を確認:"
echo "eb status ${EB_ENV_NAME}"
