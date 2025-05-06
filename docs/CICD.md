# CI / CD for Geospatial-Analytics

| Workflow file              | Trigger                                            | What it does                                                                                                                                                            |
| -------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **build-and-deploy.yml**   | Push to `main` (any path) or manual                | Detect changed `services/**` folders -> build & push Docker images -> Redeploy CloudFormation stacks (`api`, `scraper`, `etl`) with new image URIs (rolling ECS update) |
| **frontend-deploy.yml**    | Push that touches `services/frontend/**` or manual | `npm ci` -> `npm run build` for the React SPA -> Sync build artefacts to the private S3 bucket -> Invalidate CloudFront so new assets are served worldwide              |
| **run-batch-jobs.yml**     | Nightly **03:00 UTC** & manual                     | Uses `ecs run-task` to launch the _scraper_ then the _ETL_ Fargate tasks                                                                                                |
| _future_: test / lint jobs | (add as needed)                                    | Unit tests, linting, etc.                                                                                                                                               |

## Pipeline Flow

```
git push -> GitHub Actions
├─ build-and-deploy (ECR + ECS) ──▶ API online in minutes
├─ frontend-deploy (S3 + CF) ─────▶ SPA live in seconds
└─ nightly batch (scraper → ETL) ─▶ Data refreshed daily
```

### Key Points

1. **Immutable tags** – Containers are tagged with the short commit SHA (`:a1b2c3d`).
2. **Rolling updates** – Updating the CloudFormation stack makes ECS pull the fresh tag and performs a zero-downtime replacement behind the ALB.
3. **Static site** – The React app is a pure S3 + CloudFront deployment; no container rebuild is needed.
4. **Cache busting** – After every upload the workflow issues `create-invalidation /*`, ensuring edge nodes drop cached files quickly.
5. **Least-privilege auth** – Both workflows assume the same GitHub-OIDC IAM role (`github-actions`) that just needs ECR, S3, CloudFront, CloudFormation, and ECS rights.
