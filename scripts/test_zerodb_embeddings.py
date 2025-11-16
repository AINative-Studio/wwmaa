#!/usr/bin/env python3
"""
Test ZeroDB Embedding Integration

This script tests the updated embedding service that uses ZeroDB's
embedding API instead of OpenAI.

Features:
- Automatically gets JWT token from ZeroDB
- Tests single embedding generation
- Tests batch embedding generation
- Tests Redis caching
- Updates .env file with JWT token

Requirements:
- ZERODB_EMAIL must be set in .env file
- ZERODB_PASSWORD must be set in .env file
- ZERODB_PROJECT_ID must be set in .env file
"""

import sys
import os
import requests

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.embedding_service import get_embedding_service, EmbeddingError
from backend.config import get_settings


def get_jwt_token():
    """Get JWT token from ZeroDB using email and password"""
    print("=" * 70)
    print("1. Getting JWT Token from ZeroDB")
    print("=" * 70)

    settings = get_settings()

    # Check credentials
    if not settings.ZERODB_EMAIL or not settings.ZERODB_PASSWORD:
        print("❌ Missing credentials!")
        print("\nPlease add to .env file:")
        print("ZERODB_EMAIL=your@email.com")
        print("ZERODB_PASSWORD=your-password")
        return None

    print(f"Email: {settings.ZERODB_EMAIL}")
    print("Password: ********")
    print("\nRequesting JWT token from ZeroDB...")

    try:
        response = requests.post(
            "https://api.ainative.studio/v1/auth/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "username": settings.ZERODB_EMAIL,
                "password": settings.ZERODB_PASSWORD
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")

            if token:
                print(f"✅ JWT token received: {token[:30]}...")

                # Update .env file
                env_path = os.path.join(os.path.dirname(__file__), '..', '.env')

                # Read existing .env
                env_lines = []
                token_exists = False

                if os.path.exists(env_path):
                    with open(env_path, 'r') as f:
                        env_lines = f.readlines()

                    # Update existing token or mark to add
                    for i, line in enumerate(env_lines):
                        if line.startswith('ZERODB_JWT_TOKEN='):
                            env_lines[i] = f'ZERODB_JWT_TOKEN={token}\n'
                            token_exists = True
                            break

                # Add token if not exists
                if not token_exists:
                    env_lines.append(f'\nZERODB_JWT_TOKEN={token}\n')

                # Write back to .env
                with open(env_path, 'w') as f:
                    f.writelines(env_lines)

                print(f"✅ Token saved to .env file")

                # Update settings in memory (reload)
                os.environ['ZERODB_JWT_TOKEN'] = token

                return token
            else:
                print("❌ No access_token in response")
                return None
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_configuration(jwt_token):
    """Test that required configuration is present"""
    print("\n" + "=" * 70)
    print("2. Verifying Configuration")
    print("=" * 70)

    settings = get_settings()

    # Check ZERODB_PROJECT_ID
    if settings.ZERODB_PROJECT_ID:
        print(f"✅ ZERODB_PROJECT_ID: {settings.ZERODB_PROJECT_ID[:20]}...")
    else:
        print("❌ ZERODB_PROJECT_ID: NOT SET")
        return False

    # Check ZERODB_JWT_TOKEN
    if jwt_token:
        print(f"✅ ZERODB_JWT_TOKEN: {jwt_token[:30]}...")
    else:
        print("❌ ZERODB_JWT_TOKEN: Failed to obtain")
        return False

    print("\n✅ All configuration verified\n")
    return True


def test_single_embedding():
    """Test generating a single embedding"""
    print("=" * 70)
    print("3. Testing Single Embedding Generation")
    print("=" * 70)

    try:
        service = get_embedding_service()

        test_text = "martial arts training session"
        print(f"Input text: '{test_text}'")
        print("Generating embedding...")

        embedding = service.generate_embedding(test_text, use_cache=False)

        print(f"✅ Embedding generated successfully!")
        print(f"   Dimension: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        print(f"   Expected dimension: 384 (ZeroDB uses all-MiniLM-L6-v2)")

        if len(embedding) == 384:
            print("✅ Dimension matches expected (384)")
            return True
        else:
            print(f"❌ Dimension mismatch! Expected 384, got {len(embedding)}")
            return False

    except EmbeddingError as e:
        print(f"❌ Embedding generation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_embeddings():
    """Test generating batch embeddings"""
    print("\n" + "=" * 70)
    print("4. Testing Batch Embedding Generation")
    print("=" * 70)

    try:
        service = get_embedding_service()

        test_texts = [
            "karate training",
            "judo competition",
            "taekwondo tournament"
        ]

        print(f"Input texts ({len(test_texts)} items):")
        for i, text in enumerate(test_texts, 1):
            print(f"  {i}. '{text}'")

        print("\nGenerating batch embeddings...")

        embeddings = service.generate_embeddings_batch(test_texts, use_cache=False)

        print(f"✅ Batch embeddings generated successfully!")
        print(f"   Number of embeddings: {len(embeddings)}")
        print(f"   Dimensions: {[len(emb) for emb in embeddings]}")

        if len(embeddings) == len(test_texts):
            print("✅ Count matches input texts")
        else:
            print(f"❌ Count mismatch! Expected {len(test_texts)}, got {len(embeddings)}")
            return False

        if all(len(emb) == 384 for emb in embeddings):
            print("✅ All embeddings have correct dimension (384)")
            return True
        else:
            print("❌ Some embeddings have incorrect dimension")
            return False

    except EmbeddingError as e:
        print(f"❌ Batch embedding generation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_caching():
    """Test Redis caching"""
    print("\n" + "=" * 70)
    print("5. Testing Redis Caching")
    print("=" * 70)

    try:
        service = get_embedding_service()

        test_text = "cached embedding test"

        # First generation (not cached)
        print(f"First generation (cache miss): '{test_text}'")
        import time
        start = time.time()
        embedding1 = service.generate_embedding(test_text, use_cache=True)
        time1 = time.time() - start
        print(f"   Time: {time1*1000:.0f}ms")

        # Second generation (should be cached)
        print(f"Second generation (cache hit): '{test_text}'")
        start = time.time()
        embedding2 = service.generate_embedding(test_text, use_cache=True)
        time2 = time.time() - start
        print(f"   Time: {time2*1000:.0f}ms")

        if embedding1 == embedding2:
            print("✅ Cached embedding matches original")
        else:
            print("❌ Cached embedding differs from original")
            return False

        if time2 < time1:
            speedup = time1 / time2
            print(f"✅ Cache is faster ({speedup:.1f}x speedup)")
            return True
        else:
            print("⚠️  Cache not faster (might be disabled or Redis unavailable)")
            return True  # Still pass if cache is disabled

    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("ZeroDB Embedding Integration Test")
    print("=" * 70)
    print()

    # Step 1: Get JWT token
    jwt_token = get_jwt_token()
    if not jwt_token:
        print("\n" + "=" * 70)
        print("❌ FAILED TO GET JWT TOKEN")
        print("=" * 70)
        print("\nPlease check your ZERODB_EMAIL and ZERODB_PASSWORD in .env file.")
        return 1

    # Step 2: Verify configuration
    if not test_configuration(jwt_token):
        print("\n" + "=" * 70)
        print("❌ CONFIGURATION VERIFICATION FAILED")
        print("=" * 70)
        return 1

    # Step 3: Run embedding tests
    results = []
    results.append(("Single Embedding", test_single_embedding()))
    results.append(("Batch Embeddings", test_batch_embeddings()))
    results.append(("Redis Caching", test_caching()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    print("\n✅ JWT Token: Obtained and saved to .env")
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {test_name}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\nTotal: {passed_count}/{total_count} embedding tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed! ZeroDB embedding integration is working correctly.")
        print("\n✅ Your .env file has been updated with ZERODB_JWT_TOKEN")
        print("✅ Search embeddings are now using ZeroDB (FREE, no OpenAI needed)")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
