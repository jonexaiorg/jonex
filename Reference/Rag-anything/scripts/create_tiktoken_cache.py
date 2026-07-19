import tiktoken
import os

# Define the directory where you want to store the cache
cache_dir = "./tiktoken_cache"
if "TIKTOKEN_CACHE_DIR" not in os.environ:
    os.environ["TIKTOKEN_CACHE_DIR"] = cache_dir

# Create the directory if it doesn't exist
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

print("Downloading and caching tiktoken models...")
tiktoken.get_encoding("cl100k_base")
# tiktoken.get_encoding("p50k_base")

print(f"tiktoken models have been cached in '{cache_dir}'")
