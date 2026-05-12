import os
import subprocess
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)

# 配置路径
JACOCO_DIR = "/jacoco"
EXEC_FILE = "/jacoco/jacoco.exec"
TCP_EXEC_FILE = "/jacoco/jacoco-tcp.exec"  # 新增TCP模式的exec文件
REPORT_DIR = "/jacoco/report"
CLASS_FILES = "/spring-petclinic-classes/java/main"  # 通过共享卷访问
JACOCO_CLI_JAR = "/app/jacococli.jar"

# 确保报告目录存在
os.makedirs(REPORT_DIR, exist_ok=True)


@app.route("/coverage/dump")
def dump_coverage():
    """检查覆盖率文件状态"""
    exec_files = [EXEC_FILE, TCP_EXEC_FILE]
    status = {}
    
    for exec_file in exec_files:
        if os.path.exists(exec_file):
            size = os.path.getsize(exec_file)
            status[os.path.basename(exec_file)] = {"exists": True, "size": size}
        else:
            status[os.path.basename(exec_file)] = {"exists": False, "size": 0}
    
    return jsonify({"status": "success", "files": status})


@app.route("/coverage/dump-tcp")
def dump_tcp_coverage():
    """通过TCP连接导出覆盖率数据"""
    try:
        # 使用JaCoCo CLI通过TCP连接导出数据
        subprocess.run([
            "java", "-jar", JACOCO_CLI_JAR, "dump",
            "--address", "spring-petclinic_1",  # 容器名称
            "--port", "6300",
            "--destfile", TCP_EXEC_FILE
        ], check=True)
        
        if os.path.exists(TCP_EXEC_FILE):
            size = os.path.getsize(TCP_EXEC_FILE)
            return jsonify({"status": "success", "file": "jacoco-tcp.exec", "size": size})
        else:
            return jsonify({"status": "error", "error": "Failed to create TCP dump file"}), 500
            
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "error": f"TCP dump failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/coverage/report")
def generate_report():
    """生成覆盖率报告"""
    # 选择可用的exec文件
    exec_file_to_use = None
    if os.path.exists(TCP_EXEC_FILE):
        exec_file_to_use = TCP_EXEC_FILE
        file_type = "TCP"
    elif os.path.exists(EXEC_FILE):
        exec_file_to_use = EXEC_FILE
        file_type = "File"
    else:
        return jsonify({"status": "error", "error": "No jacoco.exec file found"}), 404
    
    try:
        os.makedirs(REPORT_DIR, exist_ok=True)
        
        # 生成覆盖率报告
        subprocess.run([
            "java", "-jar", JACOCO_CLI_JAR, "report", exec_file_to_use,
            "--classfiles", CLASS_FILES,
            "--html", REPORT_DIR,
            "--name", f"Spring PetClinic Coverage Report ({file_type})"
        ], check=True)
        
        # 检查报告是否成功生成
        index_file = os.path.join(REPORT_DIR, "index.html")
        if os.path.exists(index_file):
            return jsonify({
                "status": "success", 
                "url": "/coverage/report-html/index.html",
                "exec_file": os.path.basename(exec_file_to_use),
                "file_type": file_type
            })
        else:
            return jsonify({"status": "error", "error": "Report generation failed - no index.html created"}), 500
            
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "error": f"Report generation failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/coverage/report-tcp")
def generate_tcp_report():
    """先导出TCP数据然后生成报告（覆盖模式）"""
    try:
        # 第一步：通过TCP导出数据
        tcp_result = subprocess.run([
            "java", "-jar", JACOCO_CLI_JAR, "dump",
            "--address", "spring-petclinic_1",  # 容器名称
            "--port", "6300",
            "--destfile", TCP_EXEC_FILE
        ], check=True)
        
        # 第二步：生成报告
        return generate_report()
        
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "error": f"TCP dump failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/coverage/report-tcp-cumulative")
def generate_tcp_cumulative_report():
    """导出TCP数据并累积合并历史覆盖率，然后生成完整报告"""
    try:
        import shutil
        from datetime import datetime
        
        # 文件路径定义
        current_exec = os.path.join(JACOCO_DIR, "jacoco-current.exec")
        history_exec = os.path.join(JACOCO_DIR, "jacoco-history.exec")
        merged_exec = TCP_EXEC_FILE
        backup_dir = os.path.join(JACOCO_DIR, "backups")
        
        # 创建备份目录
        os.makedirs(backup_dir, exist_ok=True)
        
        # 第一步：备份现有的历史数据（如果存在）
        if os.path.exists(merged_exec):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"jacoco-backup-{timestamp}.exec")
            shutil.copy2(merged_exec, backup_file)
            shutil.copy2(merged_exec, history_exec)
            print(f"✅ 备份历史数据: {backup_file}")
        else:
            print("ℹ️  首次运行，无历史数据")
        
        # 第二步：导出当前会话的覆盖率数据
        print("📥 导出当前会话覆盖率数据...")
        subprocess.run([
            "java", "-jar", JACOCO_CLI_JAR, "dump",
            "--address", "spring-petclinic_1",
            "--port", "6300",
            "--destfile", current_exec
        ], check=True)
        print(f"✅ 当前数据已导出: {current_exec}")
        
        # 第三步：合并历史数据和当前数据
        if os.path.exists(history_exec):
            print("🔄 合并历史数据和当前数据...")
            merge_result = subprocess.run([
                "java", "-jar", JACOCO_CLI_JAR, "merge",
                history_exec,
                current_exec,
                "--destfile", merged_exec
            ], check=True, capture_output=True, text=True)
            print(f"✅ 数据已合并: {merged_exec}")
            
            # 获取文件大小信息
            history_size = os.path.getsize(history_exec)
            current_size = os.path.getsize(current_exec)
            merged_size = os.path.getsize(merged_exec)
            
            merge_info = {
                "history_size": history_size,
                "current_size": current_size,
                "merged_size": merged_size,
                "is_cumulative": True
            }
        else:
            # 如果没有历史数据，直接使用当前数据
            print("ℹ️  无历史数据，使用当前数据作为初始数据")
            shutil.copy2(current_exec, merged_exec)
            merge_info = {
                "current_size": os.path.getsize(current_exec),
                "merged_size": os.path.getsize(merged_exec),
                "is_cumulative": False,
                "note": "首次运行，建立基准数据"
            }
        
        # 第四步：生成报告
        print("📊 生成覆盖率报告...")
        
        # 直接生成报告而不是调用generate_report()
        try:
            os.makedirs(REPORT_DIR, exist_ok=True)
            
            subprocess.run([
                "java", "-jar", JACOCO_CLI_JAR, "report", merged_exec,
                "--classfiles", CLASS_FILES,
                "--html", REPORT_DIR,
                "--name", "Spring PetClinic Coverage Report (Cumulative)"
            ], check=True)
            
            # 检查报告是否成功生成
            index_file = os.path.join(REPORT_DIR, "index.html")
            if os.path.exists(index_file):
                return jsonify({
                    "status": "success", 
                    "url": "/coverage/report-html/index.html",
                    "exec_file": os.path.basename(merged_exec),
                    "file_type": "Cumulative",
                    "merge_info": merge_info
                })
            else:
                return jsonify({
                    "status": "error", 
                    "error": "Report generation failed - no index.html created"
                }), 500
                
        except subprocess.CalledProcessError as e:
            return jsonify({
                "status": "error", 
                "error": f"Report generation failed: {str(e)}"
            }), 500
        
    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error", 
            "error": f"操作失败: {str(e)}",
            "stderr": e.stderr if hasattr(e, 'stderr') else None
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error", 
            "error": str(e),
            "traceback": str(e.__traceback__)
        }), 500


