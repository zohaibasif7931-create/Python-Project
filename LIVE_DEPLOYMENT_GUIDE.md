# Deploy Your Flask App to Live Server (Free) 🚀

## Best Free Options for Deployment:

### Option 1: **Render.com** (RECOMMENDED) ⭐
- Free tier available
- Supports Flask with SQLite
- Auto-deploys from GitHub
- No credit card needed for free tier

### Option 2: **Railway.app**
- Free tier with $5/month credit
- Great Flask support
- Easy deployment

### Option 3: **PythonAnywhere**
- Free tier (www.pythonanywhere.com)
- Direct Python web hosting

---

## Step-by-Step: Deploy on Render.com (EASIEST)

### STEP 1: Prepare Your Project Locally
```
1. Open your project in terminal
2. Run: pip freeze > requirements.txt
3. Make sure you have Procfile (✓ you have it)
```

### STEP 2: Move Main App to Root Directory
Since your Flask app is in `.venv/demo-project/main.py`, move it to the root:

```powershell
# Copy main.py to root
cp ".venv/demo-project/main.py" "main.py"

# Copy templates folder to root
cp -r ".venv/demo-project/templates" "templates"

# Copy static folder if exists
cp -r ".venv/demo-project/static" "static" -ErrorAction SilentlyContinue

# Copy database files
cp "phones.db" "phones.db"
cp "satisfaction.csv" "satisfaction.csv"
```

### STEP 3: Update Procfile
Update your Procfile to use the new main.py:
```
web: gunicorn main:app
```

### STEP 4: Push to GitHub
```powershell
# Initialize git repo (if not already)
git init
git add .
git commit -m "Ready for deployment"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### STEP 5: Deploy on Render
1. Go to https://render.com
2. Click **"New" → "Web Service"**
3. Connect your GitHub account
4. Select your repository
5. Fill in details:
   - **Name**: your-app-name
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app`
6. Click **"Create Web Service"**
7. Wait 2-3 minutes for deployment
8. Your app will be live at: `https://your-app-name.onrender.com`

---

## Step-by-Step: Deploy on Railway.app

### STEP 1: Prepare Project (same as Render)
Copy main app to root directory (see Step 2 above)

### STEP 2: Push to GitHub
(Same as Render - Step 4)

### STEP 3: Deploy on Railway
1. Go to https://railway.app
2. Click **"Start a New Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect GitHub and select your repo
5. Railway auto-detects Python/Flask
6. Click **"Deploy"**
7. Get your live URL from the dashboard

---

## Deployment Checklist:

- ✓ `requirements.txt` - Updated with all dependencies
- ✓ `Procfile` - Points to correct main.py and app
- ✓ `main.py` - In root directory (or update Procfile path)
- ✓ `templates/` - Folder exists in root
- ✓ `phones.db` - SQLite database included
- ✓ `satisfaction.csv` - Data file included
- ✓ All `.pkl` model files included
- ✓ GitHub repo created and pushed
- ✓ Environment variables set (if needed)

---

## Troubleshooting:

### Issue: "No such file or directory: phones.db"
**Solution**: Include database file in `.gitignore` ONLY if you regenerate it, or commit it.

### Issue: "ModuleNotFoundError"
**Solution**: Update requirements.txt:
```bash
pip freeze > requirements.txt
```

### Issue: App crashes on deploy
**Solution**: Check logs on Render/Railway dashboard and look for error messages.

### Issue: Templates not found
**Solution**: Make sure `templates/` folder is in the **same directory as main.py**

### Issue: Static files not loading
**Solution**: Create `static/` folder and put CSS/JS there

---

## To Check Live App:
1. Visit your live URL (e.g., `https://your-app.onrender.com`)
2. Test all features (buy, sell, recommendations)
3. Make sure database operations work

---

## Keep Your Data Safe:

Since SQLite databases don't persist between deployments on free tiers, consider:
- Using **PostgreSQL** (Render offers free tier)
- Or upload data files to your repo

For now, commit your databases to ensure they deploy with your app.

---

Good luck! 🚀 Your app will be live and accessible to everyone!
