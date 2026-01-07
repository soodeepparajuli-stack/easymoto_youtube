
# GitHub Repository Secrets

To enable the daily video automation, you must add the following secrets to your GitHub repository settings (`Settings > Secrets and variables > Actions`).

| Secret Name | Description |
| :--- | :--- |
| `GEMINI_API_KEY` | Your Google Gemini API Key. |
| `GROQ_API_KEY` | Your Groq API Key. |
| `PEXELS_API_KEY` | Your Pexels API Key for stock footage. |
| `YOUTUBE_CLIENT_SECRET` | Content of your `client_secret.json` file. |
| `YOUTUBE_TOKEN_PICKLE_BASE64`| Base64 encoded content of your `token.pickle` (authenticated session). |

## How to generate `YOUTUBE_TOKEN_PICKLE_BASE64`

Run this Python script locally to get the base64 string:

```python
import base64

with open("token.pickle", "rb") as f:
    encoded = base64.b64encode(f.read()).decode("utf-8")
    print(encoded)
```

Copy the output and paste it as the secret value.
