# 🏗️ PRODUCTION INFRASTRUCTURE SETUP

**VERSION:** 1.0.0
**LAST UPDATED:** 2026-02-17
**STATUS:** 🟢 ACTIVE IN PRODUCTION

---

## 📋 OVERVIEW

**Production VPS setup running multiple projects on Kubernetes with external Nginx as reverse proxy.**

**Active Projects:**
- ✅ **surgricalswale** (Healthcare platform)
- ✅ **lovepoet** (Social platform)
- ✅ **techdeveloper** (Developer platform)

**Infrastructure Type:** Three-Tier Routing Architecture

---

## 🌐 THREE-TIER ROUTING ARCHITECTURE

### **Tier 1: Outer Nginx (The Gatekeeper) - VPS Level**

**Location:** Ubuntu VPS (System-level Nginx)
**Role:** Entry Point & SSL Termination
**Ports:** 80 (HTTP), 443 (HTTPS)

**Routing Logic:**
```nginx
# Jenkins (running outside K8s)
jenkins.techdeveloper.in → localhost:8080

# All other services (inside K8s)
api.techdeveloper.in     → K8s NodePort 31360
eureka.techdeveloper.in  → K8s NodePort 31360
kibana.techdeveloper.in  → K8s NodePort 31360
[any-other-domain]       → K8s NodePort 31360
```

**Key Features:**
- ✅ SSL/TLS termination via Certbot
- ✅ Automatic HTTPS redirect
- ✅ Single entry point for all traffic
- ✅ Separates Jenkins (non-K8s) from microservices (K8s)

**Configuration Pattern:**
```bash
# Auto-generated via tee command
cat <<EOF | sudo tee /etc/nginx/sites-available/domain.conf
server {
    server_name domain.techdeveloper.in;

    location / {
        proxy_pass http://localhost:31360;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/domain.techdeveloper.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/domain.techdeveloper.in/privkey.pem;
}

server {
    listen 80;
    server_name domain.techdeveloper.in;
    return 301 https://$server_name$request_uri;
}
EOF
```

---

### **Tier 2: Nginx Ingress Controller (The Traffic Police) - K8s Level**

**Location:** Kubernetes Pod
**Role:** Domain-based routing inside K8s cluster
**Access:** Via NodePort 31360

**How It Works:**
1. Receives traffic from Outer Nginx on port 31360
2. Inspects `Host` header (e.g., `kibana.techdeveloper.in`)
3. Routes to appropriate Kubernetes Service
4. No need to restart Outer Nginx for new apps

**Deployment:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
spec:
  type: NodePort
  ports:
  - name: http
    port: 80
    targetPort: 80
    nodePort: 31360
    protocol: TCP
  - name: https
    port: 443
    targetPort: 443
    nodePort: 31361
    protocol: TCP
```

---

### **Tier 3: Ingress Resources (The Map) - App Level**

**Location:** Kubernetes YAML manifests
**Role:** Define routing rules per application

**Example - Kibana:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kibana-ingress
  namespace: elastic-stack
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: kibana.techdeveloper.in
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: kibana
            port:
              number: 5601
```

**Example - API Gateway:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-gateway-ingress
  namespace: techdeveloper
spec:
  ingressClassName: nginx
  rules:
  - host: api.techdeveloper.in
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: techdeveloper-gateway
            port:
              number: 8085
```

---

## 🔍 ELASTIC STACK (ELK) HARDENING

**Version:** Kibana 9.2.3, Elasticsearch 9.2.3

### **Critical Fixes Applied:**

**1. Resource Scaling (Kibana Migration Issue)**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kibana
spec:
  template:
    spec:
      containers:
      - name: kibana
        resources:
          requests:
            memory: "4Gi"
            cpu: "1000m"
          limits:
            memory: "6Gi"
            cpu: "2000m"
```

**Why:** Kibana migration is memory-intensive. Default resources cause OOMKilled.

---

