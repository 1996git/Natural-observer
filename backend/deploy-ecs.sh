#!/bin/bash
# AWS ECS へのデプロイスクリプト

set -e

# 環境変数の確認
: "${AWS_REGION:?AWS_REGION を設定してください}"
: "${ECR_REPOSITORY:?ECR_REPOSITORY を設定してください}"
: "${ECS_CLUSTER:?ECS_CLUSTER を設定してください}"
: "${ECS_SERVICE:?ECS_SERVICE を設定してください}"

# バージョンタグ
VERSION=${1:-latest}
IMAGE_TAG="${ECR_REPOSITORY}:${VERSION}"

echo "🚀 Natural Observer Backend デプロイ開始"
echo "リージョン: ${AWS_REGION}"
echo "イメージ: ${IMAGE_TAG}"

# ECR にログイン
echo "📦 ECR にログイン中..."
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REPOSITORY%/*}

# Docker イメージをビルド
echo "🏗️ Docker イメージをビルド中..."
docker build -t natural-observer-backend .
docker tag natural-observer-backend:latest ${IMAGE_TAG}

# ECR にプッシュ
echo "📤 ECR にプッシュ中..."
docker push ${IMAGE_TAG}

# ECS サービスを更新
echo "🔄 ECS サービスを更新中..."
aws ecs update-service \
  --cluster ${ECS_CLUSTER} \
  --service ${ECS_SERVICE} \
  --force-new-deployment \
  --region ${AWS_REGION}

echo "✅ デプロイ完了！"
echo "サービスの状態を確認してください:"
echo "aws ecs describe-services --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE} --region ${AWS_REGION}"
