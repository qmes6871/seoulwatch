#!/usr/bin/env python3
"""
네이버 스마트스토어 상품을 가져와서 products.json을 대체하는 스크립트
- 상품 정보 + 상세페이지 HTML 가져오기
- 이미지 다운로드 및 로컬 저장
- products.json 형식으로 변환
"""

import os
import json
import time
import requests
import bcrypt
import base64
from datetime import datetime
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import shutil

# ============================================
# 설정
# ============================================
CLIENT_ID = "7Q7o2KlytZQOXs8nYVellm"
CLIENT_SECRET = "$2a$04$5/0Wz3hIsHXjjl7fFw9Jae"

BASE_DIR = '/var/www/seoulwatch'
IMAGES_DIR = os.path.join(BASE_DIR, 'images/products')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data/products.json')
BACKUP_FILE = os.path.join(BASE_DIR, 'data/products_backup.json')

API_BASE = "https://api.commerce.naver.com/external"

MAX_WIDTH = 800
JPEG_QUALITY = 80

# ============================================
# 인증 토큰 발급
# ============================================
def get_access_token():
    timestamp = int(time.time() * 1000)
    password = f"{CLIENT_ID}_{timestamp}"
    hashed = bcrypt.hashpw(password.encode('utf-8'), CLIENT_SECRET.encode('utf-8'))
    signature = base64.b64encode(hashed).decode('utf-8')

    response = requests.post(
        f"{API_BASE}/v1/oauth2/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": CLIENT_ID,
            "timestamp": timestamp,
            "client_secret_sign": signature,
            "grant_type": "client_credentials",
            "type": "SELF"
        }
    )

    if response.status_code != 200:
        print(f"토큰 발급 실패: {response.text}")
        return None

    return response.json().get("access_token")

# ============================================
# 상품 목록 조회
# ============================================
def get_product_list(token):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    all_products = []
    page = 0

    while True:
        response = requests.post(
            f"{API_BASE}/v1/products/search",
            headers=headers,
            json={"page": page, "size": 100}
        )

        if response.status_code != 200:
            print(f"상품 목록 조회 실패: {response.status_code}")
            break

        result = response.json()
        contents = result.get("contents", [])

        if not contents:
            break

        for item in contents:
            channel_products = item.get("channelProducts", [])
            if channel_products:
                all_products.append(channel_products[0])

        print(f"  페이지 {page + 1}: {len(contents)}개 조회 (총 {len(all_products)}개)")

        if page + 1 >= result.get("totalPages", 1):
            break

        page += 1
        time.sleep(0.3)

    return all_products

# ============================================
# 상품 상세 조회
# ============================================
def get_product_detail(token, channel_product_no, retry=3):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    for attempt in range(retry):
        response = requests.get(
            f"{API_BASE}/v2/products/channel-products/{channel_product_no}",
            headers=headers
        )

        if response.status_code == 200:
            return response.json().get('originProduct', {})
        elif response.status_code == 429:
            time.sleep(5)
        else:
            break

    return {}

# ============================================
# 이미지 다운로드 및 저장
# ============================================
def download_image(url, save_path):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)

        img.save(save_path, 'JPEG', quality=JPEG_QUALITY, optimize=True)
        return True
    except Exception as e:
        return False

# ============================================
# 카테고리 결정
# ============================================
def get_category(brand_name, product_name, status):
    brand_lower = (brand_name or '').lower()
    name_lower = (product_name or '').lower()

    # 품절/판매중지 상품은 ARCHIVE
    if status in ['OUTOFSTOCK', 'SUSPENSION', 'CLOSE']:
        return ['ARCHIVE'], 'other', 'unisex'

    # 브랜드 결정
    brand = 'OTHER'
    brand_id = 'other'
    if any(k in brand_lower or k in name_lower for k in ['롤렉스', 'rolex']):
        brand = 'ROLEX'
        brand_id = 'rolex'
    elif any(k in brand_lower or k in name_lower for k in ['오메가', 'omega']):
        brand = 'OMEGA'
        brand_id = 'omega'
    elif any(k in brand_lower or k in name_lower for k in ['까르띠에', 'cartier', '카르티에']):
        brand = 'CARTIER'
        brand_id = 'cartier'
    elif any(k in brand_lower or k in name_lower for k in ['파텍', 'patek']):
        brand = 'PATEK'
        brand_id = 'patek'
    elif any(k in brand_lower or k in name_lower for k in ['오데마', 'audemars', 'ap워치']):
        brand = 'AUDEMARS'
        brand_id = 'audemars'
    elif any(k in brand_lower or k in name_lower for k in ['바쉐론', 'vacheron']):
        brand = 'VACHERON'
        brand_id = 'vacheron'
    elif any(k in brand_lower or k in name_lower for k in ['피아제', 'piaget']):
        brand = 'PIAGET'
        brand_id = 'piaget'
    elif any(k in brand_lower or k in name_lower for k in ['태그호이어', 'tag heuer', 'tagheuer']):
        brand = 'TAG HEUER'
        brand_id = 'tagheuer'

    # 성별 결정
    gender = 'unisex'
    if any(k in name_lower for k in ['남성', '맨즈', 'mens', "men's", 'boy', '보이']):
        gender = 'men'
    elif any(k in name_lower for k in ['여성', '레이디', 'lady', 'ladies', "women's", 'womens', '우먼', '걸']):
        gender = 'women'

    # 카테고리 배열 생성
    category = [brand]
    if gender == 'men':
        category.append('MEN')
    elif gender == 'women':
        category.append('WOMEN')

    return category, brand_id, gender

