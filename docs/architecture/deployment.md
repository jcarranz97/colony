# Deployment Guide

This guide covers how Colony's components are deployed to various
environments.

## Documentation Deployment

Colony's documentation is automatically deployed to GitHub Pages using
GitHub Actions.

### GitHub Pages Setup

The documentation is built with MkDocs Material and deployed to GitHub
Pages at: `https://your-username.github.io/colony/`

### Automatic Deployment

Every push to the `main` branch automatically triggers a documentation
build and deployment via GitHub Actions.

#### GitHub Actions Workflow

The deployment is handled by `.github/workflows/docs.yml`:

```yaml
name: Deploy Documentation
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure Git Credentials
        run: |
          git config user.name github-actions[bot]
          git config user.email 41898282+github-actions[bot]@users.noreply.github.com

      - uses: actions/setup-python@v4
        with:
          python-version: 3.x

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          key: ${{ github.ref }}
          path: .cache

      - name: Install dependencies
        run: pip install mkdocs-material

      - name: Deploy to GitHub Pages
        run: mkdocs gh-deploy --force
```

### Manual Deployment

To deploy documentation manually:

```bash
# Install dependencies
pip install mkdocs-material

# Deploy to GitHub Pages
mkdocs gh-deploy
```

### Repository Settings

Ensure your GitHub repository has the following settings:

1. **Go to Settings > Pages**
2. **Source**: Deploy from a branch
3. **Branch**: `gh-pages`
4. **Folder**: `/ (root)`

The `gh-deploy` command automatically creates and manages the `gh-pages`
branch.

### Local Preview

To preview documentation locally before deployment:

```bash
# Install dependencies
pip install mkdocs-material

# Serve locally
mkdocs serve

# Access at http://localhost:8000
```

### Troubleshooting

**Common Issues:**

- **Permission denied**: Ensure GitHub Actions has write permissions
- **Build fails**: Check that all referenced files exist in the docs folder
- **Pages not updating**: GitHub Pages can take a few minutes to reflect
  changes

**Debug Steps:**

1. Check GitHub Actions logs in the Actions tab
2. Verify all documentation files are committed
3. Ensure `mkdocs.yml` configuration is valid
4. Test build locally with `mkdocs build`

---

## Application Deployment — Kubernetes (k3s)

Colony ships with a Helm chart located at `helm/colony/` for deploying
to a Kubernetes cluster. This guide targets a k3s homelab setup with a
private Harbor registry.

**Cluster assumptions used in this guide:**

| Item | Value |
|---|---|
| Node IPs | `192.168.1.208` (control-plane), `192.168.1.206` (worker) |
| Harbor URL | `http://192.168.1.206:30002` |
| Target namespace | `colony-app` |
| Frontend URL | `http://192.168.1.206:30080` |
| Backend URL | `http://192.168.1.206:30800` |

Substitute your own values where needed.

---

### Prerequisites

Install the following tools on the machine you will deploy from:

- **kubectl** — configured with access to the cluster
  (`kubectl get nodes` should return your nodes)
- **helm** v3 — `helm version` to verify
- **docker** — for building and pushing images

---

### Step 1 — Harbor Setup (one-time)

#### 1a. Allow insecure HTTP registry on each k3s node

Harbor runs on plain HTTP, so every k3s node must be told to trust it.
SSH into each node and create or edit
`/etc/rancher/k3s/registries.yaml`:

```yaml
mirrors:
  "192.168.1.206:30002":
    endpoint:
      - "http://192.168.1.206:30002"
```

Then restart k3s:

```bash
# On dell-01
sudo systemctl restart k3s

# On nuc-01
sudo systemctl restart k3s-agent
```

Verify k3s restarted cleanly:

```bash
kubectl get nodes
```

#### 1b. Allow insecure push from your local Docker

The steps differ depending on how Docker is installed on your machine.

##### Option A — Docker Engine installed natively inside WSL2 (Linux)

This is the case when you run `sudo apt install docker.io` (or equivalent)
inside your WSL distro and the daemon runs there. All configuration happens
from inside the WSL terminal.

Edit `/etc/docker/daemon.json` inside WSL (create if missing):

