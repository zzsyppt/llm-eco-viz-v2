import json
import os
import multiprocessing
from huggingface_hub import HfApi
from datetime import datetime
import glob

# ==== 配置 ====
INPUT_FILE = "databank/model_tree/model_tree_raw.json"
OUTPUT_FOLDER = "databank/model_metadata_bingfa"
FINAL_OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "model_metadata_merged.json")
N_WORKERS = 3

# ==== 初始化输出目录 ====
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ==== 工具函数 ====
def log_error(model_id, error_file):
    with open(error_file, "a", encoding="utf-8") as f:
        f.write(f"{model_id}\n")

def fetch_model_metadata(model_id, api: HfApi):
    try:
        model_info = api.model_info(model_id)

        region = model_info.tags[-1] if model_info.tags else None
        language = model_info.card_data.get('language', []) if model_info.card_data else []

        return {
            "downloads": model_info.downloads,
            "likes": model_info.likes,
            "spaces": model_info.spaces or [],
            "spaces_count": len(model_info.spaces) if model_info.spaces else 0,
            "author": model_info.author,
            "created_at": model_info.created_at.strftime("%Y-%m-%d") if model_info.created_at else None,
            "last_modified": model_info.last_modified.strftime("%Y-%m-%d") if model_info.last_modified else None,
            "region": region,
            "language": language,
            "pipeline_tag": model_info.pipeline_tag or None
        }
    except Exception as e:
        print(f"[Error] {model_id}: {e}")
        return None

def split_dict_equally(d, n):
    items = list(d.items())
    size = len(items) // n
    return [dict(items[i*size:(i+1)*size]) for i in range(n-1)] + [dict(items[(n-1)*size:])]

# ==== 工作进程函数（实时写入 JSONL）====
def run_worker(worker_id, model_tree_slice, output_file, error_file):
    api = HfApi()
    processed = 0

    with open(output_file, "a", encoding="utf-8") as f_out:
        for base_model, derived_categories in model_tree_slice.items():
            print(f"[Worker {worker_id}] Base: {base_model}")
            meta = fetch_model_metadata(base_model, api)
            if meta:
                json.dump({base_model: meta}, f_out, ensure_ascii=False)
                f_out.write("\n")
                processed += 1
            else:
                log_error(base_model, error_file)

            for category, models in derived_categories.items():
                for model_id in models:
                    if not model_id: continue
                    print(f"[Worker {worker_id}] Model: {model_id}")
                    meta = fetch_model_metadata(model_id, api)
                    if meta:
                        json.dump({model_id: meta}, f_out, ensure_ascii=False)
                        f_out.write("\n")
                        processed += 1
                    else:
                        log_error(model_id, error_file)

    print(f"[Worker {worker_id}] Done. Wrote {processed} records to {output_file}")

# ==== 合并多个 JSONL 文件 ====
def merge_jsonl_files(folder, pattern="model_metadata_worker*.jsonl", output_file="model_metadata_merged.json"):
    all_data = {}
    for file in glob.glob(os.path.join(folder, pattern)):
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    all_data.update(data)
                except Exception as e:
                    print(f"Error parsing line in {file}: {e}")

    final_path = os.path.join(folder, output_file)
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

    print(f"[MERGE] Combined {len(all_data)} records into {final_path}")

# ==== 主程序 ====
if __name__ == "__main__":
    print(f"=== Parallel Metadata Realtime Writer ===")
    print(f"Loading model tree from: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        model_tree = json.load(f)

    print(f"Loaded {len(model_tree)} base models. Splitting into {N_WORKERS} workers...")

    slices = split_dict_equally(model_tree, N_WORKERS)
    processes = []

    for i in range(N_WORKERS):
        output_file = os.path.join(OUTPUT_FOLDER, f"model_metadata_worker{i+1}.jsonl")
        error_file = os.path.join(OUTPUT_FOLDER, f"error_worker{i+1}.txt")
        p = multiprocessing.Process(
            target=run_worker,
            args=(i+1, slices[i], output_file, error_file)
        )
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    print("All workers finished. Merging...")
    merge_jsonl_files(OUTPUT_FOLDER)

    print("✅ All done.")
