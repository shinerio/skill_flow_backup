#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import oss2
import requests
from dotenv import load_dotenv


def fail(stage: str, error: str, extra: Optional[Dict[str, Any]] = None, exit_code: int = 1):
    payload = {"ok": False, "stage": stage, "error": error}
    if extra:
        payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(exit_code)


def slugify(text: str, default: str = "image") -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80] or default


@dataclass
class Settings:
    apimart_api_key: str
    aliyun_oss_access_key_id: str
    aliyun_oss_access_key_secret: str
    aliyun_oss_bucket: str
    aliyun_oss_region: str
    aliyun_oss_endpoint: str
    aliyun_oss_public_base_url: str
    aliyun_oss_prefix: str
    image_gen_default_model: str
    image_gen_default_size: str
    image_gen_default_resolution: str
    image_gen_download_dir: str
    image_gen_poll_interval_seconds: int
    image_gen_timeout_seconds: int


class APIMartImagePipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = "https://api.apimart.ai/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.settings.apimart_api_key}",
            "Content-Type": "application/json",
        })

    @classmethod
    def from_env(cls, env_path: Optional[str] = None):
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

        def req(name: str) -> str:
            value = os.getenv(name)
            if not value:
                fail("config", f"missing required env var: {name}")
            return value

        region = req("ALIYUN_OSS_REGION")
        if os.getenv("ALIYUN_OSS_ENDPOINT"):
            endpoint = os.getenv("ALIYUN_OSS_ENDPOINT")
        else:
            endpoint = f"https://oss-{region}.aliyuncs.com"
        bucket = req("ALIYUN_OSS_BUCKET")
        if os.getenv("ALIYUN_OSS_PUBLIC_BASE_URL"):
            public_base = os.getenv("ALIYUN_OSS_PUBLIC_BASE_URL").rstrip("/")
        else:
            # For Aliyun OSS public access, prefer third-level bucket domain:
            # https://<bucket>.oss-<region>.aliyuncs.com
            # If the endpoint already includes the bucket hostname, use it directly.
            endpoint_clean = endpoint.rstrip("/")
            if bucket in endpoint_clean:
                public_base = endpoint_clean
            else:
                parsed = requests.utils.urlparse(endpoint_clean)
                scheme = parsed.scheme or "https"
                host = parsed.netloc or parsed.path
                public_base = f"{scheme}://{bucket}.{host}"
            public_base = public_base.rstrip("/")

        settings = Settings(
            apimart_api_key=req("APIMART_API_KEY"),
            aliyun_oss_access_key_id=req("ALIYUN_OSS_ACCESS_KEY_ID"),
            aliyun_oss_access_key_secret=req("ALIYUN_OSS_ACCESS_KEY_SECRET"),
            aliyun_oss_bucket=bucket,
            aliyun_oss_region=region,
            aliyun_oss_endpoint=endpoint,
            aliyun_oss_public_base_url=public_base.rstrip("/"),
            aliyun_oss_prefix=(os.getenv("ALIYUN_OSS_PREFIX") or "generated-images/").lstrip("/"),
            image_gen_default_model=os.getenv("IMAGE_GEN_DEFAULT_MODEL") or "gemini-3.1-flash-image-preview",
            image_gen_default_size=os.getenv("IMAGE_GEN_DEFAULT_SIZE") or "16:9",
            image_gen_default_resolution=(os.getenv("IMAGE_GEN_DEFAULT_RESOLUTION") or "1K").upper(),
            image_gen_download_dir=os.getenv("IMAGE_GEN_DOWNLOAD_DIR") or "/tmp/openclaw-image-gen",
            image_gen_poll_interval_seconds=int(os.getenv("IMAGE_GEN_POLL_INTERVAL_SECONDS") or "3"),
            image_gen_timeout_seconds=int(os.getenv("IMAGE_GEN_TIMEOUT_SECONDS") or "180"),
        )
        return cls(settings)

    def submit_generation(self, prompt: str, model: Optional[str], size: Optional[str], resolution: Optional[str], n: int = 1) -> Dict[str, Any]:
        # APIMart Gemini image generation format:
        # model -> model id
        # prompt -> text description
        # size -> aspect ratio (e.g. "16:9", "1:1")
        # resolution -> 0.5K / 1K / 2K / 4K
        # n -> number of images 1-4
        # official_fallback -> optional bool
        # image_urls -> optional list of reference image URLs

        # We handle aspect ratio / resolution conversion when input is pixels:
        # If the input looks like "WxH" (e.g. "1792x1024"), we convert it to aspect ratio and guess resolution.
        size = size or self.settings.image_gen_default_size
        model = model or self.settings.image_gen_default_model

        # Parse into APIMart format
        aspect_ratio, inferred_resolution = self._parse_size(size)
        resolution = (resolution or self.settings.image_gen_default_resolution or inferred_resolution).upper()
        if resolution not in {"0.5K", "1K", "2K", "4K"}:
            fail("config", f"invalid resolution: {resolution}", {"allowed": ["0.5K", "1K", "2K", "4K"]})

        payload = {
            "prompt": prompt,
            "model": model,
            "size": aspect_ratio,
            "resolution": resolution,
            "n": max(1, min(4, n)),
            "official_fallback": False,
            "google_search": False,
            "google_image_search": False,
        }
        url = f"{self.base_url}/images/generations"
        try:
            resp = self.session.post(url, json=payload, timeout=60)
        except Exception as e:
            fail("generate", f"request failed: {e}")

        if resp.status_code >= 400:
            fail("generate", f"provider returned {resp.status_code}", {"body": safe_text(resp.text)})

        try:
            data = resp.json()
        except Exception:
            fail("generate", "provider response is not valid JSON", {"body": safe_text(resp.text)})

        return data

    # All aspect ratios supported by APIMart
    _SUPPORTED_RATIOS = [
        ("1:1", 1/1),
        ("3:2", 3/2), ("2:3", 2/3),
        ("4:3", 4/3), ("3:4", 3/4),
        ("16:9", 16/9), ("9:16", 9/16),
        ("5:4", 5/4), ("4:5", 4/5),
        ("21:9", 21/9),
        ("1:4", 1/4), ("4:1", 4/1),
        ("1:8", 1/8), ("8:1", 8/1),
    ]

    def _parse_size(self, size_str: str) -> tuple[str, str]:
        """Convert input size to APIMart (aspect_ratio, resolution).

        Accepts either native API format ("16:9") or pixel format ("1792x1024").
        Pixel format is snapped to the nearest supported aspect ratio.
        """
        size_str = size_str.strip()

        # Already in APIMart aspect ratio format like "16:9", "1:1"
        if ":" in size_str and "x" not in size_str:
            return size_str, "1K"

        # Pixel format like "1792x1024" -> snap to nearest supported ratio
        if "x" in size_str.lower():
            try:
                w_str, h_str = size_str.lower().split("x")
                w = int(w_str.strip())
                h = int(h_str.strip())
                target = w / h
                aspect = min(self._SUPPORTED_RATIOS, key=lambda r: abs(r[1] - target))[0]
                max_dim = max(w, h)
                if max_dim <= 512:
                    resolution = "0.5K"
                elif max_dim <= 1024:
                    resolution = "1K"
                elif max_dim <= 2048:
                    resolution = "2K"
                else:
                    resolution = "4K"
                return aspect, resolution
            except Exception:
                pass

        fail("config", f"unsupported size format: {size_str!r}. Use aspect ratio (e.g. '16:9') or pixels (e.g. '1792x1024')")
        return "", ""

    def extract_task_id(self, submit_data: Dict[str, Any]) -> str:
        candidates = [
            submit_data.get("task_id"),
            submit_data.get("id"),
            (submit_data.get("data") or {}).get("task_id") if isinstance(submit_data.get("data"), dict) else None,
            (submit_data.get("data") or {}).get("id") if isinstance(submit_data.get("data"), dict) else None,
        ]
        # Check if data is a list
        if isinstance(submit_data.get("data"), list) and len(submit_data["data"]) > 0:
            first = submit_data["data"][0]
            if isinstance(first, dict):
                candidates.insert(0, first.get("task_id"))
                candidates.insert(1, first.get("id"))
        for c in candidates:
            if c:
                return c
        fail("generate", "no task_id found in provider response", {"response": submit_data})
        return ""

    def poll_task(self, task_id: str) -> Dict[str, Any]:
        start = time.time()
        url = f"{self.base_url}/tasks/{task_id}"
        while True:
            if time.time() - start > self.settings.image_gen_timeout_seconds:
                fail("poll", f"task timed out after {self.settings.image_gen_timeout_seconds}s", {"task_id": task_id})
            try:
                resp = self.session.get(url, timeout=30)
            except Exception as e:
                fail("poll", f"request failed: {e}", {"task_id": task_id})

            if resp.status_code >= 400:
                fail("poll", f"provider returned {resp.status_code}", {"task_id": task_id, "body": safe_text(resp.text)})

            try:
                data = resp.json()
            except Exception:
                fail("poll", "provider response is not valid JSON", {"task_id": task_id, "body": safe_text(resp.text)})

            status = self.extract_status(data)
            if status in {"succeeded", "success", "completed", "done", "finished"}:
                return data
            if status in {"failed", "error", "cancelled", "canceled"}:
                fail("poll", f"task failed with status={status}", {"task_id": task_id, "response": data})

            time.sleep(self.settings.image_gen_poll_interval_seconds)

    def extract_status(self, data: Dict[str, Any]) -> str:
        candidates = [
            data.get("status"),
            data.get("state"),
            (data.get("data") or {}).get("status") if isinstance(data.get("data"), dict) else None,
            (data.get("data") or {}).get("state") if isinstance(data.get("data"), dict) else None,
        ]
        for c in candidates:
            if isinstance(c, str) and c.strip():
                return c.strip().lower()
        return "unknown"

    def extract_result_urls(self, data: Dict[str, Any]) -> List[str]:
        urls: List[str] = []

        def visit(node: Any):
            if isinstance(node, dict):
                for k, v in node.items():
                    lk = str(k).lower()
                    if lk in {"url", "image_url", "download_url"}:
                        if isinstance(v, str) and v.startswith("http"):
                            urls.append(v)
                        elif isinstance(v, list):
                            for item in v:
                                if isinstance(item, str) and item.startswith("http"):
                                    urls.append(item)
                    visit(v)
            elif isinstance(node, list):
                for item in node:
                    visit(item)

        visit(data)
        deduped = []
        seen = set()
        for u in urls:
            if u not in seen:
                deduped.append(u)
                seen.add(u)
        if not deduped:
            fail("download", "no result URLs found in completed task payload", {"response": data})
        return deduped

    def download_images(self, urls: List[str], prompt: str) -> List[str]:
        out_dir = Path(self.settings.image_gen_download_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        base = slugify(prompt, default="image")
        paths: List[str] = []
        for idx, url in enumerate(urls, start=1):
            try:
                resp = requests.get(url, timeout=120)
                resp.raise_for_status()
            except Exception as e:
                fail("download", f"failed to download image: {e}", {"url": url})

            content_type = resp.headers.get("Content-Type", "image/png").split(";")[0].strip()
            ext = mimetypes.guess_extension(content_type)
            if not ext or ext == ".bin":
                url_path = requests.utils.urlparse(url).path
                url_ext = Path(url_path).suffix.lower()
                if url_ext in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                    ext = ".jpg" if url_ext == ".jpeg" else url_ext
                else:
                    ext = ".png"
            file_path = out_dir / f"{base}-{timestamp}-{idx}{ext}"
            file_path.write_bytes(resp.content)
            paths.append(str(file_path))
        return paths

    def oss_bucket(self):
        auth = oss2.Auth(self.settings.aliyun_oss_access_key_id, self.settings.aliyun_oss_access_key_secret)
        return oss2.Bucket(auth, self.settings.aliyun_oss_endpoint, self.settings.aliyun_oss_bucket)

    def build_object_key(self, local_path: str, prompt: str) -> str:
        now = datetime.now(timezone.utc)
        ext = Path(local_path).suffix or ".png"
        base = slugify(prompt, default="image")
        ts = now.strftime("%Y%m%d-%H%M%S")
        prefix = self.settings.aliyun_oss_prefix.rstrip("/")
        return f"{prefix}/{now:%Y/%m/%d}/{base}-{ts}{ext}"

    def upload_to_oss(self, local_path: str, prompt: str) -> Dict[str, Any]:
        key = self.build_object_key(local_path, prompt)
        content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
        bucket = self.oss_bucket()
        headers = {"Content-Type": content_type}
        try:
            bucket.put_object_from_file(key, local_path, headers=headers)
        except Exception as e:
            fail("upload", f"failed to upload to OSS: {e}", {"local_path": local_path, "object_key": key})

        return {
            "url": f"{self.settings.aliyun_oss_public_base_url}/{key}",
            "object_key": key,
            "content_type": content_type,
        }

    def run(self, prompt: str, model: Optional[str], size: Optional[str], resolution: Optional[str], n: int) -> Dict[str, Any]:
        submit_data = self.submit_generation(prompt=prompt, model=model, size=size, resolution=resolution, n=n)
        task_id = self.extract_task_id(submit_data)
        final_data = self.poll_task(task_id)
        urls = self.extract_result_urls(final_data)
        local_files = self.download_images(urls, prompt)
        uploaded = [self.upload_to_oss(p, prompt) for p in local_files]
        for p in local_files:
            try:
                Path(p).unlink()
            except Exception:
                pass
        return {
            "ok": True,
            "provider": "apimart",
            "model": model or self.settings.image_gen_default_model,
            "size": size or self.settings.image_gen_default_size,
            "resolution": (resolution or self.settings.image_gen_default_resolution).upper(),
            "task_id": task_id,
            "prompt": prompt,
            "local_files": local_files,
            "uploaded": uploaded,
        }


def safe_text(text: str, max_len: int = 2000) -> str:
    text = text or ""
    return text[:max_len]


def parse_args():
    parser = argparse.ArgumentParser(description="Generate image via APIMart and upload to Aliyun OSS")
    parser.add_argument("--prompt", required=True, help="Final image prompt")
    parser.add_argument("--model", default=None, help="Image model")
    parser.add_argument("--size", default=None, help="Image size, e.g. 1536x1024")
    parser.add_argument("--resolution", default=None, help="Image resolution: 1K, 2K, 4K")
    parser.add_argument("--n", type=int, default=1, help="Number of images")
    parser.add_argument("--env-file", default=None, help="Path to .env file")
    return parser.parse_args()


def main():
    args = parse_args()
    pipeline = APIMartImagePipeline.from_env(args.env_file)
    result = pipeline.run(prompt=args.prompt, model=args.model, size=args.size, resolution=args.resolution, n=args.n)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