```json
{
  "insecure-registries": ["192.168.1.206:30002"]
}
```

Restart the Docker daemon. WSL2 distros often run without systemd, so try
`service` first:

```bash
sudo service docker restart
```

If your distro has systemd enabled (WSL2 + systemd is supported in recent
Windows builds and Ubuntu 22.04+):

```bash
sudo systemctl restart docker
```

Verify it picked up the change:

```bash
docker info | grep -A5 "Insecure Registries"
```

##### Option B — Docker Desktop for Windows (WSL integration)

This is the case when Docker Desktop is installed on Windows and your WSL
distro uses it via the **"Use the WSL 2 based engine"** integration.
The daemon runs inside Docker Desktop's own VM, so editing
`/etc/docker/daemon.json` inside WSL has no effect — the change must be
made on the Windows side.

**Via the Docker Desktop UI (recommended):**

1. Open Docker Desktop on Windows
2. Go to **Settings → Docker Engine**
3. Add the `insecure-registries` key to the JSON config:

```json
{
  "insecure-registries": ["192.168.1.206:30002"]
}
```

4. Click **Apply & restart**

**Via the Windows config file (alternative):**

Open `%USERPROFILE%\.docker\daemon.json`
(i.e. `C:\Users\<your-username>\.docker\daemon.json`) in any text editor
and add the same JSON block above. Then restart Docker Desktop.

After either method, verify from your WSL terminal:

```bash
docker info | grep -A5 "Insecure Registries"
```

You should see `192.168.1.206:30002` listed.

#### 1c. Create a project in Harbor

