"""
Seoul Watch Admin API
Flask backend for managing products
"""
import os
import json
import uuid
import shutil
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
from PIL import Image

import config

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
CORS(app, supports_credentials=True)


# ============================================================================
# Utility Functions
# ============================================================================

def load_products():
    """Load products from JSON file"""
    try:
        with open(config.PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('products', [])
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def save_products(products):
    """Save products to JSON file"""
    # Create backup
    if os.path.exists(config.PRODUCTS_FILE):
        backup_path = config.PRODUCTS_FILE.replace('.json', '_backup.json')
        shutil.copy2(config.PRODUCTS_FILE, backup_path)

    with open(config.PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'products': products}, f, ensure_ascii=False, indent=2)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def generate_product_id(brand, sku):
    """Generate product ID from brand and SKU"""
    brand_slug = brand.lower().replace(' ', '-')
    return f"{brand_slug}-{sku}"


# ============================================================================
# Authentication Decorator
# ============================================================================

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated


# ============================================================================
# Auth Routes
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.get_json()

    if not data or 'password' not in data:
        return jsonify({'error': 'Password is required'}), 400

    password = data['password']

    # Simple password check
    if password != config.ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 401

    # Generate JWT token
    token = jwt.encode({
        'exp': datetime.utcnow() + timedelta(hours=config.JWT_EXPIRY_HOURS),
        'iat': datetime.utcnow()
    }, config.SECRET_KEY, algorithm='HS256')

    return jsonify({
        'token': token,
        'expiresIn': config.JWT_EXPIRY_HOURS * 3600
    })


@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_token():
    """Verify token endpoint"""
    return jsonify({'valid': True})


# ============================================================================
# Products Routes
# ============================================================================

@app.route('/api/products', methods=['GET'])
@token_required
def get_products():
    """Get all products with optional filtering"""
    products = load_products()

    # Search filter
    search = request.args.get('search', '').strip().lower()
    if search:
        products = [p for p in products if
                    search in p.get('name', '').lower() or
                    search in p.get('nameEn', '').lower() or
                    search in p.get('brand', '').lower() or
                    search in p.get('sku', '').lower()]

    # Brand filter
    brand = request.args.get('brand', '').strip()
    if brand and brand != 'all':
        products = [p for p in products if p.get('brand', '').lower() == brand.lower()]

    # Status filter
    status = request.args.get('status', '').strip()
    if status and status != 'all':
        products = [p for p in products if p.get('status', 'active') == status]

    # Category filter
    category = request.args.get('category', '').strip()
    if category and category != 'all':
        products = [p for p in products if category in p.get('category', [])]

    # Sorting
    sort = request.args.get('sort', 'newest')
    if sort == 'newest':
        products = sorted(products, key=lambda x: x.get('id', ''), reverse=True)
    elif sort == 'oldest':
        products = sorted(products, key=lambda x: x.get('id', ''))
    elif sort == 'price_high':
        products = sorted(products, key=lambda x: x.get('price', 0), reverse=True)
    elif sort == 'price_low':
        products = sorted(products, key=lambda x: x.get('price', 0))
    elif sort == 'name':
        products = sorted(products, key=lambda x: x.get('name', ''))

    # Pagination
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    total = len(products)

    start = (page - 1) * limit
    end = start + limit
    paginated = products[start:end]

    return jsonify({
        'products': paginated,
        'total': total,
        'page': page,
        'limit': limit,
        'totalPages': (total + limit - 1) // limit
    })


@app.route('/api/products/<product_id>', methods=['GET'])
@token_required
def get_product(product_id):
    """Get single product by ID"""
    products = load_products()

    for product in products:
        if product.get('id') == product_id:
            return jsonify(product)

    return jsonify({'error': 'Product not found'}), 404


