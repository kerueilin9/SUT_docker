# JaCoCo Coverage API 使用說明文件

## 📋 目錄
- [服務概述](#服務概述)
- [環境要求](#環境要求)
- [快速開始](#快速開始)
- [API 端點說明](#api-端點說明)
- [使用流程](#使用流程)
- [常見問題](#常見問題)

---

## 服務概述

本服務提供基於 Flask 的 JaCoCo 代碼覆蓋率分析 API，用於監控 Spring PetClinic 應用程式的測試覆蓋率。

### 主要功能
- ✅ 通過 TCP 導出覆蓋率數據
- ✅ 生成 HTML 覆蓋率報告
- ✅ 支援累積模式（歷史數據合併）
- ✅ 覆蓋率數據備份與還原
- ✅ 自動檢測類文件路徑

### 服務端口
- **Flask API**: `http://localhost:5000`

---

## 環境要求

### 必要組件
- Docker & Docker Compose
- Java Runtime Environment (JRE)
- JaCoCo CLI (`jacococli.jar`)

### 目錄結構
```
/jacoco/
├── jacoco-current.exec    # 當前會話覆蓋率數據
├── jacoco-tcp.exec        # TCP 導出的覆蓋率數據
├── jacoco-history.exec    # 歷史累積數據
├── backups/               # 自動備份目錄
└── report/                # HTML 報告輸出目錄
    └── index.html         # 覆蓋率報告首頁
```

---

## 快速開始

### 1. 啟動服務
```bash
docker-compose up -d
```

### 2. 檢查服務狀態
```bash
curl http://localhost:5000/health
```

### 3. 生成第一份覆蓋率報告
```bash
curl http://localhost:5000/coverage/report-tcp-cumulative
```

### 4. 查看報告
在瀏覽器中訪問：
```
http://localhost:5000/coverage/report-html/index.html
```

---

## API 端點說明

### 🏠 基礎端點

#### `GET /`
**功能**: API 服務首頁，列出所有可用端點

**回應範例**:
```json
{
  "service": "JaCoCo Coverage API",
  "endpoints": {
    "/coverage/dump": "Check coverage file status",
    "/coverage/report": "Generate coverage report",
    ...
  }
}
```

---

#### `GET /health`
**功能**: 健康檢查端點

**回應範例**:
```json
{
  "status": "healthy",
  "java_available": true,
  "jacoco_cli_available": true,
  "jacoco_dir_writable": true,
  "java_version": "openjdk version \"11.0.x\""
}
```

**用途**:
- 監控服務運行狀態
- 檢查 Java 環境
- 驗證 JaCoCo CLI 可用性
- 確認目錄寫入權限

---

### 📊 覆蓋率數據操作

#### `GET /coverage/dump`
**功能**: 檢查覆蓋率文件狀態

**回應範例**:
```json
{
  "status": "success",
  "files": {
    "jacoco.exec": {
      "exists": true,
      "size": 12345
    },
    "jacoco-tcp.exec": {
      "exists": true,
      "size": 23456
    }
  }
}
```

**用途**:
- 確認覆蓋率數據文件是否存在
- 檢查文件大小
- 診斷數據收集問題

---

#### `GET /coverage/dump-tcp`
**功能**: 通過 TCP 連接導出覆蓋率數據

**技術細節**:
- 連接目標: `spring-petclinic_1:6300`
- 輸出文件: `/jacoco/jacoco-tcp.exec`

**回應範例**:
```json
{
  "status": "success",
  "file": "jacoco-tcp.exec",
  "size": 34567
}
```

**使用場景**:
- 從運行中的應用程式導出實時覆蓋率
- 手動觸發數據收集
- 調試 TCP 連接問題

**錯誤處理**:
```json
{
  "status": "error",
  "error": "TCP dump failed: Connection refused"
}
```

---

### 📈 報告生成

#### `GET /coverage/report`
**功能**: 從現有的 exec 文件生成覆蓋率報告

**優先級**:
1. 優先使用 `jacoco-tcp.exec`（TCP 模式）
2. 其次使用 `jacoco.exec`（文件模式）

**回應範例**:
```json
{
  "status": "success",
  "url": "/coverage/report-html/index.html",
  "exec_file": "jacoco-tcp.exec",
  "file_type": "TCP"
}
```

**用途**:
- 快速生成報告
- 使用最新的覆蓋率數據
- 不進行數據合併

---

#### `GET /coverage/report-tcp`
**功能**: 導出 TCP 數據後生成報告（覆蓋模式）

**執行步驟**:
1. 通過 TCP 導出最新數據
2. 覆蓋現有的 `jacoco-tcp.exec`
3. 生成新報告

**特點**:
- ⚠️ **會覆蓋**之前的數據
- 適合單次測試場景
- 不保留歷史記錄

**回應範例**:
```json
{
  "status": "success",
  "url": "/coverage/report-html/index.html",
  "exec_file": "jacoco-tcp.exec",
  "file_type": "TCP"
}
```

---

#### `GET /coverage/report-tcp-cumulative` ⭐ **推薦使用**
**功能**: 導出 TCP 數據並累積合併歷史覆蓋率

**執行流程**:
```
┌─────────────────────────┐
│ 1. 備份現有歷史數據      │
│    jacoco-tcp.exec      │
│    → backups/           │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ 2. 導出當前會話數據      │
│    TCP → current.exec   │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ 3. 合併數據              │
│    history + current    │
│    → jacoco-tcp.exec    │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ 4. 生成累積報告          │
└─────────────────────────┘
```

**回應範例**:
```json
{
  "status": "success",
  "url": "/coverage/report-html/index.html",
  "exec_file": "jacoco-tcp.exec",
  "file_type": "Cumulative",
  "merge_info": {
    "history_size": 45678,
    "current_size": 12345,
    "merged_size": 56789,
    "is_cumulative": true
  }
}
```

**首次運行回應**:
```json
{
  "status": "success",
  "merge_info": {
    "current_size": 12345,
    "merged_size": 12345,
    "is_cumulative": false,
    "note": "首次運行，建立基準數據"
  }
}
```

**優勢**:
- ✅ 保留所有測試歷史
- ✅ 自動備份數據
- ✅ 適合持續集成
- ✅ 追蹤覆蓋率趨勢

**備份機制**:
- 自動生成時間戳備份: `jacoco-backup-20250117_143022.exec`
- 保存在 `/jacoco/backups/` 目錄

---

### 🔧 配置與工具

#### `GET /coverage/check-classes`
**功能**: 檢查類文件（.class）的可用路徑

**回應範例**:
```json
{
  "status": "success",
  "class_paths": [
    {
      "path": "/spring-petclinic-classes/java/main",
      "exists": true,
      "is_directory": true,
      "class_files": 45
    },
    {
      "path": "/spring-petclinic/build/classes/java/main",
      "exists": false
    }
  ],
  "current_config": "/spring-petclinic-classes/java/main"
}
```

**用途**:
- 診斷報告生成失敗問題
- 驗證 Docker 卷掛載
- 確認類文件數量

---

#### `GET /coverage/auto-setup`
**功能**: 自動檢測並設置類文件路徑

**執行邏輯**:
1. 檢查預定義路徑列表
2. 遞迴搜尋 `.class` 文件
3. 自動更新配置

**回應範例**:
```json
{
  "status": "success",
  "message": "Class files path updated to: /spring-petclinic-classes/java/main",
  "path": "/spring-petclinic-classes/java/main"
}
```

**失敗回應**:
```json
{
  "status": "error",
  "message": "No valid class files path found",
  "checked_paths": [...]
}
```

---

#### `GET /coverage/reset`
**功能**: 清除所有覆蓋率數據和歷史記錄

**刪除內容**:
- ✅ 所有 `.exec` 文件
- ✅ 歷史備份目錄
- ✅ HTML 報告目錄

**回應範例**:
```json
{
  "status": "success",
  "message": "所有覆蓋率數據已清除",
  "removed_files": [
    "/jacoco/jacoco-tcp.exec",
    "/jacoco/jacoco-current.exec",
    "/jacoco/jacoco-history.exec"
  ],
  "removed_dirs": [
    "/jacoco/report",
    "/jacoco/backups"
  ]
}
```

**⚠️ 警告**: 
- 此操作**不可逆**
- 會刪除所有歷史數據
- 建議在使用前先備份重要數據

---

### 🌐 報告查看

#### `GET /coverage/report-html/index.html`
**功能**: 查看生成的 HTML 覆蓋率報告

**訪問方式**:
```
http://localhost:5000/coverage/report-html/index.html
```

**報告內容**:
- 整體覆蓋率統計
- 各包（Package）的覆蓋率
- 類級別的詳細覆蓋率
- 行覆蓋率、分支覆蓋率等指標

**報告導航**:
```
index.html (總覽)
├── org.springframework.samples.petclinic/
│   ├── PetClinicApplication.html
│   └── ...
├── org.springframework.samples.petclinic.owner/
│   ├── Owner.html
│   ├── OwnerController.html
│   └── ...
└── ...
```

---

## 使用流程

### 場景一: 單次測試覆蓋率分析

```bash
# 1. 運行測試（在應用程式中）
# ... 執行測試 ...

# 2. 生成報告
curl http://localhost:5000/coverage/report-tcp

# 3. 查看報告
# 在瀏覽器訪問: http://localhost:5000/coverage/report-html/index.html
```

---

### 場景二: 持續追蹤覆蓋率（推薦）

```bash
# 第一次測試
curl http://localhost:5000/coverage/report-tcp-cumulative

# 第二次測試（數據會累積）
curl http://localhost:5000/coverage/report-tcp-cumulative

# 第三次測試（繼續累積）
curl http://localhost:5000/coverage/report-tcp-cumulative

# 查看完整的累積報告
# 瀏覽器訪問: http://localhost:5000/coverage/report-html/index.html
```

---

### 場景三: 清除數據重新開始

```bash
# 1. 清除所有歷史數據
curl http://localhost:5000/coverage/reset

# 2. 重新開始收集
curl http://localhost:5000/coverage/report-tcp-cumulative
```

---

### 場景四: 診斷問題

```bash
# 1. 檢查服務健康狀態
curl http://localhost:5000/health

# 2. 檢查覆蓋率文件
curl http://localhost:5000/coverage/dump

# 3. 檢查類文件配置
curl http://localhost:5000/coverage/check-classes

# 4. 自動修復類文件路徑
curl http://localhost:5000/coverage/auto-setup
```

---

## 常見問題

### Q1: 報告生成失敗，顯示 "No jacoco.exec file found"
**原因**: 沒有可用的覆蓋率數據文件

**解決方案**:
```bash
# 先導出數據
curl http://localhost:5000/coverage/dump-tcp

# 再生成報告
curl http://localhost:5000/coverage/report
```

---

### Q2: TCP 導出失敗，顯示 "Connection refused"
**原因**: 
- Spring PetClinic 應用程式未啟動
- JaCoCo agent 未正確配置
- 端口 6300 未開放

**檢查步驟**:
1. 確認應用程式容器運行中: `docker ps`
2. 檢查容器名稱是否為 `spring-petclinic_1`
3. 驗證 JaCoCo agent 參數: `-javaagent:jacoco.jar=output=tcpserver,port=6300`

---

### Q3: 報告顯示 0% 覆蓋率
**原因**: 類文件路徑配置錯誤

**解決方案**:
```bash
# 檢查類文件路徑
curl http://localhost:5000/coverage/check-classes

# 自動設置正確路徑
curl http://localhost:5000/coverage/auto-setup

# 重新生成報告
curl http://localhost:5000/coverage/report
```

---

### Q4: 如何恢復備份的覆蓋率數據？
**步驟**:
```bash
# 1. 進入容器
docker exec -it flask-server bash

# 2. 查看備份文件
ls -lh /jacoco/backups/

# 3. 複製備份文件
cp /jacoco/backups/jacoco-backup-20250117_143022.exec /jacoco/jacoco-tcp.exec

# 4. 生成報告
curl http://localhost:5000/coverage/report
```

---

### Q5: 累積模式和覆蓋模式有什麼區別？

| 特性 | 累積模式 (`/report-tcp-cumulative`) | 覆蓋模式 (`/report-tcp`) |
|------|-------------------------------------|-------------------------|
| 數據保留 | ✅ 保留所有歷史數據 | ❌ 覆蓋之前的數據 |
| 自動備份 | ✅ 是 | ❌ 否 |
| 使用場景 | 持續測試、CI/CD | 單次測試 |
| 推薦度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 進階使用

### 使用 PowerShell 腳本自動化

```powershell
# 定義 API 基礎 URL
$baseUrl = "http://localhost:5000"

# 函數: 健康檢查
function Test-ServiceHealth {
    $response = Invoke-RestMethod -Uri "$baseUrl/health"
    Write-Host "服務狀態: $($response.status)" -ForegroundColor Green
}

# 函數: 生成累積報告
function New-CumulativeReport {
    Write-Host "正在生成累積報告..." -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "$baseUrl/coverage/report-tcp-cumulative"
    
    if ($response.status -eq "success") {
        Write-Host "✅ 報告生成成功!" -ForegroundColor Green
        Write-Host "報告 URL: $baseUrl$($response.url)"
        Write-Host "合併信息:" -ForegroundColor Cyan
        $response.merge_info | ConvertTo-Json
    }
}

# 函數: 清除數據
function Clear-CoverageData {
    $confirm = Read-Host "確定要清除所有覆蓋率數據嗎? (Y/N)"
    if ($confirm -eq "Y") {
        $response = Invoke-RestMethod -Uri "$baseUrl/coverage/reset"
        Write-Host "✅ 數據已清除" -ForegroundColor Green
    }
}

# 執行
Test-ServiceHealth
New-CumulativeReport
```

---

### 定期備份腳本

```powershell
# 備份腳本
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = ".\coverage-backups\$timestamp"

# 創建備份目錄
New-Item -ItemType Directory -Path $backupDir -Force

# 複製報告
docker cp flask-server:/jacoco/report "$backupDir\report"
docker cp flask-server:/jacoco/jacoco-tcp.exec "$backupDir\jacoco-tcp.exec"

Write-Host "✅ 備份完成: $backupDir" -ForegroundColor Green
```

---

## 技術支援

### 日誌查看
```bash
# 查看 Flask 服務日誌
docker logs flask-server

# 實時監控日誌
docker logs -f flask-server
```

### 容器內調試
```bash
# 進入容器
docker exec -it flask-server bash

# 檢查文件
ls -lh /jacoco/

# 測試 JaCoCo CLI
java -jar /app/jacococli.jar --help
```

---

## 更新日誌

### Version 1.0
- ✅ 基礎覆蓋率報告生成
- ✅ TCP 數據導出
- ✅ 累積模式支持
- ✅ 自動備份功能
- ✅ 健康檢查端點
- ✅ 自動路徑檢測

---

## 授權與版權

本專案使用 JaCoCo (Eclipse Public License)

---

**文件版本**: 1.0  
**最後更新**: 2025-11-17  
**作者**: System Administrator