**2. Persistent Storage (PVC)**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: kibana-data
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: elasticsearch-data
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
```

**Why:** Without PVC, logs are lost on pod restart.

---

**3. Security & RBAC (Critical Fix)**

**Problem:** `security_exception: action [indices:admin/create] is unauthorized`

**Root Cause:** Kibana needs permission to create system indices (`.kibana`, `.apm`, etc.)

**Solution:**
```bash
# Create custom role in Elasticsearch
curl -X POST "http://elasticsearch:9200/_security/role/kibana_system_indices" \
-H 'Content-Type: application/json' -d'
{
  "indices": [
    {
      "names": [".kibana*", ".apm*", ".fleet*", ".security*"],
      "privileges": ["all"],
      "allow_restricted_indices": true
    }
  ]
}'

# Assign role to kibana_system user
curl -X POST "http://elasticsearch:9200/_security/user/kibana_system/_password" \
-H 'Content-Type: application/json' -d'
{
  "password": "your-password"
}'
```

**Key:** `allow_restricted_indices: true` is MANDATORY for system indices.

---

## 🚀 AUTOMATION & IDEMPOTENCY

**Principle:** All configurations are idempotent - safe to rerun.

### **Nginx Configuration Automation**
```bash
# Idempotent nginx config creation
cat <<EOF | sudo tee /etc/nginx/sites-available/${DOMAIN}.conf
[nginx config here]
EOF

# Enable site (idempotent)
sudo ln -sf /etc/nginx/sites-available/${DOMAIN}.conf /etc/nginx/sites-enabled/

# Test & reload
sudo nginx -t && sudo systemctl reload nginx
```

### **Kubernetes Apply Pattern**
```bash
# Always use apply (not create)
kubectl apply -f deployment.yaml

