"""
Memory audit script.
Measures RSS before and after each model load.
Run from the backend/ directory.
"""
import os, sys, gc

try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    HAVE_PSUTIL = False

def rss_mb():
    if HAVE_PSUTIL:
        return psutil.Process().memory_info().rss / 1024 / 1024
    # Fallback: read /proc/self/status (Linux only)
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except Exception:
        pass
    return None

def model_param_mb(model):
    total = sum(p.numel() * p.element_size() for p in model.parameters())
    return total / 1024 / 1024

def separator(label):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

# ------------------------------------------------------------------
separator("BASELINE (no models loaded)")
gc.collect()
baseline = rss_mb()
print(f"  RSS: {baseline:.1f} MB" if baseline else "  RSS: unavailable")

# ------------------------------------------------------------------
separator("After importing torch + transformers (import overhead)")
import torch
from transformers import AutoTokenizer, AutoModel, CLIPModel, CLIPProcessor
gc.collect()
after_imports = rss_mb()
print(f"  RSS: {after_imports:.1f} MB" if after_imports else "  RSS: unavailable")
if baseline and after_imports:
    print(f"  Import overhead: {after_imports - baseline:.1f} MB")

# ------------------------------------------------------------------
separator("Load TextSearchService model (all-MiniLM-l6-v2)")
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-l6-v2")
text_model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-l6-v2")
text_model.eval()
gc.collect()
after_text = rss_mb()
print(f"  RSS: {after_text:.1f} MB" if after_text else "  RSS: unavailable")
if after_imports and after_text:
    print(f"  Delta (text model): {after_text - after_imports:.1f} MB")
print(f"  Model param size: {model_param_mb(text_model):.1f} MB")
print(f"  Model dtype: {next(text_model.parameters()).dtype}")

import faiss, numpy as np
# Load text FAISS index if it exists
text_faiss_path = "faiss_indexes/text_index.faiss"
if os.path.isfile(text_faiss_path):
    text_index = faiss.read_index(text_faiss_path)
    gc.collect()
    after_text_faiss = rss_mb()
    print(f"\n  After loading text FAISS index:")
    print(f"    RSS: {after_text_faiss:.1f} MB" if after_text_faiss else "    RSS: unavailable")
    print(f"    Index ntotal={text_index.ntotal}, d={text_index.d}")
    print(f"    File size: {os.path.getsize(text_faiss_path)/1024:.1f} KB")
else:
    print(f"  text FAISS index not found at {text_faiss_path}")
    after_text_faiss = after_text

text_ids_path = "embeddings/text/product_ids.npy"
if os.path.isfile(text_ids_path):
    text_ids = np.load(text_ids_path)
    print(f"  text product_ids: {len(text_ids)} entries, {os.path.getsize(text_ids_path)/1024:.1f} KB")

# ------------------------------------------------------------------
separator("Load ImageSearchService model (CLIP ViT-B/32 float32)")
clip_name = "openai/clip-vit-base-patch32"
processor = CLIPProcessor.from_pretrained(clip_name)
clip_model = CLIPModel.from_pretrained(clip_name, torch_dtype=torch.float32)
clip_model.eval()
gc.collect()
after_clip = rss_mb()
print(f"  RSS: {after_clip:.1f} MB" if after_clip else "  RSS: unavailable")
if after_text_faiss and after_clip:
    print(f"  Delta (CLIP float32): {after_clip - after_text_faiss:.1f} MB")
print(f"  Model param size: {model_param_mb(clip_model):.1f} MB")
print(f"  Model dtype: {next(clip_model.parameters()).dtype}")

image_faiss_path = "faiss_indexes/image_index.faiss"
if os.path.isfile(image_faiss_path):
    image_index = faiss.read_index(image_faiss_path)
    gc.collect()
    after_image_faiss = rss_mb()
    print(f"\n  After loading image FAISS index:")
    print(f"    RSS: {after_image_faiss:.1f} MB" if after_image_faiss else "    RSS: unavailable")
    print(f"    Index ntotal={image_index.ntotal}, d={image_index.d}")
    print(f"    File size: {os.path.getsize(image_faiss_path)/1024:.1f} KB")
