# Deploying to AWS

This app is a standard containerized Flask service, so it fits any of AWS's
container-hosting options. Two straightforward paths:

## Option A — AWS App Runner (simplest)

App Runner builds and runs a container from source or an image with almost
no infrastructure to manage — a good fit for a small API like this one.

1. Push this repo to GitHub.
2. In the AWS Console, open **App Runner &rarr; Create service**.
3. Source: **Source code repository** &rarr; connect your GitHub repo.
4. Deployment settings: automatic deploys on push (optional).
5. Build settings: App Runner detects the `Dockerfile` automatically, or set:
   - Build command: *(none — Docker build handles it)*
   - Start command: *(none — the Dockerfile's `CMD` handles it)*
   - Port: `8080`
6. Service settings: 0.25 vCPU / 0.5 GB memory is plenty for this API.
7. Deploy. App Runner gives you an HTTPS URL immediately.

## Option B — Elastic Beanstalk (Docker platform)

1. Install the EB CLI: `pip install awsebcli`
2. From this project's directory:
   ```bash
   eb init -p docker freight-rate-api --region us-east-1
   eb create freight-rate-api-env
   ```
3. Elastic Beanstalk builds the Dockerfile, provisions a load balancer +
   auto scaling group, and gives you a public URL.
4. Subsequent deploys: `eb deploy`

## Option C — Plain EC2 / Docker (manual, cheapest for a demo)

```bash
docker build -t freight-rate-api .
docker run -d -p 80:8080 --restart unless-stopped freight-rate-api
```

Point a domain or Elastic IP at the instance and you're live.

## Environment & health checks

- The API is stateless (no database), so it scales horizontally with zero
  configuration — any number of instances behind a load balancer is fine.
- `/health` returns `200 {"status": "ok"}` — use it as the health-check path
  in App Runner, an ALB target group, or an ECS task definition.
- No secrets or environment variables are required for the app to run.

## Why this wasn't deployed live

Actually standing up the AWS resources requires an AWS account and billable
infrastructure, which isn't something to spin up without you in the loop.
Everything above is copy-pasteable — App Runner is the fastest path (a few
minutes, first 12 months are within the AWS free tier for this size of app).
