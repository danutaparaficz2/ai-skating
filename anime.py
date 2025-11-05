"""Simple remote-only image edit script.

This script does NOT load big models locally. It sends your image + prompt to a
remote inference endpoint (Qwen cloud or Hugging Face Inference API) and saves
back the returned image.

Why this change: your Mac crashed when loading large models locally. This file
removes all local model loading and only uses remote inference.

Usage (zsh):
  # Option A: Qwen cloud (preferred if you have it)
  export QWEN_API_URL="https://your-qwen-endpoint/v1/inference"
  export QWEN_API_KEY="<your_qwen_api_key>"
  python anime.py

  # Option B: Hugging Face Inference API
  export HUGGINGFACE_HUB_TOKEN="hf_xxx"
  export HF_MODEL="Qwen/Qwen-Image-Edit"  # optional
  python anime.py

Notes:
 - Do NOT paste API keys into chat. Set them as environment variables.
 - Remote inference will likely be billed by the provider. Check pricing.
"""

import os
import io
import json
import base64
import mimetypes
import requests
import time
import datetime
from PIL import Image

# ---------- Configuration (read from environment) ----------
# Read API URL and key. Support both our generic variable names and Alibaba DashScope names
# DashScope docs recommend using DASHSCOPE_API_KEY and DASHSCOPE_HTTP_BASE_URL
QWEN_API_URL = os.getenv("QWEN_API_URL") or os.getenv("DASHSCOPE_HTTP_BASE_URL")
QWEN_API_KEY = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
import certifi
# Simple defaults
INPUT_IMAGE_PATH = os.getenv("INPUT_IMAGE_PATH", "Milad.jpg")
OUTPUT_IMAGE_PATH = os.getenv("OUTPUT_IMAGE_PATH", "output_remote.png")
PROMPT = os.getenv("PROMPT", "Convert the image into a stunning, detailed Japanese anime style, high quality, vibrant colors, cinematic lighting.")
NEGATIVE_PROMPT = os.getenv("NEGATIVE_PROMPT", "low quality, bad anatomy, blurry, unrealistic, cgi, 3d, rendering, photo, cropped")
NUM_STEPS = int(os.getenv("NUM_INFERENCE_STEPS", "20"))
NUM_OUTPUTS = int(os.getenv("NUM_OUTPUTS", "1"))
QWEN_MODEL = os.getenv("QWEN_MODEL") or os.getenv("DASHSCOPE_MODEL") or "qwen-image-edit-plus"

# Prefer the vendor SDK; require it for the simple mode
try:
    import dashscope
    from dashscope import MultiModalConversation
except Exception:
    dashscope = None
    MultiModalConversation = None

# ---------- Helpers ----------

def load_image_as_base64(path: str) -> str:
    """Read the original file bytes and return base64-encoded data (no data: prefix).

    Caller may choose to wrap this into a data URI with the appropriate mime type.
    """
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("ascii")


def build_data_uri(path: str) -> str:
    """Return a data:{mime};base64,{data} string suitable for the Qwen API.

    Uses the file extension to guess the mime type (falls back to image/jpeg).
    """
    b64 = load_image_as_base64(path)
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/jpeg"
    return f"data:{mime};base64,{b64}"


def save_base64_image(b64: str, out_path: str) -> None:
    data = base64.b64decode(b64)
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.save(out_path)


# ---------- Main (very simple) ----------