# ============================================
# 상품 변환 및 이미지 다운로드
# ============================================
def process_product(token, product, index, total):
    channel_product_no = product.get('channelProductNo')
    brand_name = product.get('brandName', 'OTHER')
    name = product.get('name', '')
    price = product.get('salePrice', 0)
    status = product.get('statusType', 'SALE')

    # 상세 정보 조회
    detail = get_product_detail(token, channel_product_no)

    # 이미지 URL 수집
    image_urls = []
    if detail.get('images', {}).get('representativeImage', {}).get('url'):
        image_urls.append(detail['images']['representativeImage']['url'])
    for img in detail.get('images', {}).get('optionalImages', []):
        if img.get('url'):
            image_urls.append(img['url'])

    # 이미지가 없으면 목록에서 대표 이미지라도
    if not image_urls and product.get('representativeImage', {}).get('url'):
        image_urls.append(product['representativeImage']['url'])

    # 카테고리 결정
    category, brand_id, gender = get_category(brand_name, name, status)

    # 고유 ID 생성
    product_id = f"{brand_id}-{channel_product_no}"

    # 이미지 다운로드
    local_images = []
    for i, url in enumerate(image_urls):
        filename = f"{product_id}_{i}.jpg"
        save_path = os.path.join(IMAGES_DIR, filename)

        if os.path.exists(save_path) or download_image(url, save_path):
            local_images.append(f"/seoulwatch/images/products/{filename}")

    # 변환된 상품 데이터
    converted = {
        "id": product_id,
        "brand": brand_id.upper(),
        "name": name,
        "nameEn": "",
        "price": price,
        "category": category,
        "gender": gender,
        "image": local_images[0] if local_images else "",
        "images": local_images,
        "sku": str(channel_product_no),
        "descriptionHtml": detail.get('detailContent', '')
    }

    return converted

# ============================================
# 메인 실행
# ============================================
def main():
    print("=" * 60)
    print("네이버 스마트스토어 → products.json 동기화")
    print("=" * 60)

    # 이미지 디렉토리 확인
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # 1. 토큰 발급
    print("\n[1/4] 토큰 발급 중...")
    token = get_access_token()
    if not token:
        print("토큰 발급 실패")
        return
    print("토큰 발급 성공!")

    # 2. 상품 목록 조회
    print("\n[2/4] 상품 목록 조회 중...")
    products = get_product_list(token)
    print(f"총 {len(products)}개 상품 조회됨")

    if not products:
        print("상품이 없습니다")
        return

    # 3. 기존 파일 백업
    if os.path.exists(OUTPUT_FILE):
        print(f"\n[3/4] 기존 파일 백업: {BACKUP_FILE}")
        shutil.copy2(OUTPUT_FILE, BACKUP_FILE)

    # 4. 상품 처리 (상세 조회 + 이미지 다운로드)
    print(f"\n[4/4] 상품 상세 조회 및 이미지 다운로드...")
    converted_products = []
    start_time = time.time()

    for i, product in enumerate(products):
        if (i + 1) % 50 == 0 or i == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining = (len(products) - i - 1) / rate if rate > 0 else 0
            print(f"  [{i+1}/{len(products)}] 처리 중... (남은 시간: {remaining/60:.1f}분)")

        try:
            converted = process_product(token, product, i, len(products))
            converted_products.append(converted)
        except Exception as e:
            print(f"  상품 {product.get('channelProductNo')} 처리 실패: {e}")

        time.sleep(0.5)  # Rate limit

    # 5. 저장
    output_data = {"products": converted_products}

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    print(f"\n완료!")
    print(f"  - 처리된 상품: {len(converted_products)}개")
    print(f"  - 소요 시간: {elapsed/60:.1f}분")
    print(f"  - 저장 위치: {OUTPUT_FILE}")
    print(f"  - 백업 위치: {BACKUP_FILE}")

if __name__ == "__main__":
    main()
