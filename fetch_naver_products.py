#!/usr/bin/env python3
"""
네이버 스마트스토어 커머스 API를 사용하여 상품 정보를 가져오는 스크립트
"""

import os
import json
import time
import requests
import bcrypt
import base64
from datetime import datetime

# ============================================
# 설정
# ============================================
CLIENT_ID = "7Q7o2KlytZQOXs8nYVellm"
CLIENT_SECRET = "$2a$04$5/0Wz3hIsHXjjl7fFw9Jae"

BASE_DIR = '/var/www/seoulwatch'
OUTPUT_FILE = os.path.join(BASE_DIR, 'data/naver_products.json')

# API 엔드포인트
API_BASE = "https://api.commerce.naver.com/external"
TOKEN_URL = f"{API_BASE}/v1/oauth2/token"

# ============================================
# 인증 토큰 발급
# ============================================
def get_access_token():
    """네이버 커머스 API 인증 토큰 발급"""
    timestamp = int(time.time() * 1000)

    # bcrypt 서명 생성
    password = f"{CLIENT_ID}_{timestamp}"

    # CLIENT_SECRET이 이미 bcrypt salt 형식이므로 그대로 사용
    hashed = bcrypt.hashpw(password.encode('utf-8'), CLIENT_SECRET.encode('utf-8'))
    signature = base64.b64encode(hashed).decode('utf-8')

    # 토큰 요청
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": CLIENT_ID,
        "timestamp": timestamp,
        "client_secret_sign": signature,
        "grant_type": "client_credentials",
        "type": "SELF"
    }

    print("토큰 발급 요청 중...")
    response = requests.post(TOKEN_URL, headers=headers, data=data)

    if response.status_code != 200:
        print(f"토큰 발급 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return None

    result = response.json()
    print("토큰 발급 성공!")
    return result.get("access_token")

# ============================================
# 상품 목록 조회
# ============================================
def get_product_list(token):
    """전체 상품 목록 조회 (POST /v1/products/search)"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    all_products = []
    page = 0
    page_size = 100

    while True:
        # 상품 목록 조회 API (v1 POST)
        url = f"{API_BASE}/v1/products/search"
        body = {
            "page": page,
            "size": page_size
        }

        print(f"상품 목록 조회 중... (페이지 {page + 1})")
        response = requests.post(url, headers=headers, json=body)

        if response.status_code != 200:
            print(f"상품 목록 조회 실패: {response.status_code}")
            print(f"응답: {response.text}")
            break

        result = response.json()
        contents = result.get("contents", [])

        if not contents:
            break

        # channelProducts 배열에서 실제 상품 정보 추출
        for item in contents:
            channel_products = item.get("channelProducts", [])
            if channel_products:
                # 첫 번째 채널 상품 사용 (보통 스마트스토어)
                all_products.append(channel_products[0])

        print(f"  - {len(contents)}개 상품 조회됨 (총 {len(all_products)}개)")

        # 다음 페이지가 없으면 종료
        total_pages = result.get("totalPages", 1)
        if page + 1 >= total_pages:
            break

        page += 1
        time.sleep(0.5)  # Rate limit 고려

    return all_products

# ============================================
# 상품 상세 조회 (상세페이지 HTML 포함)
# ============================================
def get_product_detail(token, channel_product_no):
    """개별 상품 상세 정보 조회 - originProduct에서 detailContent 추출"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{API_BASE}/v2/products/channel-products/{channel_product_no}"
    response = requests.get(url, headers=headers)

    if response.status_code == 429:
        # Rate limit - 잠시 대기 후 재시도
        print(f"  Rate limit 도달, 5초 대기...")
        time.sleep(5)
        response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"  상품 {channel_product_no} 상세 조회 실패: {response.status_code}")
        return None

    result = response.json()
    # originProduct에서 detailContent와 images 추출
    return result.get('originProduct', {})