# Apply is idempotent
kubectl apply -f ingress.yaml
```

---

## 📋 ADDING NEW PUBLIC APP (STEP-BY-STEP)

**Example:** Adding `frontend.techdeveloper.in`

### **Step 1: DNS Configuration**
```
Type: A
Name: frontend
Value: [VPS_PUBLIC_IP]
TTL: 3600
```

### **Step 2: Outer Nginx Configuration**
```bash
# Create nginx config
cat <<EOF | sudo tee /etc/nginx/sites-available/frontend.techdeveloper.in.conf
server {
    server_name frontend.techdeveloper.in;

    location / {
        proxy_pass http://localhost:31360;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    listen 80;
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/frontend.techdeveloper.in.conf /etc/nginx/sites-enabled/

# Test & reload
sudo nginx -t && sudo systemctl reload nginx
```

### **Step 3: SSL Certificate (Certbot)**
```bash
# Auto-configure SSL
sudo certbot --nginx -d frontend.techdeveloper.in

# Certbot will:
# 1. Generate SSL certificate
# 2. Update nginx config with SSL
# 3. Add HTTP → HTTPS redirect
```

### **Step 4: Kubernetes Ingress**
```yaml
# frontend-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend-ingress
  namespace: techdeveloper
spec:
  ingressClassName: nginx
  rules:
  - host: frontend.techdeveloper.in
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

```bash
kubectl apply -f frontend-ingress.yaml
```

### **Step 5: Verify**
```bash
# Check ingress
kubectl get ingress -n techdeveloper

# Check from outside
curl -I https://frontend.techdeveloper.in

# Should return 200 OK
```

---

## 🛠️ TROUBLESHOOTING GUIDE

### **Issue: 404 Not Found on New Domain**

**Symptoms:**
- Outer Nginx works (SSL shows correctly)
- But application returns 404

**Diagnosis:**
```bash
# Check ingress
kubectl get ingress -A

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Check service
kubectl get svc -n [namespace]
```

**Fix:**
1. Verify Ingress YAML has correct `host` and `service` name
2. Ensure `ingressClassName: nginx` is set
3. Check service is running: `kubectl get pods -n [namespace]`

---

### **Issue: Kibana Migration Fails**

**Symptoms:**
```
[Kibana][migrations] Timeout occurred while waiting for...
```

**Diagnosis:**
```bash
# Check Kibana resources
kubectl top pod -n elastic-stack

# Check Kibana logs
kubectl logs -n elastic-stack deployment/kibana --tail=100
```

**Fix:**
1. Increase Kibana memory to 6Gi
2. Increase CPU to 2 cores
3. Restart Kibana pod
```bash
kubectl patch deployment kibana -n elastic-stack -p '{"spec":{"template":{"spec":{"containers":[{"name":"kibana","resources":{"limits":{"memory":"6Gi","cpu":"2000m"},"requests":{"memory":"4Gi","cpu":"1000m"}}}]}}}}'

kubectl rollout restart deployment/kibana -n elastic-stack
```

---

### **Issue: Elasticsearch security_exception**

**Symptoms:**
```
security_exception: action [indices:admin/create] is unauthorized for user [kibana_system]
```

**Diagnosis:**
```bash
# Check Elasticsearch roles
curl -X GET "http://elasticsearch:9200/_security/role/kibana_system"
```

**Fix:**
Create role with `allow_restricted_indices: true` (see Security & RBAC section above)

---

## 📊 COMPONENT OVERVIEW TABLE

| Component | Location | Role | Access | Port |
|-----------|----------|------|--------|------|
| **Outer Nginx** | VPS OS | SSL & Entry Point | Public IP | 80, 443 |
| **Ingress Controller** | K8s Pod | Internal Routing | localhost | 31360 |
| **Service** | K8s Object | Pod Grouping | Cluster IP | varies |
| **Pod** | K8s Object | Application | Container Port | varies |
| **Jenkins** | VPS (non-K8s) | CI/CD | localhost | 8080 |
| **Kibana** | K8s Pod | Log Visualization | Cluster IP | 5601 |
| **Elasticsearch** | K8s Pod | Log Storage | Cluster IP | 9200 |

---

## 🔐 SECURITY BEST PRACTICES

**1. No Direct Port Exposure**
- ❌ Never expose application ports directly to internet
- ✅ Always route through Nginx (SSL + security headers)

**2. Namespace Isolation**
```bash
# Each project in separate namespace
kubectl create namespace surgricalswale
kubectl create namespace lovepoet
kubectl create namespace techdeveloper
```

**3. Resource Limits**
```yaml
# Always set limits to prevent resource exhaustion
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

**4. SSL Everywhere**
- ✅ All domains MUST have SSL (via Certbot)
- ✅ Force HTTPS redirect in Outer Nginx

---

## 🎯 WHY THIS ARCHITECTURE IS BEST

| Benefit | Explanation |
|---------|-------------|
| **Separation** | Jenkins and K8s coexist without conflicts |
| **Security** | Real app ports never exposed to internet |
| **Scalability** | Add 100 apps with just Ingress YAML |
| **SSL Automation** | Certbot handles all SSL renewals |
| **Zero Downtime** | New apps don't require Nginx restart |
| **Idempotency** | Safe to rerun all configurations |

---

## 📖 QUICK REFERENCE COMMANDS

**Check Ingress:**
```bash
kubectl get ingress -A
```

**Check Services:**
```bash
kubectl get svc -A
```

**Check Pods:**
```bash
kubectl get pods -A
```

**Ingress Controller Logs:**
```bash
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller --tail=50 -f
```

**Test Nginx Config:**
```bash
sudo nginx -t
```

**Reload Nginx:**
```bash
sudo systemctl reload nginx
```

**Get SSL (Certbot):**
```bash
sudo certbot --nginx -d domain.techdeveloper.in
```

**Apply K8s Resource:**
```bash
kubectl apply -f resource.yaml
```

---

## 📝 MAINTENANCE NOTES

**Certbot Auto-Renewal:**
- ✅ Certbot timer is enabled by default
- ✅ Auto-renews certificates 30 days before expiry
- ✅ Check: `sudo systemctl status certbot.timer`

**Nginx Config Backup:**
```bash
# Before major changes
sudo cp -r /etc/nginx/sites-available /etc/nginx/sites-available.backup.$(date +%Y%m%d)
```

**K8s Resource Backup:**
```bash
# Export all resources
kubectl get all -A -o yaml > k8s-backup-$(date +%Y%m%d).yaml
```

---

**END OF DOCUMENT**
