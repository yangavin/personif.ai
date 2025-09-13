# 🔒 Security Notice

## API Key Exposure

**⚠️ IMPORTANT: AssemblyAI API Key was previously hardcoded in commit history**

The AssemblyAI API key `bdf0002c857f452dac6670c41392a68a` was accidentally committed to this repository in commit `cfd73de`.

## Immediate Actions Required:

1. **✅ DONE**: Moved API key to environment variable (.env file)
2. **⚠️ ACTION NEEDED**: Regenerate the AssemblyAI API key at https://www.assemblyai.com/dashboard/
3. **⚠️ ACTION NEEDED**: Update your local .env file with the new API key
4. **✅ DONE**: Added .env to .gitignore to prevent future exposure

## Current Security Status:

- ✅ API key now loaded from `process.env.ASSEMBLYAI_API_KEY`
- ✅ .env file is properly excluded from git
- ✅ Server code no longer contains hardcoded secrets
- ⚠️ Old API key should be regenerated for security

## How to Use:

1. Create a `.env` file in the project root:
```
ASSEMBLYAI_API_KEY=your_new_api_key_here
```

2. Get a new API key from AssemblyAI dashboard
3. Start the server: `node server.js`

## Git History:

The exposed API key exists in git history (commits cfd73de and bc55409). If this is a public repository, consider:
- Creating a fresh repository
- Or using `git filter-branch` to rewrite history (advanced)

## Prevention:

- Always use environment variables for API keys
- Never commit .env files
- Use tools like `git-secrets` to scan for secrets before committing