else:
    print(f"  image FAISS index not found at {image_faiss_path}")
    after_image_faiss = after_clip

image_ids_path = "embeddings/image/image_product_ids.npy"
if os.path.isfile(image_ids_path):
    image_ids = np.load(image_ids_path)
    print(f"  image product_ids: {len(image_ids)} entries, {os.path.getsize(image_ids_path)/1024:.1f} KB")

# ------------------------------------------------------------------
separator("TOTAL STEADY-STATE (both loaded)")
gc.collect()
total = rss_mb()
print(f"  RSS: {total:.1f} MB" if total else "  RSS: unavailable")
if baseline and total:
    print(f"  Total above baseline: {total - baseline:.1f} MB")

# ------------------------------------------------------------------
separator("CLIP in float16 — param size comparison")
clip_f16 = CLIPModel.from_pretrained(clip_name, torch_dtype=torch.float16)
clip_f16.eval()
print(f"  CLIP float16 param size: {model_param_mb(clip_f16):.1f} MB")
print(f"  CLIP float32 param size: {model_param_mb(clip_model):.1f} MB")
print(f"  Saving from float16:     {model_param_mb(clip_model) - model_param_mb(clip_f16):.1f} MB")
del clip_f16
gc.collect()

# ------------------------------------------------------------------
separator("Dynamic quantization of CLIP vision encoder — param size")
import torch.quantization
clip_q = CLIPModel.from_pretrained(clip_name, torch_dtype=torch.float32)
clip_q.eval()
try:
    clip_q_dyn = torch.quantization.quantize_dynamic(
        clip_q.vision_model, {torch.nn.Linear}, dtype=torch.qint8
    )
    dyn_mb = sum(
        p.numel() * p.element_size() for p in clip_q_dyn.parameters()
    ) / 1024 / 1024
    print(f"  Vision encoder float32 param MB: {model_param_mb(clip_q.vision_model):.1f} MB")
    print(f"  Vision encoder int8 param MB:    {dyn_mb:.1f} MB")
    print(f"  Note: actual RSS saving depends on runtime representation.")
except Exception as e:
    print(f"  Dynamic quantization failed: {e}")
del clip_q
gc.collect()

# ------------------------------------------------------------------
separator("SUMMARY TABLE")
print(f"  {'Component':<40} {'RSS Delta (MB)':>15}")
print(f"  {'-'*55}")
if baseline and after_imports:
    print(f"  {'torch + transformers import':<40} {after_imports - baseline:>15.1f}")
if after_imports and after_text:
    print(f"  {'all-MiniLM-l6-v2 (text model)':<40} {after_text - after_imports:>15.1f}")
if after_text and after_text_faiss:
    print(f"  {'text FAISS index':<40} {after_text_faiss - after_text:>15.1f}")
if after_text_faiss and after_clip:
    print(f"  {'CLIP ViT-B/32 float32':<40} {after_clip - after_text_faiss:>15.1f}")
if after_clip and after_image_faiss:
    print(f"  {'image FAISS index':<40} {after_image_faiss - after_clip:>15.1f}")
print(f"  {'-'*55}")
if baseline and total:
    print(f"  {'TOTAL above Python baseline':<40} {total - baseline:>15.1f}")
print(f"\n  Railway Starter plan limit: 512 MB")
if baseline and total:
    headroom = 512 - (total - baseline)
    print(f"  Estimated headroom:         {headroom:.1f} MB")
    if headroom < 50:
        print("  WARNING: Very tight. OOM risk is HIGH.")
    elif headroom < 150:
        print("  WARNING: Moderate risk. OOM likely under load.")
    else:
        print("  OK: Sufficient headroom for production use.")
