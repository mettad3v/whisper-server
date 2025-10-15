# CORS Configuration Guide

## Current Configuration (Development)

The API is currently configured to allow **all origins** (`*`) for easy development:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

This allows your frontend to make requests from any domain during development.

---

## Production Configuration

For production, you should **restrict origins** to your specific frontend URL(s):

### Option 1: Single Frontend Domain

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Option 2: Multiple Environments

```python
import os

# Get allowed origins from environment variable
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173"  # Default for local dev
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

Then set in your environment:

```bash
# Development
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173"

# Production
export ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

### Option 3: Environment-Based Configuration

```python
import os

# Determine environment
ENV = os.getenv("ENVIRONMENT", "development")

if ENV == "production":
    # Strict CORS for production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://yourdomain.com",
            "https://www.yourdomain.com"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )
else:
    # Permissive CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

---

## Testing CORS

### From Browser Console

```javascript
// Test from your frontend's browser console
fetch("http://localhost:8000/health")
  .then((r) => r.json())
  .then(console.log)
  .catch(console.error);
```

### From Different Origin

```javascript
// This should work with CORS enabled
const formData = new FormData();
formData.append("file", audioFile);

fetch("http://localhost:8000/transcribe", {
  method: "POST",
  body: formData,
})
  .then((r) => r.json())
  .then(console.log);
```

---

## Common Frontend Frameworks

### React (Vite)

If using Vite, you can also configure a proxy in `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
```

Then use `/api/transcribe` instead of `http://localhost:8000/transcribe`.

### Next.js

Add to `next.config.js`:

```javascript
module.exports = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};
```

---

## Security Best Practices

1. **Never use `allow_origins=["*"]` in production**
2. **Specify exact origins** - don't use wildcards in production
3. **Limit methods** - only allow necessary HTTP methods
4. **Limit headers** - specify exact headers if possible
5. **Use HTTPS** in production for both frontend and backend

---

## Troubleshooting

### Error: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Solution**: Make sure CORS middleware is added and the origin is allowed.

### Error: "CORS policy: The value of the 'Access-Control-Allow-Credentials' header"

**Solution**: When using `allow_credentials=True`, you cannot use `allow_origins=["*"]`. Specify exact origins.

### Preflight Requests Failing

**Solution**: Make sure `OPTIONS` method is allowed:

```python
allow_methods=["GET", "POST", "OPTIONS"]
```

---

## Current Status

✅ **CORS is enabled** with permissive settings for development
⚠️ **Remember to restrict origins before deploying to production**
