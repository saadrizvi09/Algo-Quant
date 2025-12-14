## 🚀 Quick Deployment Steps for Hugging Face Spaces

### Step 1: Create Space on Web (Do this first!)
1. Go to: https://huggingface.co/new-space
2. Fill in:
   - **Space name:** algoquant-backend
   - **License:** MIT
   - **SDK:** Docker (Select from dropdown)
   - **Hardware:** CPU basic (free)
3. Click **"Create Space"**

### Step 2: Clone Your Space
After creating the Space, run:
```powershell
cd "C:\Projects\Full stack trading bot"
git clone https://huggingface.co/spaces/YOUR_USERNAME/algoquant-backend hf-space
```
Replace YOUR_USERNAME with your Hugging Face username (saadrizvi09)

### Step 3: Copy Backend Files
```powershell
cd hf-space
Copy-Item -Path "..\backend\*" -Destination "." -Recurse -Exclude "venv","__pycache__",".env","*.db"
```

### Step 4: Prepare README
```powershell
if (Test-Path "README_HF.md") { Rename-Item "README_HF.md" "README.md" -Force }
```

### Step 5: Commit and Push
```powershell
git add .
git commit -m "Deploy AlgoQuant Backend"
git push
```

### Step 6: Add Secrets (Important!)
1. Go to your Space: https://huggingface.co/spaces/YOUR_USERNAME/algoquant-backend
2. Click **"Settings"** tab
3. Scroll to **"Repository secrets"**
4. Add these secrets:
   - Name: `DATABASE_URL`
     Value: `sqlite:///./algoquant.db` (for testing) or your PostgreSQL URL
   - Name: `SECRET_KEY`
     Value: Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### Step 7: Monitor Build
1. Go to **"Logs"** tab in your Space
2. Wait for Docker build to complete (~5-10 minutes)
3. Once done, your API will be live at:
   https://YOUR_USERNAME-algoquant-backend.hf.space

### Step 8: Test API
```powershell
# Test the API
curl https://YOUR_USERNAME-algoquant-backend.hf.space/docs
```

---

## Commands Summary (Copy-Paste After Creating Space)

```powershell
# Navigate to project
cd "C:\Projects\Full stack trading bot"

# Clone your Space (replace YOUR_USERNAME)
git clone https://huggingface.co/spaces/YOUR_USERNAME/algoquant-backend hf-space

# Go to space directory
cd hf-space

# Copy backend files
Copy-Item -Path "..\backend\*" -Destination "." -Recurse -Exclude "venv","__pycache__",".env","*.db","*.pyc"

# Rename README
if (Test-Path "README_HF.md") { Rename-Item "README_HF.md" "README.md" -Force }

# Commit and push
git add .
git commit -m "Deploy AlgoQuant Backend to Hugging Face"
git push

# Done! Now add secrets in Space Settings
```

---

## Next Steps After Deployment

1. **Add Secrets** in Space Settings (DATABASE_URL, SECRET_KEY)
2. **Wait for build** in Logs tab
3. **Test API** at https://YOUR_USERNAME-algoquant-backend.hf.space/docs
4. **Update Frontend** to use the deployed backend URL

Your backend will auto-redeploy whenever you push to the Space repository!
