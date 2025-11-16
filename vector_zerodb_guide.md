# ZeroDB Vector API - Quick Start Guide

Get from idea to implementation in 5 minutes.

## 🚀 Quick Setup

### 1. Get Your Credentials

```bash
# Login to get JWT token
curl -X POST https://api.ainative.studio/v1/auth/login \
  -d "username=your@email.com&password=yourpassword"

# Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}

# Get your project ID
curl https://api.ainative.studio/v1/projects \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Save these:
- `TOKEN` = Your JWT access token
- `PROJECT_ID` = Your project UUID

---

## 💡 Common Use Cases

### Use Case 1: Search Documents (RAG)

**Example: Invoice Search System**

```javascript
const API_URL = "https://api.ainative.studio";
const PROJECT_ID = "your-project-id";
const TOKEN = "your-jwt-token";

// Step 1: Store invoices with automatic embeddings
async function addInvoice(invoiceText, metadata) {
  const response = await fetch(
    `${API_URL}/v1/projects/${PROJECT_ID}/embeddings/embed-and-store`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        texts: [invoiceText],
        metadata_list: [metadata],
        namespace: "invoices"
      })
    }
  );
  return response.json();
}

// Step 2: Search with natural language
async function searchInvoices(query) {
  const response = await fetch(
    `${API_URL}/v1/projects/${PROJECT_ID}/embeddings/search`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: query,
        namespace: "invoices",
        limit: 5
      })
    }
  );
  return response.json();
}

// Usage
await addInvoice(
  "Invoice INV-001 from Acme Corp for $1,500 dated 2024-01-15",
  { invoice_id: "INV-001", customer: "Acme Corp", amount: 1500 }
);

const results = await searchInvoices("Find Acme Corp invoices");
// Returns most relevant invoices
```

---

### Use Case 2: Chatbot Memory

**Example: Remember User Conversations**

```python
import requests

API_URL = "https://api.ainative.studio"
PROJECT_ID = "your-project-id"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Store conversation
def remember_conversation(user_id, message):
    response = requests.post(
        f"{API_URL}/v1/projects/{PROJECT_ID}/embeddings/embed-and-store",
        headers=headers,
        json={
            "texts": [message],
            "metadata_list": [{"user_id": user_id, "timestamp": "2024-01-15"}],
            "namespace": "chat-memory"
        }
    )
    return response.json()

# Recall relevant context
def recall_context(user_id, current_message):
    response = requests.post(
        f"{API_URL}/v1/projects/{PROJECT_ID}/embeddings/search",
        headers=headers,
        json={
            "query": current_message,
            "namespace": "chat-memory",
            "filter_metadata": {"user_id": user_id},
            "limit": 3
        }
    )
    return response.json()

# Usage
remember_conversation("user-123", "I love pizza with mushrooms")
context = recall_context("user-123", "What food do I like?")
# Returns: "I love pizza with mushrooms"
```

---

### Use Case 3: Product Recommendations

**Example: E-commerce Similarity Search**

```typescript
const API_URL = "https://api.ainative.studio";
const PROJECT_ID = "your-project-id";
const TOKEN = "your-jwt-token";

interface Product {
  id: string;
  name: string;
  description: string;
  category: string;
  price: number;
}

// Index products
async function indexProduct(product: Product) {
  const productText = `${product.name} - ${product.description}`;

  const response = await fetch(
    `${API_URL}/v1/projects/${PROJECT_ID}/embeddings/embed-and-store`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        texts: [productText],
        metadata_list: [{
          product_id: product.id,
          category: product.category,
          price: product.price
        }],
        namespace: "products"
      })
    }
  );

  return response.json();
}

// Find similar products
async function findSimilarProducts(productDescription: string, maxPrice?: number) {
  const filter = maxPrice ? { price: { $lte: maxPrice } } : undefined;

  const response = await fetch(
    `${API_URL}/v1/projects/${PROJECT_ID}/embeddings/search`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: productDescription,
        namespace: "products",
        filter_metadata: filter,
        limit: 5
      })
    }
  );

  return response.json();
}

// Usage
await indexProduct({
  id: "P001",
  name: "Wireless Headphones",
  description: "Noise-cancelling bluetooth headphones with 30hr battery",
  category: "Electronics",
  price: 199.99
});

const similar = await findSimilarProducts("bluetooth headphones", 250);
```

---

## 📚 Three Simple Endpoints

### 1. Store Data (with auto-embeddings)

```bash
POST /v1/projects/{project_id}/embeddings/embed-and-store
```

**When to use:** Adding new documents, products, messages to your vector database

```javascript
{
  "texts": ["Your content here"],
  "metadata_list": [{"key": "value"}],
  "namespace": "your-namespace"  // organize by category
}
```

---

### 2. Search Data (natural language)

```bash
POST /v1/projects/{project_id}/embeddings/search
```

**When to use:** Finding relevant content, recommendations, similar items

```javascript
{
  "query": "What are you looking for?",
  "namespace": "your-namespace",
  "limit": 10
}
```

---

### 3. Generate Embeddings (optional)

```bash
POST /v1/projects/{project_id}/embeddings/generate
```

**When to use:** You need embeddings but want to store them yourself

```javascript
{
  "texts": ["Text to convert to vector"]
}
```

---

## 🎯 Best Practices

### Namespaces
Use namespaces to organize different types of data:

```javascript
// Good
namespace: "invoices"      // Financial documents
namespace: "products"      // Product catalog
namespace: "support-chat"  // Customer conversations

// Bad
namespace: "default"       // Everything mixed together
```

### Metadata
Add searchable metadata for filtering:

```javascript
// Good - Rich metadata
metadata: {
  customer_id: "C123",
  date: "2024-01-15",
  amount: 1500,
  status: "paid"
}

// Bad - No metadata
metadata: {}
```

### Batch Operations
Store multiple items at once for better performance:

```javascript
// Good - Batch insert
texts: ["Doc 1", "Doc 2", "Doc 3"],
metadata_list: [{...}, {...}, {...}]

// Slow - Multiple single inserts
// Don't make 100 separate API calls
```

---

## 🔧 Error Handling

```javascript
async function safeVectorSearch(query) {
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query, namespace: "products" })
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('API Error:', error.detail);
      return { results: [], error: error.detail };
    }

    return await response.json();
  } catch (error) {
    console.error('Network Error:', error);
    return { results: [], error: error.message };
  }
}
```

---

## 💰 Pricing

**FREE** - Embeddings are generated using our self-hosted Railway service
- No per-request charges for embedding generation
- Standard ZeroDB storage costs apply

---

## 🆘 Common Issues

### Issue: "401 Unauthorized"
**Solution:** Token expired, get a fresh one:
```bash
curl -X POST https://api.ainative.studio/v1/auth/login \
  -d "username=your@email.com&password=yourpassword"
```

### Issue: "404 Not Found"
**Solution:** Check your path - use `/v1/projects/{id}/embeddings/*` not `/v1/public/...`

### Issue: "No results returned"
**Solution:**
- Check namespace matches between store and search
- Lower the similarity threshold: `"threshold": 0.5`
- Verify data was actually stored first

---

## 🚀 Next Steps

1. **Start with Search:** Use `embed-and-store` + `search` for most use cases
2. **Add Filters:** Use metadata filters to narrow results
3. **Organize Data:** Use namespaces to separate different content types
4. **Scale Up:** Batch operations for better performance

---

## 📖 Complete API Reference

Full API documentation: https://api.ainative.studio/docs

Need help? Check the examples above or contact support.