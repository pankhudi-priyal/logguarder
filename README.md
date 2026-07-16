# LogGuard – Automated Log Monitoring and Incident Detection System


A production-style DevOps project that demonstrates centralized log collection, real-time monitoring, CI/CD automation, and GitOps-based deployment using Kubernetes and ArgoCD.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        GitHub Repo                          │
│  Push → GitHub Actions CI/CD → Docker Hub                   │
│                    │                                         │
│                    └── updates k8s/app/deployment.yml       │
└────────────────────────────┬────────────────────────────────┘
                             │ GitOps sync
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Minikube / Kubernetes                      │
│                                                              │
│  ┌─────────────┐    logs     ┌──────────┐                   │
│  │  Flask App  │ ──────────► │ Filebeat │                   │
│  │  :5001      │             └────┬─────┘                   │
│  └──────┬──────┘                  │ beats                   │
│         │ /metrics                ▼                          │
│         │              ┌──────────────────┐                 │
│  ┌──────▼──────┐       │    Logstash      │                 │
│  │ Prometheus  │       │  (parse/filter)  │                 │
│  │  :9090      │       └────────┬─────────┘                 │
│  └──────┬──────┘                │                           │
│         │                       ▼                           │
│  ┌──────▼──────┐       ┌─────────────────┐                 │
│  │   Grafana   │       │ Elasticsearch   │                  │
│  │  :3000      │       │    :9200        │                  │
│  └─────────────┘       └────────┬────────┘                  │
│                                 │                           │
│                        ┌────────▼────────┐                  │
│                        │    Kibana       │                  │
│                        │    :5601        │                  │
│                        └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Tools & Technologies

| Category | Tool | Purpose |
|---|---|---|
| Application | Python / Flask | REST API generating structured logs |
| Containerization | Docker / Docker Compose | Local development environment |
| Orchestration | Kubernetes (Minikube) | Production-style deployment |
| GitOps / CD | ArgoCD | Auto-sync k8s from Git |
| Log Collection | Filebeat | Ships container logs from Kubernetes nodes |
| Log Processing | Logstash | Parses, filters, and enriches logs |
| Log Storage | Elasticsearch | Indexes and stores log data |
| Log Visualization | Kibana | Dashboards for log analysis |
| Metrics | Prometheus | Scrapes `/metrics` from Flask app |
| Metrics Dashboards | Grafana | Request rate, error rate, response time |
| CI/CD | GitHub Actions | Automated test → scan → build → deploy |
| Security Scan | Trivy | Container image vulnerability scanning |
| Code Quality | SonarQube (SonarCloud) | Static code analysis |
| Image Registry | Docker Hub | Stores and distributes container images |
| Secrets | GitHub Secrets + k8s Secrets | Secure credential management |

---

## CI/CD Flow

```
git push → GitHub Actions
    │
    ├── 1. pytest (unit tests + coverage)
    ├── 2. SonarCloud (static analysis)
    ├── 3. docker build
    ├── 4. Trivy scan (CRITICAL/HIGH CVEs block the pipeline)
    └── 5. docker push to Docker Hub
            │
            └── update k8s/app/deployment.yml image tag
                    │
                    └── ArgoCD detects change → auto-deploys to Minikube
```

---

## Quick Start — Docker Compose (Local)

```bash
# Start the full stack
docker compose up --build

# Generate logs
curl http://localhost:5001/
curl http://localhost:5001/order
curl http://localhost:5001/login

# Run tests
app/venv/bin/pytest app/tests/ -v
```

| Service | URL |
|---|---|
| Flask App | http://localhost:5001 |
| Kibana | http://localhost:5601 |
| Grafana | http://localhost:3000 (admin/admin) |
| Prometheus | http://localhost:9090 |

---

## Kubernetes Setup (Minikube)

### Prerequisites
```bash
brew install minikube kubectl
minikube start --memory=4096 --cpus=2
```

### Deploy all manifests
```bash
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/secrets.yml
kubectl apply -f k8s/elasticsearch/
kubectl apply -f k8s/logstash/
kubectl apply -f k8s/kibana/
kubectl apply -f k8s/filebeat/
kubectl apply -f k8s/prometheus/
kubectl apply -f k8s/grafana/
kubectl apply -f k8s/app/
```

### Access services via Minikube
```bash
minikube service logguard-app -n logguard
minikube service kibana -n logguard
minikube service grafana -n logguard
minikube service prometheus -n logguard
```

### Check pod status
```bash
kubectl get pods -n logguard
kubectl logs -n logguard deployment/logguard-app
```

---

## ArgoCD Setup

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=120s

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Edit k8s/argocd/application.yml — replace YOUR_GITHUB_USERNAME
# Then apply the ArgoCD Application:
kubectl apply -f k8s/argocd/application.yml
```

ArgoCD will now watch the `k8s/` folder and auto-deploy on every git push.

---

## GitHub Secrets Required

Go to your repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|---|---|
| `DOCKER_USERNAME` | Your Docker Hub username |
| `DOCKER_PASSWORD` | Your Docker Hub access token |
| `SONAR_TOKEN` | Token from sonarcloud.io |

---

## Kibana Dashboard Setup

1. Open http://localhost:5601
2. Menu → Stack Management → Data Views → Create data view
3. Pattern: `logguard-*`, time field: `@timestamp`
4. Go to Discover to query logs by `level`, `log_message`, `service`

**Useful KQL queries:**
```
level: "ERROR"
level: "WARNING"
log_message: *payment*
```

---

## Grafana Dashboard

The dashboard auto-loads from `grafana/dashboards/logguard-dashboard.json` and shows:
- Total request count
- Error rate (5xx)
- Request rate per endpoint (req/s)
- Response time P95
- HTTP status code breakdown
- Error % gauge with threshold alerts

---

## Project Structure

```
logguarder/
├── .github/workflows/ci.yml     # CI/CD pipeline
├── app/
│   ├── app.py                   # Flask application
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/test_app.py        # 6 unit tests
├── elk/
│   └── logstash/pipeline/       # Logstash config (Docker Compose)
├── k8s/                         # Kubernetes manifests
│   ├── app/
│   ├── elasticsearch/
│   ├── logstash/
│   ├── kibana/
│   ├── filebeat/
│   ├── prometheus/
│   ├── grafana/
│   └── argocd/application.yml
├── prometheus/prometheus.yml
├── grafana/
│   ├── provisioning/            # Auto-loaded datasource + dashboard config
│   └── dashboards/              # Grafana dashboard JSON
├── sonar-project.properties     # SonarQube config
└── docker-compose.yml
```
