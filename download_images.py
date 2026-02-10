import os
import json
import requests
from PIL import Image
from io import BytesIO
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

BASE_DIR = '/var/www/seoulwatch'
IMAGES_DIR = os.path.join(BASE_DIR, 'images/products')
PRODUCTS_FILE = os.path.join(BASE_DIR, 'data/products.json')

MAX_WIDTH = 1200
JPEG_QUALITY = 85
MAX_WORKERS = 10

os.makedirs(IMAGES_DIR, exist_ok=True)

def get_filename_from_url(url, product_id, index):
    """Generate a clean filename from URL"""
    ext = url.split('.')[-1].split('?')[0].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        ext = 'jpg'
    return f"{product_id}_{index}.{ext}"

def download_and_resize(url, save_path):
    """Download image and resize if needed"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too large
        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)
        
        # Save as JPEG
        save_path_jpg = save_path.rsplit('.', 1)[0] + '.jpg'
        img.save(save_path_jpg, 'JPEG', quality=JPEG_QUALITY, optimize=True)
        
        return save_path_jpg
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def process_product(product):
    """Process all images for a product"""
    product_id = product['id']
    images = product.get('images', [])
    
    local_images = []
    for i, url in enumerate(images):
        if not url:
            continue
        
        filename = f"{product_id}_{i}.jpg"
        save_path = os.path.join(IMAGES_DIR, filename)
        
        # Skip if already exists
        if os.path.exists(save_path):
            local_images.append(f"images/products/{filename}")
            continue
        
        result = download_and_resize(url, save_path)
        if result:
            local_images.append(f"images/products/{os.path.basename(result)}")
    
    return product_id, local_images

# Load products
with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

products = data['products']
total = len(products)
completed = 0
start_time = time.time()

print(f"Processing {total} products...")

# Process products
for product in products:
    product_id, local_images = process_product(product)
    
    if local_images:
        product['image'] = local_images[0]
        product['images'] = local_images
    
    completed += 1
    if completed % 10 == 0:
        elapsed = time.time() - start_time
        rate = completed / elapsed
        remaining = (total - completed) / rate if rate > 0 else 0
        print(f"Progress: {completed}/{total} ({completed*100//total}%) - ETA: {remaining/60:.1f} min")

# Save updated products
with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nCompleted! Total time: {(time.time() - start_time)/60:.1f} minutes")