1. Open `http://192.168.1.206:30002` in a browser
2. Log in (default credentials: `admin` / `Harbor12345` — change these)
3. Go to **Projects → New Project**
4. Create a project named `colony` (or use the existing `library` project)
5. Set the project to **Public** so k3s can pull without authentication, or
   keep it private and create a pull secret (see
   [Step 4 — Pull Secret](#step-4--optional-harbor-pull-secret))

#### 1d. Log in to Harbor from Docker

```bash
docker login 192.168.1.206:30002
# Enter your Harbor username and password
```

---

### Step 2 — Build and Push Images

> **Frontend API URL — runtime injection**
>
> The frontend image is built with a placeholder string instead of a
> hardcoded URL. At container startup, `entrypoint.sh` replaces that
> placeholder in the compiled JavaScript with the value of
> `NEXT_PUBLIC_API_URL` supplied at runtime. This means **one image can
> be deployed anywhere** — no rebuild needed when the backend URL changes.
> The URL is set in `values.yaml` under `frontend.env.apiUrl` and injected
> by Helm as a container environment variable.

#### Build the backend

```bash
docker build \
  -t 192.168.1.206:30002/colony/colony-backend:1.0.0 \
  ./backend

docker push 192.168.1.206:30002/colony/colony-backend:1.0.0
```

#### Build the frontend

```bash
docker build \
  -t 192.168.1.206:30002/colony/colony-frontend:1.0.0 \
  ./frontend

docker push 192.168.1.206:30002/colony/colony-frontend:1.0.0
```

---

### Step 3 — Install with Helm

Configuration goes in a custom `my-values.yaml` file. Two starting
templates follow — **Option 1** with Ingress for hostname-based access,
**Option 2** with NodePort-only access. Both are valid; you can migrate
from one to the other later via `helm upgrade`.

> **Why a values file rather than `--set` flags?** Helm's `--set` parser
> treats commas as key/value delimiters, so settings that contain commas
> (notably the JSON `allowedHosts` array) fail to parse with
> `Error: failed parsing --set data: key "..." has no value`. A values
> file is immune to this and to most shell-quoting traps. Same on Helm
> 3.x and 4.x.

#### Option 1 — NodePort + Ingress (recommended)

Reach the app at clean hostnames like `http://colony.dev.lan` and
`http://api.colony.dev.lan`, served by Traefik (which ships with k3s by
default). Requires DNS resolution for those names — see
[*Step 7 — Switching Between NodePort and Ingress*](#step-7--optional-switching-between-nodeport-and-ingress)
for `/etc/hosts` setup or the homelab's
[Pi-hole guide](https://github.com/jcarranz97/homelab/blob/main/docs/guides/pi-hole-setup.md).

```yaml title="my-values.yaml — with Ingress"
image:
  registry: "192.168.1.206:30002"

backend:
  image:
    repository: colony/colony-backend
    tag: "1.0.0"
  port: 8000
  service:
    type: NodePort
    nodePort: 30800
  env:
    secretKey: "your-long-random-secret-here"
    # CORS: include both Ingress hostname and NodePort URL during transition.
    allowedHosts: '["http://colony.dev.lan","http://192.168.1.206:30080"]'
    defaultAdminPassword: "your-admin-password"

frontend:
  image:
    repository: colony/colony-frontend
    tag: "1.0.0"
  port: 3000
  service:
    type: NodePort
    nodePort: 30080
  env:
    # Browser-side URL the JS calls. Use the Ingress hostname.
    apiUrl: "http://api.colony.dev.lan/api/v1"

ingress:
  enabled: true
  ingressClassName: traefik
  frontend:
    host: colony.dev.lan
  backend:
    host: api.colony.dev.lan

postgresql:
  password: "your-strong-db-password"
```

#### Option 2 — NodePort only (no Ingress)

Reach the app at `http://<node-ip>:<nodePort>`. Simpler — no DNS or
ingress controller assumptions. This is also the default if you omit the
`ingress` block entirely.

```yaml title="my-values.yaml — NodePort only"
image:
  registry: "192.168.1.206:30002"

backend:
  image:
    repository: colony/colony-backend
    tag: "1.0.0"
  port: 8000
  service:
    type: NodePort
    nodePort: 30800
  env:
    secretKey: "your-long-random-secret-here"
    allowedHosts: '["http://192.168.1.206:30080"]'
    defaultAdminPassword: "your-admin-password"

frontend:
  image:
    repository: colony/colony-frontend
    tag: "1.0.0"
  port: 3000
  service:
    type: NodePort
    nodePort: 30080
  env:
    apiUrl: "http://192.168.1.206:30800/api/v1"

postgresql:
  password: "your-strong-db-password"
```

#### Install

Whichever file you used:

```bash
helm install colony ./helm/colony \
  --namespace colony-app \
  --create-namespace \
  -f my-values.yaml
```

> **Tip — separate values files per environment.** Keep distinct files
> for dev and prod (e.g. `~/homelab/colony-dev/my-values.yaml` and
> `~/homelab/colony-prod/my-values.yaml`) with their own NodePort numbers,
> hostnames, and image tags. They install with the same chart but
> different `--namespace` and `-f`. To make dev/prod resource names
> distinct in the cluster, use distinct release names too —
> `helm install colony-dev …` vs `helm install colony-prod …` — which
> propagates through every templated resource via
> `{{ include "colony.fullname" . }}`.

#### Step 4 — Optional: Harbor Pull Secret

If your Harbor project is private, create a pull secret so k3s can
authenticate:

```bash
kubectl create secret docker-registry harbor-secret \
  --docker-server=192.168.1.206:30002 \
  --docker-username=<harbor-user> \
  --docker-password=<harbor-password> \
  --namespace colony-app
```

Then set `imagePullSecrets` in your values file:

```yaml
imagePullSecrets:
  - name: harbor-secret
```

---

### Step 5 — Verify the Deployment

```bash
# Watch pods come up
kubectl get pods -n colony-app -w

# All three pods should reach Running/Ready state:
# colony-backend-*     1/1  Running
# colony-frontend-*    1/1  Running
# colony-postgresql-*  1/1  Running

# Check services and NodePorts
kubectl get svc -n colony-app
```

---

### Step 6 — Access the Application

| Service | URL |
|---|---|
| Frontend (app) | `http://192.168.1.206:30080` |
| Backend API docs | `http://192.168.1.206:30800/docs` |
| Backend health | `http://192.168.1.206:30800/health` |

The default admin credentials are whatever you set in
`backend.env.defaultAdminUsername` / `backend.env.defaultAdminPassword`
(defaults: `admin` / `colony-admin`).

---

### Step 7 — Optional: Switching Between NodePort and Ingress

If you installed with **Option 1** (Ingress already enabled in
`my-values.yaml`), the chart has already created the Ingress resources;
skip ahead to *7b* for DNS setup.

If you installed with **Option 2** (NodePort-only) and later want
hostname access, edit `my-values.yaml` to enable the Ingress block and
update the URLs the frontend and backend use:

```yaml
ingress:
  enabled: true
  ingressClassName: traefik
  frontend:
    host: colony.dev.lan
  backend:
    host: api.colony.dev.lan

backend:
  env:
    # Both Ingress hostname and NodePort URL — coexist during the switch.
    allowedHosts: '["http://colony.dev.lan","http://192.168.1.206:30080"]'

frontend:
  env:
    apiUrl: "http://api.colony.dev.lan/api/v1"
```

Apply:

```bash
helm upgrade colony ./helm/colony \
  --namespace colony-app \
  -f my-values.yaml
```

#### 7a. Verify Traefik and the Ingress resources

k3s ships Traefik preinstalled — no extra install is needed. Sanity check
the controller and the Ingresses created by the chart:

```bash
kubectl get ingressclass
# NAME      CONTROLLER                      AGE
# traefik   traefik.io/ingress-controller   ...

kubectl get svc -n kube-system traefik
# TYPE           EXTERNAL-IP                   PORT(S)
# LoadBalancer   192.168.1.206,192.168.1.208   80:32103/TCP,443:32192/TCP

kubectl get ingress -n colony-app
# NAME              CLASS     HOSTS                ADDRESS                       PORTS
# colony-frontend   traefik   colony.dev.lan       192.168.1.206,192.168.1.208   80
# colony-backend    traefik   api.colony.dev.lan   192.168.1.206,192.168.1.208   80
```

The Ingress resource names follow `{{ release-name }}-frontend` /
`-backend`, so a release named `colony-dev` would produce
`colony-dev-frontend` / `colony-dev-backend`.

#### 7b. Resolve the hostnames

Until a LAN-wide DNS server is in place, add entries on each client
machine that needs access. **`/etc/hosts` does not support wildcards** —
list each hostname explicitly, one per line (or space-separated on a
single line):

```text
192.168.1.206  colony.dev.lan api.colony.dev.lan
```

For a permanent solution that covers every device on the network with a
single `*.dev.lan` wildcard rule, see the homelab guide
[Pi-hole Local DNS Setup](https://github.com/jcarranz97/homelab/blob/main/docs/guides/pi-hole-setup.md).

#### 7c. Verify end-to-end

```bash
getent hosts colony.dev.lan          # → 192.168.1.206
getent hosts api.colony.dev.lan      # → 192.168.1.206

curl -I http://colony.dev.lan        # → HTTP/1.1 200 OK
curl http://api.colony.dev.lan/health
```

Open `http://colony.dev.lan` in a browser and log in. The frontend's
JavaScript will call the backend at `http://api.colony.dev.lan/api/v1`.

> **NodePort still works — but only if the browser has DNS for the
> hostname.** Once `apiUrl` points at `api.colony.dev.lan`, accessing the
> frontend via `http://192.168.1.206:30080` still serves the page, but
> its API calls will fail unless that browser can also resolve
> `api.colony.dev.lan` (via `/etc/hosts` or Pi-hole). For machines without
> DNS for the new names, keep using the NodePort URLs end-to-end.

> **HTTPS and `cookieSecure`.** This Ingress serves plain HTTP, so leave
> `frontend.env.cookieSecure: "false"` (the chart default) — `Secure`
> cookies are dropped over HTTP and break login. When you later add TLS
> to Traefik (cert-manager + Let's Encrypt, or self-signed via mkcert),
> flip `cookieSecure` to `"true"`. See *Login succeeds (backend returns
> 200) but the app redirects back to login* in the troubleshooting
> section below for context.

---

### Updating the Application

#### Update the backend

```bash
# 1. Build and push the new image
docker build -t 192.168.1.206:30002/colony/colony-backend:1.1.0 ./backend
docker push 192.168.1.206:30002/colony/colony-backend:1.1.0

# 2. Upgrade the release
helm upgrade colony ./helm/colony \
  --namespace colony-app \
  --reuse-values \
  --set backend.image.tag=1.1.0
```

#### Update the frontend

```bash
# 1. Build and push the new image (no build args needed)
docker build \
  -t 192.168.1.206:30002/colony/colony-frontend:1.1.0 \
  ./frontend
docker push 192.168.1.206:30002/colony/colony-frontend:1.1.0

# 2. Upgrade the release
helm upgrade colony ./helm/colony \
  --namespace colony-app \
  --reuse-values \
  --set frontend.image.tag=1.1.0
```

To change the backend URL the frontend points to (e.g. after moving to a
different node or port), no image rebuild is required — just update the
value and upgrade:

```bash
helm upgrade colony ./helm/colony \
  --namespace colony-app \
  --reuse-values \
  --set frontend.env.apiUrl="http://192.168.1.206:30800/api/v1"
```

#### Update both at once

```bash
helm upgrade colony ./helm/colony \
  --namespace colony-app \
  --reuse-values \
  --set backend.image.tag=1.1.0 \
  --set frontend.image.tag=1.1.0
```

> **Note on `--reuse-values`**: This flag carries forward all values from
> the previous `helm install` or `helm upgrade`. You only need to specify
> the values you want to change.

---

### Rolling Back

If an upgrade introduces a problem, roll back to the previous release:

```bash
# See the release history
helm history colony -n colony-app

# Roll back to the previous revision
helm rollback colony -n colony-app

# Roll back to a specific revision number
helm rollback colony 2 -n colony-app
```

---

### Seeding Sample Data (optional)

The backend automatically creates the admin user on first startup via the
`DEFAULT_ADMIN_*` environment variables. Seeding is only needed if you want
to pre-populate sample payment methods, cycles, and expenses.

```bash
helm upgrade colony ./helm/colony \
  --namespace colony-app \
  --reuse-values \
  --set seeder.enabled=true \
  --set-file seeder.seedDataContent=./seed_data.yaml
```

The seeder runs once as a Kubernetes Job (Helm post-install hook) and
self-deletes after it succeeds.

---

### Uninstalling

```bash
helm uninstall colony -n colony-app

# Optionally delete the namespace (removes all remaining resources)
kubectl delete namespace colony-app
```

> The PostgreSQL PersistentVolumeClaim is **not** deleted by
> `helm uninstall` because Helm does not delete PVCs by default. Delete it
> manually if you want to wipe the data:
>
> ```bash
> kubectl delete pvc colony-postgres-data -n colony-app
> ```

---

### Helm Chart Reference

The chart lives at `helm/colony/`. Key files:

| File | Purpose |
|---|---|
| `Chart.yaml` | Chart metadata and version |
| `values.yaml` | All configurable defaults |
| `templates/secrets.yaml` | K8s Secret: DB password, JWT key |
| `templates/configmap-backend.yaml` | Non-sensitive backend env vars |
| `templates/postgres-*.yaml` | PostgreSQL Deployment, Service, PVC |
| `templates/backend-*.yaml` | FastAPI Deployment + NodePort Service |
| `templates/frontend-*.yaml` | Next.js Deployment + NodePort Service |
| `templates/ingress.yaml` | Frontend + backend Ingresses (gated by `ingress.enabled`) |
| `templates/seeder-job.yaml` | Optional seed data Job (post-install) |

#### Key values

| Value | Default | Description |
|---|---|---|
| `image.registry` | `192.168.1.206:30002` | Harbor registry address |
| `backend.image.tag` | `latest` | Backend image tag |
| `frontend.image.tag` | `latest` | Frontend image tag |
| `frontend.env.apiUrl` | `http://192.168.1.206:30800/api/v1` | Backend URL injected at runtime |
| `backend.service.nodePort` | `30800` | Backend external port |
| `frontend.service.nodePort` | `30080` | Frontend external port |
| `backend.env.secretKey` | *(must set)* | JWT signing secret |
| `backend.env.allowedHosts` | `["http://192.168.1.206:30080"]` | CORS origins |
| `postgresql.password` | *(must set)* | Database password |
| `postgresql.persistence.size` | `5Gi` | PVC size for Postgres |
| `ingress.enabled` | `false` | Create Ingress resources for frontend + backend |
| `ingress.frontend.host` | `""` | Frontend hostname (e.g. `colony.dev.lan`) |
| `ingress.backend.host` | `""` | Backend hostname (e.g. `api.colony.dev.lan`) |
| `seeder.enabled` | `false` | Enable sample data seeder |

---

## Troubleshooting & FAQ

### Backend pod crashes on startup with `psycopg2.OperationalError`

**Symptom:** The backend pod enters a crash loop immediately after the
init container exits. The logs show a connection error like:

```
psycopg2.OperationalError: connection to server on socket
"@##@colony-postgresql/.s.PGSQL.5432" failed: Connection refused
```

**Cause:** The `postgresql.password` (or `postgresql.username`) in your
`values.yaml` contains URL-special characters — most commonly `@` or `#`.
These break the `DATABASE_URL` connection string:

- `@` is the delimiter between credentials and hostname in a URL
  (`user:pass@host`), so a `@` in the password confuses the parser.
- `#` marks the start of a URL fragment, causing everything after it to be
  ignored.

The Helm chart URL-encodes both fields with `urlquery` to prevent this, but
if you are using an older revision of the chart (before this fix) you will
hit this issue.

**Fix:** Upgrade to the latest chart revision and restart the backend:

```bash
helm upgrade colony ./helm/colony --namespace colony-app -f my-values.yaml
kubectl rollout restart deployment colony-backend -n colony-app
```

**Prevention:** Any password that works in a URL is fine. Characters to
avoid unless you are on the fixed chart version: `@`, `#`, `%`, `?`, `&`.

### Login returns 401 "Incorrect username or password" on first deploy

**Symptom:** The app loads, login page appears, but every login attempt
with the admin credentials returns 401.

**Cause:** The admin user was never created. In the original Helm
deployment the seeder was disabled by default, and the backend's startup
only created tables — it did not bootstrap the admin user. A fresh
database therefore has all tables but no rows in `users`.

**Fix (chart v0.1.0 and later):** As of the fix shipped in this chart,
`_bootstrap_admin()` runs inside the FastAPI `lifespan` on every startup.
It creates the default household and admin user automatically if they do
not already exist. Simply deploying the updated image is enough.

**Fix (manual, for existing deployments):** If you are on an older image
and the tables are already created but empty, exec into the running backend
pod and run the seeder in `auth_only` mode — this creates only the admin
user and household without touching any sample data:

```bash
kubectl exec -n colony-app deployment/colony-backend -- \
  sh -c "echo '{}' > /tmp/seed.yaml && \
         SEED_FILE=/tmp/seed.yaml \
         SEED_MODE=auth_only \
         uv run python scripts/seed_db.py"
```

**Prevention:** Build and deploy the updated backend image which includes
the `_bootstrap_admin()` lifespan call in `app/main.py`.

### Login succeeds (backend returns 200) but the app redirects back to login

**Symptom:** You can see a `POST /api/v1/auth/login 200 OK` in the backend
logs, but the browser immediately returns to the login page.

**Cause:** The auth cookie is set with `Secure: true` when
`COOKIE_SECURE=true`, which tells browsers to only transmit the cookie over
HTTPS. When the app is served over plain HTTP (as in a homelab without TLS),
the browser silently discards the cookie — so every page load sees no token
and redirects back to `/login`.

**Fix:** Ensure `COOKIE_SECURE=false` is set in the frontend container (the
default in `values.yaml`). Then rebuild and deploy the frontend image with
the updated `actions/auth.action.ts` that reads `COOKIE_SECURE` instead of
`NODE_ENV`:

```bash
docker build -t 192.168.1.206:30002/colony/colony-frontend:1.0.1 ./frontend
docker push 192.168.1.206:30002/colony/colony-frontend:1.0.1

helm upgrade colony ./helm/colony \
  --namespace colony-app \
  -f my-values.yaml \
  --set frontend.image.tag=1.0.1
```

**Note:** If you ever add HTTPS to the cluster (e.g. via a TLS ingress),
set `frontend.env.cookieSecure: "true"` in your values file so session
cookies are properly protected.