@app.route('/api/products', methods=['POST'])
@token_required
def create_product():
    """Create new product"""
    data = request.get_json()

    # Validate required fields
    required = ['brand', 'name', 'price', 'sku']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    products = load_products()

    # Generate ID
    product_id = generate_product_id(data['brand'], data['sku'])

    # Check if ID already exists
    for p in products:
        if p.get('id') == product_id:
            return jsonify({'error': 'Product with this SKU already exists'}), 400

    # Create product object
    product = {
        'id': product_id,
        'brand': data['brand'].upper(),
        'name': data['name'],
        'nameEn': data.get('nameEn', ''),
        'price': int(data['price']),
        'category': data.get('category', []),
        'movement': data.get('movement', 'automatic'),
        'image': data.get('image', ''),
        'images': data.get('images', []),
        'sku': data['sku'],
        'description': data.get('description', ''),
        'descriptionHtml': data.get('descriptionHtml', ''),
        'status': data.get('status', 'active'),
        'createdAt': datetime.utcnow().isoformat()
    }

    # Set main image from images array if not set
    if not product['image'] and product['images']:
        product['image'] = product['images'][0]

    products.insert(0, product)  # Add to beginning
    save_products(products)

    return jsonify(product), 201


@app.route('/api/products/<product_id>', methods=['PUT'])
@token_required
def update_product(product_id):
    """Update existing product"""
    data = request.get_json()
    products = load_products()

    for i, product in enumerate(products):
        if product.get('id') == product_id:
            # Update fields
            product['brand'] = data.get('brand', product['brand']).upper()
            product['name'] = data.get('name', product['name'])
            product['nameEn'] = data.get('nameEn', product.get('nameEn', ''))
            product['price'] = int(data.get('price', product['price']))
            product['category'] = data.get('category', product.get('category', []))
            product['movement'] = data.get('movement', product.get('movement', 'automatic'))
            product['image'] = data.get('image', product.get('image', ''))
            product['images'] = data.get('images', product.get('images', []))
            product['description'] = data.get('description', product.get('description', ''))
            product['descriptionHtml'] = data.get('descriptionHtml', product.get('descriptionHtml', ''))
            product['status'] = data.get('status', product.get('status', 'active'))
            product['updatedAt'] = datetime.utcnow().isoformat()

            # Update main image from images array if not set
            if not product['image'] and product['images']:
                product['image'] = product['images'][0]

            # Handle SKU change (regenerate ID)
            new_sku = data.get('sku', product.get('sku'))
            if new_sku != product.get('sku'):
                new_id = generate_product_id(product['brand'], new_sku)
                # Check if new ID already exists
                for p in products:
                    if p.get('id') == new_id and p.get('id') != product_id:
                        return jsonify({'error': 'Product with this SKU already exists'}), 400
                product['id'] = new_id
                product['sku'] = new_sku

            products[i] = product
            save_products(products)

            return jsonify(product)

    return jsonify({'error': 'Product not found'}), 404


@app.route('/api/products/<product_id>', methods=['DELETE'])
@token_required
def delete_product(product_id):
    """Delete product"""
    products = load_products()

    for i, product in enumerate(products):
        if product.get('id') == product_id:
            deleted = products.pop(i)
            save_products(products)
            return jsonify({'message': 'Product deleted', 'product': deleted})

    return jsonify({'error': 'Product not found'}), 404


@app.route('/api/products/<product_id>/status', methods=['PATCH'])
@token_required
def update_product_status(product_id):
    """Update product status (active/archive)"""
    data = request.get_json()
    new_status = data.get('status')

    if new_status not in ['active', 'archive']:
        return jsonify({'error': 'Invalid status'}), 400

    products = load_products()

    for i, product in enumerate(products):
        if product.get('id') == product_id:
            product['status'] = new_status
            product['updatedAt'] = datetime.utcnow().isoformat()
            products[i] = product
            save_products(products)
            return jsonify(product)

    return jsonify({'error': 'Product not found'}), 404


@app.route('/api/products/bulk-delete', methods=['POST'])
@token_required
def bulk_delete_products():
    """Bulk delete products"""
    data = request.get_json()
    ids = data.get('ids', [])

    if not ids:
        return jsonify({'error': 'No product IDs provided'}), 400

    products = load_products()
    deleted = []
    remaining = []

    for product in products:
        if product.get('id') in ids:
            deleted.append(product)
        else:
            remaining.append(product)

    save_products(remaining)

    return jsonify({
        'message': f'{len(deleted)} products deleted',
        'deleted': len(deleted)
    })


