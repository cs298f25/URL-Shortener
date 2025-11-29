# URL-Shortener
URL-Shortener

Development process described in [developers.md](docs/developers.md)

Authors: Jake Morro, Cole Aydelotte

## Redis Setup
The application now persists link data in Redis instead of JSON files.

1. Install Redis (for macOS: `brew install redis`, or see https://redis.io/docs/getting-started/installation/ for other platforms).
2. Start a local Redis server with the default configuration (`redis-server`). The app assumes `redis://localhost:6379/0` when `REDIS_URL` is not set.
3. (Optional) Point the app to a different instance by exporting `REDIS_URL=redis://<host>:<port>/<db>` before running Flask or Gunicorn.

With Redis running, install dependencies (`pip install -r requirements.txt`) and start the Flask app as usual. All short code mappings will be stored under the `link:` namespace in Redis.