import os
import json
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

BATCH_SIZE = 50
HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_user_data(user_or_org_name):
    url = f"https://huggingface.co/{user_or_org_name}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return user_or_org_name, None

    soup = BeautifulSoup(response.content, "html.parser")
    data = {}

    body_class = soup.body.get("class", [])
    if "OrgPage" in body_class:
        data["type"] = "org"
        data["full_name"] = soup.find("h1", class_="mb-2 mr-3 text-2xl font-bold md:mb-0").text.strip()
        photo_tag = soup.find("img", class_="h-full w-full rounded-lg object-cover")
        data["photo"] = photo_tag["src"] if photo_tag else None
        type_tag = soup.find("span", class_="capitalize")
        data["nature"] = type_tag.text.strip() if type_tag else None
        website_tag = soup.find("a", rel="nofollow", href=True)
        data["website"] = website_tag["href"] if website_tag else None
        github_tag = soup.find("a", href=lambda href: href and "github.com" in href)
        data["github"] = github_tag["href"] if github_tag else None
        followers_tag = soup.find("span", title=lambda title: title and "followers" in title.lower())
        data["followers"] = followers_tag.text.strip() if followers_tag else "0"
        model_count_tag = soup.find("span", class_="ml-3 w-7 font-normal text-gray-400")
        data["models"] = model_count_tag.text.strip() if model_count_tag else "0"

    elif "UserPage" in body_class:
        data["type"] = "usr"
        full_name_tag = soup.find("span", class_="mr-3 leading-6")
        data["full_name"] = full_name_tag.text.strip() if full_name_tag else None
        profile_picture_tag = soup.find("img", class_="h-32 w-32 overflow-hidden rounded-full shadow-inner lg:h-48 lg:w-48")
        data["photo"] = profile_picture_tag["src"] if profile_picture_tag else None
        github_tag = soup.find("a", href=lambda href: href and "github.com" in href)
        data["github"] = github_tag["href"] if github_tag else None

        org_tags = soup.select("div.mt-3.flex.flex-wrap a.mb-1.mr-1.inline-block")
        data["organizations"] = [
            {"name": org.get("href", "").strip("/"), "logo": org.find("img")["src"]} for org in org_tags
        ]

        followers_tag = soup.find("button", string=lambda s: s and "following" in s.lower())
        data["followers"] = followers_tag.text.strip() if followers_tag else "0"

        models_count_tag = soup.find("div", id="models")
        if models_count_tag:
            models_header = models_count_tag.find("h3")
            model_count_span = models_header.find("span", class_="ml-3 w-7 font-normal text-gray-400")
            data["models"] = model_count_span.text.strip() if model_count_span else "0"
    else:
        return user_or_org_name, None

    return user_or_org_name, data


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def parallel_main():
    input_file = "databank/raw/model_metadata/model_metadata.json"
    output_dir = "databank/raw/author_metadata/"
    org_output_file = os.path.join(output_dir, "org_data.json")
    usr_output_file = os.path.join(output_dir, "usr_data.json")
    error_file = os.path.join(output_dir, "error_getting_author_info.txt")
    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as f:
        model_metadata = json.load(f)

    user_or_org_list = list(set(key.split("/")[0] for key in model_metadata.keys()))

    # 读取现有数据
    org_data = {}
    usr_data = {}
    if os.path.exists(org_output_file):
        with open(org_output_file, "r", encoding="utf-8") as f:
            org_data = json.load(f)
    if os.path.exists(usr_output_file):
        with open(usr_output_file, "r", encoding="utf-8") as f:
            usr_data = json.load(f)

    done = set(org_data.keys()) | set(usr_data.keys())
    to_fetch = [name for name in user_or_org_list if name not in done]

    org_batch = {}
    usr_batch = {}

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_user_data, name): name for name in to_fetch}
        for idx, future in enumerate(tqdm(as_completed(futures), total=len(futures), desc="Fetching")):
            name, result = future.result()
            if result is None:
                print(f"[❌] {name} - Failed")
                with open(error_file, "a", encoding="utf-8") as ef:
                    ef.write(f"{name}\n")
                continue

            print(f"[✅] {name} - {result['type']}")
            if result["type"] == "org":
                org_data[name] = result
                org_batch[name] = result
            else:
                usr_data[name] = result
                usr_batch[name] = result

            # 每 BATCH_SIZE 条就写一次
            if (len(org_batch) + len(usr_batch)) >= BATCH_SIZE:
                if org_batch:
                    write_json(org_output_file, org_data)
                    org_batch.clear()
                if usr_batch:
                    write_json(usr_output_file, usr_data)
                    usr_batch.clear()

    # 写入剩余的
    if org_batch:
        write_json(org_output_file, org_data)
    if usr_batch:
        write_json(usr_output_file, usr_data)

    print("✅ All data saved.")
    print(f"📁 Org -> {org_output_file}")
    print(f"📁 Usr -> {usr_output_file}")
    print(f"📄 Errors -> {error_file}")


if __name__ == "__main__":
    parallel_main()
