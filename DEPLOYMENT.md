# Deployment Guide for Texas 42 Game

This is a Flask application with WebSocket support (using Socket.IO). It requires a server that supports long-running connections and WebSockets.

## Important Note about Cloudflare Pages

**Cloudflare Pages is for static sites only** and cannot run this Flask application. This app requires:
- Python runtime
- WebSocket connections (Socket.IO)
- SQLite database
- Server-side processing

## Recommended Deployment Options

### Option 1: Render.com (Recommended - Free Tier Available)

1. **Push your code to GitHub**
2. **Go to [render.com](https://render.com)** and sign in with GitHub
3. **Click "New +" → "Web Service"**
4. **Connect your GitHub repository**
5. **Render will auto-detect the `render.yaml` file** and configure everything
6. **Click "Create Web Service"**

That's it! Render will:
- Install dependencies from `requirements.txt`
- Run `python app.py`
- Provide a free `.onrender.com` URL
- Auto-deploy on every GitHub push

**Note:** Free tier services sleep after inactivity and take ~30s to wake up.

### Option 2: Railway.app

1. **Push your code to GitHub**
2. **Go to [railway.app](https://railway.app)** and sign in with GitHub
3. **Click "New Project" → "Deploy from GitHub repo"**
4. **Select your repository**
5. **Railway will auto-detect Python** and use `railway.json` config
6. **Add environment variable:** `SECRET_KEY` (Railway can generate this)
7. **Deploy!**

Railway provides:
- Free $5 credit per month
- Auto-deploy from GitHub
- Custom domains
- Better performance than Render free tier

### Option 3: Fly.io

1. **Install Fly CLI:** `curl -L https://fly.io/install.sh | sh`
2. **Login:** `fly auth login`
3. **Create app:** `fly launch` (follow prompts)
4. **Set secret:** `fly secrets set SECRET_KEY=$(openssl rand -base64 32)`
5. **Deploy:** `fly deploy`

Fly.io provides:
- Generous free tier (3 small VMs)
- Global edge network
- WebSocket support
- Fast deployments

### Option 4: Heroku

1. **Install Heroku CLI**
2. **Login:** `heroku login`
3. **Create app:** `heroku create your-app-name`
4. **Set buildpack:** `heroku buildpacks:set heroku/python`
5. **Set config:** `heroku config:set SECRET_KEY=$(openssl rand -base64 32)`
6. **Deploy:** `git push heroku main`

Note: Heroku no longer has a free tier.

## Environment Variables

All platforms need these environment variables:

- `SECRET_KEY` - Flask secret key (auto-generated on most platforms)
- `PORT` - Port to run on (usually auto-set by platform, default: 8080)

## Database

The app uses SQLite by default, which is fine for small deployments. For production at scale, consider:
- PostgreSQL (supported by all platforms above)
- Update `SQLALCHEMY_DATABASE_URI` in `app.py`

## WebSocket Configuration

The app uses:
- Flask-SocketIO with eventlet
- CORS enabled for all origins (`cors_allowed_origins="*"`)
- Auto-reconnection on client side

Most platforms support WebSockets by default. No special configuration needed.

## Testing Deployment

After deploying:

1. **Visit your app URL**
2. **Create a guest account**
3. **Create a game**
4. **Test in multiple browser tabs** (to verify WebSocket sync)
5. **Try on mobile device** (to verify network accessibility)

## Troubleshooting

**App won't start:**
- Check logs on your platform
- Verify `requirements.txt` has all dependencies
- Ensure Python 3.9+ is being used

**WebSockets not working:**
- Check if platform supports WebSockets (all above do)
- Look for connection errors in browser console
- Verify CORS settings

**Database errors:**
- Delete old `game.db` file
- Ensure database migrations run on deploy
- Check file write permissions

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Access at http://localhost:8080
```

## GitHub Integration

All recommended platforms support automatic deployment from GitHub:

1. **Connect your GitHub repo** to the platform
2. **Enable auto-deploy** from main/master branch
3. **Push to GitHub** - platform auto-deploys
4. **Monitor deployment** in platform dashboard

## Custom Domain

All platforms above support custom domains:
- Add your domain in platform settings
- Update DNS CNAME record to point to platform URL
- SSL/TLS is automatic on all platforms

## Cost Comparison

| Platform | Free Tier | Paid Start | Best For |
|----------|-----------|------------|----------|
| Render   | Yes (sleeps) | $7/mo | Easy setup |
| Railway  | $5 credit/mo | $5/mo usage | Best free tier |
| Fly.io   | 3 VMs free | Usage-based | Global edge |
| Heroku   | No | $7/mo | Enterprise |

## Support

For issues:
- Check platform documentation
- Review deployment logs
- Test locally first
- Verify environment variables

Happy deploying! 🎲