@app.route('/api/products/bulk-status', methods=['POST'])
@token_required
def bulk_update_status():
    """Bulk update product status"""
    data = request.get_json()
    ids = data.get('ids', [])
    new_status = data.get('status')

    if not ids:
        return jsonify({'error': 'No product IDs provided'}), 400

    if new_status not in ['active', 'archive']:
        return jsonify({'error': 'Invalid status'}), 400

    products = load_products()
    updated = 0

    for product in products:
        if product.get('id') in ids:
            product['status'] = new_status
            product['updatedAt'] = datetime.utcnow().isoformat()
            updated += 1

    save_products(products)

    return jsonify({
        'message': f'{updated} products updated',
        'updated': updated
    })


# ============================================================================
# Image Routes
# ============================================================================

@app.route('/api/images/upload', methods=['POST'])
@token_required
def upload_image():
    """Upload product image"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Get brand and sku from form data
    brand = request.form.get('brand', 'unknown').lower().replace(' ', '-')
    sku = request.form.get('sku', str(uuid.uuid4())[:8])
    index = request.form.get('index', '0')

    # Generate filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{brand}-{sku}_{index}.{ext}"
    filepath = os.path.join(config.IMAGES_DIR, filename)

    # Ensure directory exists
    os.makedirs(config.IMAGES_DIR, exist_ok=True)

    # Save and optimize image
    try:
        img = Image.open(file)

        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Resize if too large (max 2000px on longest side)
        max_size = 2000
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Save as JPEG with optimization
        img.save(filepath, 'JPEG', quality=85, optimize=True)

    except Exception as e:
        return jsonify({'error': f'Failed to process image: {str(e)}'}), 500

    # Return the path
    image_url = f"/seoulwatch/images/products/{filename}"

    return jsonify({
        'filename': filename,
        'url': image_url,
        'path': filepath
    })


@app.route('/api/images/<filename>', methods=['DELETE'])
@token_required
def delete_image(filename):
    """Delete product image"""
    filepath = os.path.join(config.IMAGES_DIR, secure_filename(filename))

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'message': 'Image deleted'})

    return jsonify({'error': 'Image not found'}), 404


# ============================================================================
# Stats Routes
# ============================================================================

@app.route('/api/stats', methods=['GET'])
@token_required
def get_stats():
    """Get dashboard statistics"""
    products = load_products()

    total = len(products)
    active = sum(1 for p in products if p.get('status', 'active') == 'active')
    archive = sum(1 for p in products if p.get('status') == 'archive')

    # Brand distribution
    brands = {}
    for p in products:
        brand = p.get('brand', 'Unknown')
        brands[brand] = brands.get(brand, 0) + 1

    # Sort brands by count
    brands_sorted = sorted(brands.items(), key=lambda x: x[1], reverse=True)

    # Category distribution
    categories = {}
    for p in products:
        for cat in p.get('category', []):
            categories[cat] = categories.get(cat, 0) + 1

    # Recent products (last 5)
    recent = products[:5]

    return jsonify({
        'total': total,
        'active': active,
        'archive': archive,
        'brands': dict(brands_sorted[:10]),  # Top 10 brands
        'categories': categories,
        'recent': recent
    })


# ============================================================================
# Brands Route
# ============================================================================

@app.route('/api/brands', methods=['GET'])
@token_required
def get_brands():
    """Get list of all brands"""
    products = load_products()

    brands = set()
    for p in products:
        brand = p.get('brand', '').strip()
        if brand:
            brands.add(brand)

    return jsonify(sorted(list(brands)))


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.IMAGES_DIR, exist_ok=True)

    print(f"Starting Seoul Watch Admin API...")
    print(f"Data directory: {config.DATA_DIR}")
    print(f"Images directory: {config.IMAGES_DIR}")

    # Run in production mode, bind to localhost only (nginx proxy handles external access)
    app.run(host='127.0.0.1', port=5000, debug=False)