@app.route("/coverage/check-classes")
def check_class_files():
    """检查class文件是否可用"""
    possible_paths = [
        "/spring-petclinic-classes/java/main",  # 共享卷路径
        "/spring-petclinic/build/classes/java/main",  # 直接路径
    ]
    
    available_paths = []
    for path in possible_paths:
        if os.path.exists(path):
            try:
                class_count = len([f for f in os.listdir(path) if f.endswith('.class')]) if os.path.isdir(path) else 0
                available_paths.append({
                    "path": path,
                    "exists": True,
                    "is_directory": os.path.isdir(path),
                    "class_files": class_count
                })
            except Exception as e:
                available_paths.append({
                    "path": path,
                    "exists": True,
                    "error": str(e)
                })
        else:
            available_paths.append({
                "path": path,
                "exists": False
            })
    
    return jsonify({
        "status": "success",
        "class_paths": available_paths,
        "current_config": CLASS_FILES
    })


@app.route("/coverage/auto-setup")
def auto_setup_class_files():
    """自动设置class文件路径"""
    global CLASS_FILES
    
    possible_paths = [
        "/spring-petclinic-classes/java/main",  # 共享卷路径
        "/spring-petclinic/build/classes/java/main",  # 直接路径
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            # 检查是否包含class文件（递归检查子目录）
            try:
                has_class_files = False
                for root, dirs, files in os.walk(path):
                    if any(f.endswith('.class') for f in files):
                        has_class_files = True
                        break
                
                if has_class_files:
                    CLASS_FILES = path
                    return jsonify({
                        "status": "success",
                        "message": f"Class files path updated to: {path}",
                        "path": path
                    })
            except Exception as e:
                continue
    
    return jsonify({
        "status": "error",
        "message": "No valid class files path found",
        "checked_paths": possible_paths
    }), 404


@app.route("/")
def index():
    """API首页"""
    return jsonify({
        "service": "JaCoCo Coverage API",
        "endpoints": {
            "/coverage/dump": "Check coverage file status",
            "/coverage/dump-tcp": "Dump coverage data via TCP",
            "/coverage/report": "Generate coverage report from available exec file",
            "/coverage/report-tcp": "Dump TCP data and generate report (overwrite mode)",
            "/coverage/report-tcp-cumulative": "Dump TCP data and merge with history (cumulative mode)",
            "/coverage/reset": "Clear all coverage data and history",
            "/coverage/check-classes": "Check available class file paths",
            "/coverage/auto-setup": "Automatically setup class file path",
            "/coverage/report-html/index.html": "View generated HTML report",
            "/health": "Service health check"
        }
    })


@app.route("/coverage/reset")
def reset_coverage():
    """清除所有覆盖率数据和历史记录"""
    try:
        import shutil
        
        files_to_remove = [
            TCP_EXEC_FILE,
            os.path.join(JACOCO_DIR, "jacoco-current.exec"),
            os.path.join(JACOCO_DIR, "jacoco-history.exec"),
            EXEC_FILE
        ]
        
        dirs_to_remove = [
            REPORT_DIR,
            os.path.join(JACOCO_DIR, "backups")
        ]
        
        removed_files = []
        removed_dirs = []
        
        # 删除文件
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
                removed_files.append(file_path)
        
        # 删除目录
        for dir_path in dirs_to_remove:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                removed_dirs.append(dir_path)
        
        # 重新创建报告目录
        os.makedirs(REPORT_DIR, exist_ok=True)
        
        return jsonify({
            "status": "success",
            "message": "所有覆盖率数据已清除",
            "removed_files": removed_files,
            "removed_dirs": removed_dirs
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/health")
def health():
    """健康检查端点"""
    try:
        # 检查Java是否可用
        java_result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        java_available = java_result.returncode == 0
        
        # 检查JaCoCo CLI是否存在
        jacoco_available = os.path.exists(JACOCO_CLI_JAR)
        
        # 检查目录权限
        jacoco_dir_writable = os.access("/jacoco", os.W_OK)
        
        return jsonify({
            "status": "healthy",
            "java_available": java_available,
            "jacoco_cli_available": jacoco_available,
            "jacoco_dir_writable": jacoco_dir_writable,
            "java_version": java_result.stderr if java_available else "N/A"
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
