#!/bin/bash
# ============================================================================
# CORS DEBUGGING SCRIPT
# Save this as: /root/bond_platform/debug_cors.sh
# Run: bash debug_cors.sh
# ============================================================================

echo "========================================="
echo "CORS CONFIGURATION DEBUGGING"
echo "========================================="
echo ""

# 1. Check if server is running
echo "1. Checking if Django server is running..."
if pgrep -f "manage.py runserver" > /dev/null; then
    echo "✓ Django server is running"
    ps aux | grep "manage.py runserver" | grep -v grep
else
    echo "✗ Django server is NOT running!"
    echo "Start it with: nohup python manage.py runserver 0.0.0.0:8000 --settings=config.settings.local &"
fi
echo ""

# 2. Check current CORS settings in files
echo "2. Checking CORS settings in base.py..."
cd /root/bond_platform/Backend
if grep -n "CORS_ALLOW_ALL_ORIGINS" config/settings/base.py 2>/dev/null; then
    echo "⚠ WARNING: CORS_ALLOW_ALL_ORIGINS found in base.py (should be removed!)"
else
    echo "✓ CORS_ALLOW_ALL_ORIGINS not in base.py (good)"
fi
echo ""

echo "3. Checking CORS settings in local.py..."
grep -n "CORS_ALLOW" config/settings/local.py 2>/dev/null
echo ""

# 3. Test Django settings
echo "4. Testing actual Django settings..."
python manage.py shell --settings=config.settings.local << 'PYEOF'
from django.conf import settings
import sys

print("=" * 60)
print("CURRENT DJANGO SETTINGS:")
print("=" * 60)

# Check CORS settings
try:
    print(f"CORS_ALLOW_ALL_ORIGINS: {settings.CORS_ALLOW_ALL_ORIGINS}")
except AttributeError:
    print("CORS_ALLOW_ALL_ORIGINS: Not set")

try:
    print(f"CORS_ALLOW_CREDENTIALS: {settings.CORS_ALLOW_CREDENTIALS}")
except AttributeError:
    print("⚠ CORS_ALLOW_CREDENTIALS: Not set (PROBLEM!)")

try:
    origins = settings.CORS_ALLOWED_ORIGINS
    print(f"CORS_ALLOWED_ORIGINS: {origins}")
    if not origins:
        print("⚠ CORS_ALLOWED_ORIGINS is empty (PROBLEM!)")
except AttributeError:
    print("⚠ CORS_ALLOWED_ORIGINS: Not set (PROBLEM!)")

# Check JWT cookie settings
print("\nJWT COOKIE SETTINGS:")
print(f"AUTH_COOKIE_SECURE: {settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE')}")
print(f"AUTH_COOKIE_SAMESITE: {settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE')}")
print(f"AUTH_COOKIE: {settings.SIMPLE_JWT.get('AUTH_COOKIE')}")

# Check if corsheaders is in INSTALLED_APPS
print("\nCORS MIDDLEWARE CHECK:")
if 'corsheaders' in settings.INSTALLED_APPS:
    print("✓ corsheaders in INSTALLED_APPS")
else:
    print("✗ corsheaders NOT in INSTALLED_APPS (PROBLEM!)")

if 'corsheaders.middleware.CorsMiddleware' in settings.MIDDLEWARE:
    print("✓ CorsMiddleware in MIDDLEWARE")
    # Check position
    idx = settings.MIDDLEWARE.index('corsheaders.middleware.CorsMiddleware')
    common_idx = settings.MIDDLEWARE.index('django.middleware.common.CommonMiddleware')
    if idx < common_idx:
        print(f"✓ CorsMiddleware is before CommonMiddleware (position {idx})")
    else:
        print(f"⚠ CorsMiddleware is AFTER CommonMiddleware (PROBLEM!)")
else:
    print("✗ CorsMiddleware NOT in MIDDLEWARE (PROBLEM!)")

print("=" * 60)
PYEOF

echo ""

# 4. Test actual CORS headers with curl
echo "5. Testing CORS headers with curl..."
echo "Testing OPTIONS request (preflight)..."

BACKEND_URL="http://93.127.206.37:8000"
FRONTEND_URL="http://93.127.206.37:3040"

# Test a common endpoint
curl -s -I \
  -H "Origin: ${FRONTEND_URL}" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS \
  "${BACKEND_URL}/api/auth/register/" 2>&1 | grep -i "access-control"

echo ""
echo "Testing GET request..."
curl -s -I \
  -H "Origin: ${FRONTEND_URL}" \
  "${BACKEND_URL}/api/auth/register/" 2>&1 | grep -i "access-control"

echo ""

# 5. Check server logs for CORS errors
echo "6. Checking recent server logs for CORS/403 errors..."
if [ -f "server.log" ]; then
    echo "Last 20 lines of server.log:"
    tail -20 server.log | grep -E "CORS|403|Origin|Bad Host|WARNING"
else
    echo "⚠ server.log not found"
fi

echo ""
echo "========================================="
echo "DEBUGGING COMPLETE"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Review the output above for any ✗ or ⚠ warnings"
echo "2. Check if CORS headers are present in curl output"
echo "3. If headers missing, verify django-cors-headers is installed:"
echo "   pip show django-cors-headers"
echo ""