#!/usr/bin/env python3
"""
Istanbul Code Coverage Parser
解析並顯示 Istanbul coverage 資料的統計資訊
"""

import json
import requests
from typing import Dict, List

def fetch_coverage_data(url: str = "http://localhost:3100/coverage/object") -> Dict:
    """從 API 獲取 coverage 資料"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"無法獲取資料: {e}")
        return {}

def parse_coverage_data(coverage_data: Dict) -> Dict:
    """解析 coverage 資料並計算統計"""
    stats = {
        'files': [],
        'total': {
            'statements': {'covered': 0, 'total': 0},
            'branches': {'covered': 0, 'total': 0},
            'functions': {'covered': 0, 'total': 0},
            'lines': {'covered': 0, 'total': 0}
        }
    }
    
    for file_path, file_data in coverage_data.items():
        file_stats = {
            'path': file_path,
            'statements': calculate_coverage(file_data.get('s', {})),
            'branches': calculate_branch_coverage(file_data.get('b', {})),
            'functions': calculate_coverage(file_data.get('f', {})),
            'lines': calculate_coverage(file_data.get('l', {}))
        }
        
        stats['files'].append(file_stats)
        
        # 累加總計
        for metric in ['statements', 'branches', 'functions', 'lines']:
            stats['total'][metric]['covered'] += file_stats[metric]['covered']
            stats['total'][metric]['total'] += file_stats[metric]['total']
    
    return stats

def calculate_coverage(data: Dict) -> Dict:
    """計算一般覆蓋率 (statements, functions, lines)"""
    total = len(data)
    covered = sum(1 for count in data.values() if count > 0)
    percentage = (covered / total * 100) if total > 0 else 0
    return {
        'covered': covered,
        'total': total,
        'percentage': round(percentage, 2)
    }

def calculate_branch_coverage(data: Dict) -> Dict:
    """計算分支覆蓋率"""
    total_branches = sum(len(branches) for branches in data.values())
    covered_branches = sum(
        sum(1 for count in branches if count > 0)
        for branches in data.values()
    )
    percentage = (covered_branches / total_branches * 100) if total_branches > 0 else 0
    return {
        'covered': covered_branches,
        'total': total_branches,
        'percentage': round(percentage, 2)
    }

def print_coverage_report(stats: Dict):
    """列印覆蓋率報告"""
    print("\n" + "="*80)
    print("Istanbul Code Coverage Report")
    print("="*80 + "\n")
    
    # 總體統計
    print("📊 總體覆蓋率:")
    print("-" * 80)
    for metric_name, metric_data in stats['total'].items():
        covered = metric_data['covered']
        total = metric_data['total']
        percentage = (covered / total * 100) if total > 0 else 0
        bar = create_progress_bar(percentage)
        
        print(f"{metric_name.capitalize():12} : {bar} {covered}/{total} ({percentage:.2f}%)")
    
    print("\n" + "="*80)
    print(f"📁 檔案覆蓋率詳情 (共 {len(stats['files'])} 個檔案):")
    print("="*80 + "\n")
    
    # 個別檔案統計
    for file_stat in stats['files']:
        print(f"\n📄 {file_stat['path']}")
        print("-" * 80)
        
        for metric in ['statements', 'branches', 'functions', 'lines']:
            data = file_stat[metric]
            bar = create_progress_bar(data['percentage'])
            print(f"  {metric.capitalize():12} : {bar} {data['covered']}/{data['total']} ({data['percentage']:.2f}%)")

def create_progress_bar(percentage: float, width: int = 30) -> str:
    """創建進度條"""
    filled = int(width * percentage / 100)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}]"

def get_coverage_vector(coverage_data: Dict, metric: str) -> List[int]:
    """
    提取覆蓋率向量（類似 Java 代碼的做法）
    metric: 's' (statements) 或 'b' (branches)
    """
    vector = []
    
    for file_path, file_data in coverage_data.items():
        if metric == 's':
            # Statement vector
            s_data = file_data.get('s', {})
            vector.extend(s_data.values())
        elif metric == 'b':
            # Branch vector
            b_data = file_data.get('b', {})
            for branches in b_data.values():
                vector.extend(branches)
    
    return vector

def main():
    print("正在從 http://localhost:3000/coverage/object 獲取資料...")
    
    coverage_data = fetch_coverage_data()
    
    if not coverage_data:
        print("無法獲取 coverage 資料，請確認服務是否正在運行")
        return
    
    stats = parse_coverage_data(coverage_data)
    print_coverage_report(stats)
    
    # 顯示向量資訊（類似 Java 代碼）
    print("\n" + "="*80)
    print("📈 Coverage Vectors (類似 Java 代碼的輸出):")
    print("="*80)
    
    statement_vector = get_coverage_vector(coverage_data, 's')
    branch_vector = get_coverage_vector(coverage_data, 'b')
    
    print(f"\nStatement Vector 長度: {len(statement_vector)}")
    print(f"  覆蓋的語句數: {sum(1 for x in statement_vector if x > 0)}")
    print(f"  未覆蓋的語句數: {sum(1 for x in statement_vector if x == 0)}")
    
    print(f"\nBranch Vector 長度: {len(branch_vector)}")
    print(f"  覆蓋的分支數: {sum(1 for x in branch_vector if x > 0)}")
    print(f"  未覆蓋的分支數: {sum(1 for x in branch_vector if x == 0)}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

