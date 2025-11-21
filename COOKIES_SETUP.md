# How to Add X.com Cookies for Authentication

Twitter/X rate-limits unauthenticated requests. To fix the 403 error, add your X.com login cookies:

## Steps:

1. **Log into X.com in your browser**
   - Go to https://x.com and log in to your account

2. **Extract cookies using DevTools**
   - Press `F12` to open DevTools
   - Go to **Application** tab
   - Click **Cookies** → **https://x.com**
   - You'll see a list of cookies

3. **Format and save cookies**
   - Export the cookies as JSON format into `cookies.json`
   - The format should be:
   ```json
   [
     {
       "name": "cookie_name",
       "value": "cookie_value",
       "domain": ".x.com",
       "path": "/"
     },
     {
       "name": "another_cookie",
       "value": "another_value",
       "domain": ".x.com",
       "path": "/"
     }
   ]
   ```

4. **Restart the bot**
   - Once you save cookies.json, the bot will automatically load them on startup
   - You'll see: `✅ Cookies loaded` in the logs

## Why This Helps:
- Authenticated requests have much higher rate limits
- Fixes the `403 Forbidden` error
- Allows monitoring of protected/private accounts
- More reliable tweet fetching

## Security Note:
- Keep `cookies.json` private - it contains your session data
- Don't share it publicly
- It's already in .gitignore so it won't be committed
