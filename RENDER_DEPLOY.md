# Deploy to Render.com (100% FREE FOREVER)

## Why Render?
- ✅ **100% FREE forever** (no credit card required)
- ✅ **2-minute setup** (easiest option)
- ✅ **Auto-deploy from GitHub** (push = deploy)
- ✅ **Automatic HTTPS**
- ⚠️ Sleeps after 15 min inactivity (wakes in 30s on first visit)

## Step-by-Step Instructions

### 1. Push Your Code to GitHub
Your code is already on GitHub at: `henrybrewer00-dotcom/FourtyTwo`

### 2. Sign Up for Render
1. Go to https://render.com
2. Click **"Get Started"**
3. Click **"Sign in with GitHub"**
4. Authorize Render to access your repos

### 3. Create Web Service
1. Click **"New +"** (top right)
2. Select **"Web Service"**
3. Find your **FourtyTwo** repository
4. Click **"Connect"**

### 4. Configure (Auto-Detected!)
Render will automatically detect your `render.yaml` file and configure:
- ✅ Name: `fourtytwo-game`
- ✅ Build Command: `pip install -r requirements.txt`
- ✅ Start Command: `python app.py`
- ✅ Free tier selected

### 5. Deploy!
1. Click **"Create Web Service"**
2. Wait 2-3 minutes while it builds
3. Your app will be live at: `https://fourtytwo-game.onrender.com`

## That's It! 🎉

### Testing Your Deployment
1. Visit your `.onrender.com` URL
2. Create a guest account
3. Create a game
4. Share the link with friends
5. Play!

### Tips
- **First visit after sleep:** Takes ~30 seconds to wake up
- **Keeps awake:** If people are playing continuously
- **Auto-deploy:** Every time you push to GitHub, Render auto-deploys
- **Logs:** View real-time logs in Render dashboard
- **Custom domain:** You can add your own domain for free!

### Avoiding Sleep (Optional Tricks)
If you want to keep it awake 24/7 for free:
1. Use a service like **UptimeRobot** to ping your site every 5 minutes
2. Or use **Cron-Job.org** for free scheduled pings

### Support
- **Render Docs:** https://render.com/docs
- **Status:** Check https://status.render.com
- **Community:** https://community.render.com

## Cost: $0 Forever ✨
Render's free tier is permanent. No hidden fees, no credit card needed.

Happy gaming! 🎲
