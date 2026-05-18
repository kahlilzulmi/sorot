# Socket.IO Production Server Options (Flask)

Werkzeug is fine for local development only. For production, use an async-capable server stack.

## Recommended Choice

Use Gunicorn + Eventlet behind Nginx on Linux.

Why:
- Stable Socket.IO/WebSocket behavior
- Straightforward deployment
- Common Flask-SocketIO production path

## Option 1: Gunicorn + Eventlet (Recommended)

Install:

```bash
pip install gunicorn eventlet
```

Run:

```bash
gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 sorot:app
```

Notes:
- Use `-w 1` unless you configure a message queue (Redis) for multi-worker scaling.

## Option 2: Gunicorn + Gevent

Install:

```bash
pip install gunicorn gevent gevent-websocket
```

Run:

```bash
gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:5000 sorot:app
```

## Option 3: uWSGI + gevent (Advanced)

Use only if your ops team already manages uWSGI. Config is more complex than Gunicorn.

## Reverse Proxy (Nginx)

Enable websocket upgrade headers for `/socket.io`:
- `Upgrade $http_upgrade`
- `Connection "upgrade"`

Without this, Socket.IO can fail or fall back poorly.

## Scaling Rule

If you want multiple workers/instances, add a message queue:
- Redis as Socket.IO message broker
- Configure Flask-SocketIO with `message_queue` URL

## Windows Note

Production deployment is best on Linux containers/VMs. Keep Windows + Werkzeug for local development.
