# 🚀 Complete Deployment Guide

## Option 1: GitHub Actions (Recommended - 5 min setup)

### Step 1: Add Workflow File

Create `.github/workflows/autonomous-agent.yml`:

```yaml
name: Autonomous GitHub Agent

on:
  workflow_dispatch:
  schedule:
    - cron: '0 9 * * MON-FRI'  # 9 AM weekdays
  issues:
    types: [opened, edited]
  pull_request:
    types: [opened, synchronize]

jobs:
  agent:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: labgadget015-dotcom/autonomous-github-agent@v1.0.0
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          actions: |
            - triage-issues
            - review-pr
            - generate-tests
            - update-docs
          config: |
            {
              "ai_model": "gpt-4-turbo",
              "auto_label": true,
              "auto_assign": true,
              "cache_enabled": true,
              "batch_size": 10
            }
```

### Step 2: Add Secrets

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add two secrets:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `GITHUB_TOKEN`: Already available by default

### Step 3: Test

1. Go to **Actions** tab
2. Click **Autonomous GitHub Agent**
3. Click **Run workflow**
4. Watch it process your repo

## Option 2: Docker Deployment (10 min setup)

### Step 1: Create Docker Compose File

`docker-compose.yml`:

```yaml
version: '3.8'
services:
  agent:
    image: labgadget015/autonomous-github-agent:latest
    container_name: autonomous-agent
    environment:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      REPO: ${GITHUB_REPOSITORY}
      ACTIONS: "triage-issues,review-pr,generate-tests"
      BATCH_SIZE: "10"
      CACHE_ENABLED: "true"
      LOG_LEVEL: "info"
    volumes:
      - ./logs:/app/logs
      - ./cache:/app/cache
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Step 2: Create `.env` File

```bash
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_key_here
GITHUB_REPOSITORY=org/repo
```

### Step 3: Deploy

```bash
docker-compose up -d

# View logs
docker-compose logs -f agent

# Stop
docker-compose down
```

## Option 3: Kubernetes Deployment (30 min setup)

### Step 1: Create Kubernetes Secret

```bash
kubectl create secret generic autonomous-agent-secrets \
  --from-literal=github_token=$GITHUB_TOKEN \
  --from-literal=openai_api_key=$OPENAI_API_KEY
```

### Step 2: Create Deployment Manifest

`autonomous-agent-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: autonomous-agent
  labels:
    app: autonomous-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: autonomous-agent
  template:
    metadata:
      labels:
        app: autonomous-agent
    spec:
      containers:
      - name: agent
        image: labgadget015/autonomous-github-agent:latest
        imagePullPolicy: Always
        env:
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: autonomous-agent-secrets
              key: github_token
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: autonomous-agent-secrets
              key: openai_api_key
        - name: REPO
          value: "org/repo"
        - name: BATCH_SIZE
          value: "10"
        - name: CACHE_ENABLED
          value: "true"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Step 3: Deploy to Kubernetes

```bash
kubectl apply -f autonomous-agent-deployment.yaml

# Monitor
kubectl logs -f deployment/autonomous-agent

# Check status
kubectl get deployment autonomous-agent
```

## Option 4: AWS Lambda Deployment (20 min setup)

### Step 1: Create Lambda Function

```bash
# Clone function code
git clone https://github.com/labgadget015-dotcom/autonomous-github-agent.git
cd autonomous-github-agent/aws-lambda

# Install dependencies
pip install -r requirements.txt -t package/

# Create deployment package
cd package && zip -r ../function.zip . && cd ..
zip -g function.zip lambda_handler.py

# Deploy
aws lambda create-function \
  --function-name autonomous-agent \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-role \
  --handler lambda_handler.handler \
  --zip-file fileb://function.zip \
  --timeout 900 \
  --memory-size 512 \
  --environment "Variables={GITHUB_TOKEN=$GITHUB_TOKEN,OPENAI_API_KEY=$OPENAI_API_KEY}"
```

### Step 2: Create EventBridge Rule

```bash
aws events put-rule \
  --name autonomous-agent-schedule \
  --schedule-expression "cron(0 9 MON-FRI ? *)" \
  --state ENABLED

aws events put-targets \
  --rule autonomous-agent-schedule \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:autonomous-agent","RoleArn"="arn:aws:iam::ACCOUNT_ID:role/eventbridge-role"
```

## Performance Tuning

### Optimization Checklist

- [ ] Enable caching: `cache_enabled: true`
- [ ] Set batch size: `batch_size: 10-20`
- [ ] Use GPT-4 Turbo (90% cheaper): `model: gpt-4-turbo`
- [ ] Schedule off-peak: `cron: '0 2 * * *'` (2 AM)
- [ ] Limit scope: `max_repos: 5` (start small)
- [ ] Monitor costs: Check OpenAI dashboard weekly

### Cost Optimization

| Configuration | API Calls/Day | Cost/Month |
|---|---|---|
| Default | 1,000 | $150 |
| Optimized | 200 | $30 |
| Enterprise | 5,000 | $400/mo flat |

## Monitoring & Alerts

### CloudWatch Dashboard (AWS)

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name autonomous-agent-failures \
  --alarm-description "Alert on agent failures" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

### GitHub Workflow Notifications

Add to your workflow:

```yaml
- name: Notify on Failure
  if: failure()
  uses: actions/github-script@v6
  with:
    script: |
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: '💩 Agent error: Check logs'
      })
```

## Troubleshooting

### Agent Not Running

1. Check logs: `docker-compose logs agent`
2. Verify tokens: `echo $GITHUB_TOKEN`
3. Test API: `curl -H "Auth: Bearer $GITHUB_TOKEN" https://api.github.com/user`

### High Costs

1. Check batch size: reduce `batch_size` from 20 to 5
2. Enable caching: `cache_enabled: true`
3. Use GPT-3.5: `model: gpt-3.5-turbo` (cheaper)
4. Schedule less frequently: change `cron` schedule

### Performance Issues

1. Increase memory: `memory_size: 1024`
2. Enable parallel: `parallel_tasks: 5`
3. Reduce timeout: `timeout: 300` (5 min)

## Production Checklist

- [ ] Secrets configured correctly
- [ ] Rate limiting set appropriately
- [ ] Cost monitoring enabled
- [ ] Error notifications configured
- [ ] Backup of important data
- [ ] Regular testing scheduled
- [ ] Documentation updated
- [ ] Team trained on system

## Support

- Issues: https://github.com/labgadget015-dotcom/autonomous-github-agent/issues
- Docs: https://docs.autonomous-agent.dev
- Email: support@autonomous-agent.dev
