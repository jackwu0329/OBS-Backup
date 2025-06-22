import os
import sys
import json
import shutil
from pathlib import Path

print("=== OBS 備份程序（Python 版）開始 ===")

# 取得 OBS 原始路徑
obs_path = os.path.join(os.environ["APPDATA"], "obs-studio")

if getattr(sys, 'frozen', False):
    # PyInstaller 打包後，取得 exe 所在資料夾
    base_path = Path(sys.executable).parent.resolve()
else:
    # Python 腳本執行
    base_path = Path(__file__).parent.resolve()

backup_dir = base_path / "backup"
backup_obs = backup_dir / "obs-studio"
backup_files = backup_dir / "files"

# 建立備份資料夾
backup_obs.mkdir(parents=True, exist_ok=True)
backup_files.mkdir(parents=True, exist_ok=True)

# 備份 obs-studio 整個資料夾（排除 crashes 和 logs）
print("[1/3] 備份 OBS 設定資料夾中...")

def ignore_folders(path, names):
    ignore_list = []
    if os.path.basename(path) == "obs-studio":
        if "crashes" in names:
            ignore_list.append("crashes")
        if "logs" in names:
            ignore_list.append("logs")
    return ignore_list

if obs_path and os.path.exists(obs_path):
    shutil.copytree(obs_path, backup_obs, dirs_exist_ok=True, ignore=ignore_folders)
    print("[1/3] 備份完成！")
else:
    print("[錯誤] 找不到 OBS 設定資料夾。")
    exit(1)


# 遍歷備份後的 basic/scenes 資料夾
scene_path = backup_obs / "basic" / "scenes"
if not scene_path.exists():
    print("[錯誤] 備份資料中未找到 basic/scenes。")
    exit(1)

print("[2/3] 搜尋 JSON 檔案中含有 \"file\": 的路徑...")

count = 0
for json_file in scene_path.glob("*.json"):
    print(f"處理: {json_file.name}")
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 遞迴搜尋所有 "file" 欄位
        def find_files(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "file" and isinstance(v, str):
                        yield v
                    else:
                        yield from find_files(v)
            elif isinstance(obj, list):
                for item in obj:
                    yield from find_files(item)

        for file_path in find_files(data):
            norm_path = os.path.normpath(file_path.strip('"'))
            if os.path.exists(norm_path):
                try:
                    shutil.copy(norm_path, backup_files)
                    print(f"  ↳ 已複製: {norm_path}")
                    count += 1
                except Exception as e:
                    print(f"  [錯誤] 複製失敗: {norm_path} → {e}")
            else:
                print(f"  [警告] 找不到檔案: {norm_path}")

    except Exception as e:
        print(f"[錯誤] 無法解析 {json_file.name} → {e}")

print(f"[3/3] 檔案處理完成 ✅ 共複製 {count} 筆檔案")

input("\n按 Enter 鍵結束...")

