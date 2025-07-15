import os
from huggingface_hub import HfApi

# === Step 1: 创建目录 ===
output_dir = "databank/raw/basemodel"
os.makedirs(output_dir, exist_ok=True)

# === Step 2: 初始化 Hugging Face API ===
api = HfApi()

models = api.list_models(
    sort="likes",         # 按点赞量排序
    direction=-1,         # 降序排序
    limit=1000            # 返回前 1000 个模型
)

base_model_path = os.path.join(output_dir, "basemodels_top1000_likes.txt")
error_model_path = os.path.join(output_dir, "error_finding_basemodels.txt")

# === Step 3: 清空文件（避免旧数据残留）===
open(base_model_path, "w").close()
open(error_model_path, "w").close()

# === Step 4: 实时处理和写入 ===
base_models = set()
error_models = set()

for model in models:
    try:
        model_info = api.model_info(model.modelId)
        card_data = model_info.card_data or {}
        if 'base_model' in card_data:
            base_model = card_data['base_model']
            if base_model is None:
                base_models.add(model_info.id)
                print("add base_model self:", model_info.id)
                with open(base_model_path, "a") as f:
                    f.write(model_info.id + "\n")
            else:
                if isinstance(base_model, list):
                    base_models.add(base_model[0])
                    print("add base_model dad:", base_model[0])
                    with open(base_model_path, "a") as f:
                        f.write(base_model[0] + "\n")
                else:
                    base_models.add(base_model)
                    print("add base_model dad:", base_model)
                    with open(base_model_path, "a") as f:
                        f.write(base_model + "\n")
    except Exception as e:
        print(f"Error accessing {model.modelId}: {e}")
        error_models.add(model.modelId)
        with open(error_model_path, "a") as f:
            f.write(model.modelId + "\n")