# ============================================
# 데이터 변환 (현재 사이트 형식으로)
# ============================================
def convert_to_site_format(naver_product, detail=None):
    """네이버 상품 데이터를 사이트 형식으로 변환"""

    # 기본 정보
    channel_product_no = naver_product.get('channelProductNo', '')
    product_id = f"naver-{channel_product_no}"
    name = naver_product.get('name', '')
    price = naver_product.get('salePrice', 0)

    # 이미지 처리 - 목록 조회에서는 representativeImage만 있음
    images = []
    rep_image = naver_product.get('representativeImage', {})
    if rep_image and rep_image.get('url'):
        images.append(rep_image['url'])

    # 상세 조회에서 추가 이미지 가져오기
    if detail:
        detail_images = detail.get('images', {})
        if detail_images.get('representativeImage', {}).get('url'):
            if detail_images['representativeImage']['url'] not in images:
                images.insert(0, detail_images['representativeImage']['url'])
        for img in detail_images.get('optionalImages', []):
            if img.get('url') and img['url'] not in images:
                images.append(img['url'])

    # 브랜드 - API 응답에서 직접 가져오기
    brand = naver_product.get('brandName', '')
    if not brand:
        # 상품명에서 추출
        brand = "OTHER"
        brand_keywords = {
            'ROLEX': ['롤렉스', 'rolex'],
            'OMEGA': ['오메가', 'omega'],
            'CARTIER': ['까르띠에', 'cartier', '카르티에'],
            'TAG HEUER': ['태그호이어', 'tag heuer'],
            'BREITLING': ['브라이틀링', 'breitling'],
            'IWC': ['iwc'],
            'PANERAI': ['파네라이', 'panerai'],
            'TUDOR': ['튜더', 'tudor'],
            'PIAGET': ['피아제', 'piaget'],
            'CORUM': ['코럼', 'corum'],
            'PATEK PHILIPPE': ['파텍필립', 'patek'],
            'AUDEMARS PIGUET': ['오데마피게', 'audemars'],
            'JAEGER-LECOULTRE': ['예거르쿨트르', 'jaeger'],
            'VACHERON CONSTANTIN': ['바쉐론콘스탄틴', 'vacheron'],
        }
        name_lower = name.lower()
        for b, keywords in brand_keywords.items():
            if any(k in name_lower for k in keywords):
                brand = b
                break

    # 카테고리 추출 (브랜드 기반)
    category = ['all']
    brand_lower = brand.lower()
    if 'rolex' in brand_lower or '롤렉스' in brand_lower:
        category.append('rolex')
    elif 'omega' in brand_lower or '오메가' in brand_lower:
        category.append('omega')
    elif 'cartier' in brand_lower or '까르띠에' in brand_lower:
        category.append('cartier')
    elif 'tag' in brand_lower or '태그' in brand_lower:
        category.append('tagheuer')
    else:
        category.append('other')

    # 상세 HTML (상세 조회 결과에서)
    description_html = ""
    if detail:
        description_html = detail.get('detailContent', '')

    # 상태 (SALE, OUTOFSTOCK, SUSPENSION 등)
    status = naver_product.get('statusType', 'SALE')

    return {
        "id": product_id,
        "brand": brand.upper() if brand else "OTHER",
        "name": name,
        "nameEn": "",
        "price": price,
        "category": category,
        "movement": "automatic",
        "image": images[0] if images else "",
        "images": images,
        "sku": str(channel_product_no),
        "descriptionHtml": description_html,
        "originProductNo": naver_product.get('originProductNo'),
        "channelProductNo": channel_product_no,
        "status": status
    }

# ============================================
# 메인 실행
# ============================================
def main():
    print("=" * 50)
    print("네이버 스마트스토어 상품 가져오기")
    print("=" * 50)

    # 1. 토큰 발급
    token = get_access_token()
    if not token:
        print("토큰 발급 실패. 종료합니다.")
        return

    # 2. 상품 목록 조회
    print("\n상품 목록 조회 중...")
    products = get_product_list(token)
    print(f"\n총 {len(products)}개 상품 조회됨")

    if not products:
        print("상품이 없습니다. 종료합니다.")
        return

    # 3. 각 상품 상세 조회 및 변환
    print("\n상품 상세 정보 조회 중...")
    converted_products = []

    for i, product in enumerate(products):
        channel_product_no = product.get('channelProductNo')

        if (i + 1) % 50 == 0 or i == 0:
            print(f"[{i+1}/{len(products)}] 상품 {channel_product_no} 상세 조회 중...")

        # 상세 정보 조회
        detail = get_product_detail(token, channel_product_no)

        # 변환
        converted = convert_to_site_format(product, detail)
        converted_products.append(converted)

        # Rate limit 대응 - 0.5초 간격
        time.sleep(0.5)

    # 4. 저장
    output_data = {
        "products": converted_products,
        "fetchedAt": datetime.now().isoformat(),
        "totalCount": len(converted_products)
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n완료! {OUTPUT_FILE}에 저장되었습니다.")
    print(f"총 {len(converted_products)}개 상품")

if __name__ == "__main__":
    main()