def main():
    # Check we have QWEN credentials configured
    if not (QWEN_API_URL and QWEN_API_KEY):
        print("ERROR: QWEN_API_URL and QWEN_API_KEY must be set for remote inference.")
        return

    # Make sure input image exists
    if not os.path.exists(INPUT_IMAGE_PATH):
        print(f"ERROR: Input image not found at '{INPUT_IMAGE_PATH}'.")
        print("Set INPUT_IMAGE_PATH environment variable or place a file named 'input.jpg' next to this script.")
        return

    print("Encoding image to base64...")
    encode_start = time.time()
    print("Encode start:", datetime.datetime.utcnow().isoformat() + "Z")
    img_b64 = load_image_as_base64(INPUT_IMAGE_PATH)
    encode_end = time.time()
    print("Encode end:", datetime.datetime.utcnow().isoformat() + "Z")
    print(f"Encoding elapsed (seconds): {encode_end - encode_start:.3f}")

    # Build request following DashScope / Qwen docs:
    # {
    #   "model": "qwen-image-edit-plus",
    #   "input": { "messages": [ { "role": "user", "content": [ {"image": "data:..."}, {"text": "prompt"} ] } ] },
    #   "parameters": { "n": 1, "negative_prompt": " ", "watermark": false }
    # }
    data_uri = build_data_uri(INPUT_IMAGE_PATH)
    payload = {
        "model": QWEN_MODEL,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"image": data_uri},
                        {"text": PROMPT}
                    ]
                }
            ]
        },
        "parameters": {
            "n": NUM_OUTPUTS,
            "negative_prompt": NEGATIVE_PROMPT,
            "watermark": False
        }
    }

    # QWEN cloud is required for remote inference in this simplified script
    if not (QWEN_API_URL and QWEN_API_KEY):
        print("ERROR: QWEN_API_URL and QWEN_API_KEY must be set for remote inference.")
        return

    # Use vendor SDK (dashscope) for the request. This is the simplest path and
    # matches the Alibaba Cloud example: build messages and call
    # MultiModalConversation.call(...). If the SDK isn't installed, explain how
    # to install it and fail fast.
    if MultiModalConversation is None:
        print("ERROR: dashscope SDK is not installed. Install it with: python -m pip install dashscope")
        return

    # If user supplied a full QWEN_API_URL that contains /api/v1, set the SDK base
    # URL accordingly so the SDK uses the correct region endpoint.
    try:
        if QWEN_API_URL and "/api/v1" in QWEN_API_URL:
            dashscope.base_http_api_url = QWEN_API_URL.split("/api/v1")[0] + "/api/v1"
        else:
            # default to Singapore if not explicitly provided
            dashscope.base_http_api_url = dashscope.base_http_api_url or "https://dashscope-intl.aliyuncs.com/api/v1"
    except Exception:
        pass

    print("Calling DashScope SDK MultiModalConversation...")
    start_ts = time.time()
    messages = payload["input"]["messages"]
    sdk_resp = MultiModalConversation.call(
        api_key=QWEN_API_KEY,
        model=QWEN_MODEL,
        messages=messages,
        stream=False,
        n=NUM_OUTPUTS,
        watermark=False,
        negative_prompt=NEGATIVE_PROMPT,
    )
    end_ts = time.time()
    print("Response received:", datetime.datetime.utcnow().isoformat() + "Z")
    print(f"Request elapsed (seconds): {end_ts - start_ts:.3f}")

    # The SDK returns .status_code and .output structures matching the HTTP API.
    if getattr(sdk_resp, "status_code", None) != 200:
        print("SDK call failed:", getattr(sdk_resp, "status_code", None))
        try:
            print(sdk_resp)
        except Exception:
            pass
        return

    body = {}
    if hasattr(sdk_resp, "output"):
        body["output"] = sdk_resp.output

    # Helper to download a URL and save to disk
    def download_and_save(url: str, out_path: str) -> None:
        try:
            with requests.get(url, stream=True, timeout=60, verify=certifi.where()) as r:
                r.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in r.iter_content(1024 * 32):
                        if chunk:
                            f.write(chunk)
        except Exception as e:
            print(f"Failed to download {url}: {e}")

    # Try the documented 'output' -> choices path first
    images_saved = 0
    try:
        output = body.get("output") if isinstance(body, dict) else None
        if output and "choices" in output and output["choices"]:
            contents = output["choices"][0]["message"]["content"]
            for i, item in enumerate(contents):
                if not isinstance(item, dict):
                    continue
                if "image" in item and item["image"]:
                    imgval = item["image"]
                    # Either a data URI or an http(s) URL
                    if isinstance(imgval, str) and imgval.startswith("data:"):
                        # strip data:<mime>;base64,
                        prefix, b64data = imgval.split(",", 1)
                        out_path = OUTPUT_IMAGE_PATH if NUM_OUTPUTS == 1 else f"{os.path.splitext(OUTPUT_IMAGE_PATH)[0]}_{i+1}{os.path.splitext(OUTPUT_IMAGE_PATH)[1]}"
                        save_base64_image(b64data, out_path)
                        print(f"Saved remote result to {out_path}")
                        images_saved += 1
                    elif isinstance(imgval, str) and imgval.startswith("http"):
                        out_path = OUTPUT_IMAGE_PATH if NUM_OUTPUTS == 1 else f"{os.path.splitext(OUTPUT_IMAGE_PATH)[0]}_{i+1}{os.path.splitext(OUTPUT_IMAGE_PATH)[1]}"
                        download_and_save(imgval, out_path)
                        print(f"Downloaded remote result to {out_path}")
                        images_saved += 1
        # Fallback: some endpoints may return choices differently or a list under 'images'
        if images_saved == 0 and isinstance(body, dict):
            # old-style 'images' or 'image' fields
            if "images" in body and body["images"]:
                for i, b64item in enumerate(body["images"]):
                    out_path = OUTPUT_IMAGE_PATH if len(body["images"]) == 1 else f"{os.path.splitext(OUTPUT_IMAGE_PATH)[0]}_{i+1}{os.path.splitext(OUTPUT_IMAGE_PATH)[1]}"
                    save_base64_image(b64item, out_path)
                    print(f"Saved remote result to {out_path}")
                    images_saved += 1
            elif "image" in body:
                save_base64_image(body["image"], OUTPUT_IMAGE_PATH)
                print(f"Saved remote result to {OUTPUT_IMAGE_PATH}")
                images_saved += 1
    except Exception as e:
        print("Error parsing response JSON:", e)
        try:
            print(json.dumps(body)[:1000])
        except Exception:
            print(str(body)[:1000])

    if images_saved == 0:
        print("No images were saved. Response (first 2000 chars):")
        try:
            print(json.dumps(body)[:2000])
        except Exception:
            print(str(body)[:2000])


if __name__ == "__main__":
    main()