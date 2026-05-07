# SSU Room Scanner / Study Room Finder
A cloud-based room occupancy dashboard for Sonoma State University. The app helps students check whether study rooms, classrooms, labs, and lounge spaces are empty or occupied before walking across campus.

The project uses a hybrid cloud architecture:
- **Render.com** hosts the static frontend.
- **AWS API Gateway** exposes the backend API.
- **AWS Lambda** runs the backend logic.
- **Amazon DynamoDB** stores room records and occupancy status.
- **Docker** seeds and optionally simulates room occupancy changes.
- **GitHub Actions** supports CI/CD.
- **IAM** secures Lambda access to DynamoDB using least privilege.

---

## Live URLs

**Frontend**
```text
https://study-room-frontend.onrender.com
```

**API Gateway Base URL**

```text
https://f01fxvetb3.execute-api.us-west-1.amazonaws.com/prod
```

**Rooms API**

```text
https://f01fxvetb3.execute-api.us-west-1.amazonaws.com/prod/rooms
```

---

## Project Purpose

SSU students often waste time walking between buildings looking for an open study space. This project provides a centralized dashboard showing current room availability across campus buildings.

The dashboard displays:

- Room name
- Building
- Floor
- Room type
- Capacity
- Empty / occupied status
- Last updated timestamp

---

## Covered Buildings

The prototype includes room data for major SSU campus buildings, including:

- Salazar Hall
- Darwin Hall
- Stevenson Hall
- Schulz Information Center / Library
- Student Center
- Rachel Carson Hall

---

## Architecture

```text
Student Browser
    |
    | HTTPS
    v
Render Static Frontend
    |
    | fetch()
    v
AWS API Gateway
    |
    | Lambda proxy integration
    v
AWS Lambda
    |
    | boto3
    v
Amazon DynamoDB

Docker Simulator
    |
    | boto3 writes / updates
    v
Amazon DynamoDB
```

---

## Cloud Services Used

| Component | Service | Purpose |
|---|---|---|
| Frontend hosting | Render.com Static Site | Hosts `public/index.html` |
| API routing | AWS API Gateway | Public HTTPS API endpoint |
| Backend compute | AWS Lambda | Handles API requests |
| Database | Amazon DynamoDB | Stores rooms and occupancy status |
| Permissions | AWS IAM | Gives Lambda least-privilege DynamoDB access |
| Containerization | Docker | Seeds and simulates room data |
| CI/CD | GitHub Actions + Render | Validates repo and deploys frontend |
| Logging | Amazon CloudWatch | Stores Lambda logs |

---

## Repository Structure

```text
study-room-finder/
├── public/
│   └── index.html
├── backend/
│   └── lambda_function.py
├── docker/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── seed_and_simulate.py
├── iam/
│   └── iam_policy.json
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── render.yaml
├── package.json
└── README.md
```

---

## Frontend

The frontend is a static HTML, CSS, and JavaScript app located at:

```text
public/index.html
```

It is hosted on Render as a static site.

The frontend calls API Gateway using:

```javascript
const API_URL = "https://f01fxvetb3.execute-api.us-west-1.amazonaws.com/prod";
```

The frontend then fetches room data from:

```javascript
fetch(`${API_URL}/rooms`)
```

Frontend features include:

- Room cards grouped by building
- Empty / occupied badges
- Building filter
- Room type filter
- Status filter
- Summary counts
- Manual refresh button
- Auto-refresh every 60 seconds
- Mobile-friendly layout

---

## Backend

The backend is implemented as an AWS Lambda function.

Lambda function name:

```text
ssu-room-scanner
```

Runtime:

```text
Python 3.x
```

The Lambda function reads from and updates the DynamoDB table:

```text
SSURooms
```

The Lambda function is exposed through AWS API Gateway.

---

## DynamoDB

DynamoDB table name:

```text
SSURooms
```

Primary key:

```text
RoomID
```

Primary key type:

```text
String
```

Example room item:

```json
{
  "RoomID": "SAL-101",
  "Building": "Salazar Hall",
  "BuildingCode": "SAL",
  "Floor": 1,
  "RoomName": "Salazar 101",
  "RoomType": "Study Room",
  "Capacity": 8,
  "Status": "empty",
  "LastUpdated": "2026-05-07T17:45:00Z"
}
```

---

## API Routes

Base URL:

```text
https://f01fxvetb3.execute-api.us-west-1.amazonaws.com/prod
```

| Method | Route | Purpose | Used By |
|---|---|---|---|
| GET | `/rooms` | Returns all rooms | Frontend |
| GET | `/rooms?building=SAL` | Filters rooms by building code | Frontend |
| GET | `/rooms?status=empty` | Filters rooms by availability | Frontend |
| GET | `/rooms/{roomId}` | Returns one room by ID | Frontend / testing |
| GET | `/buildings` | Returns building summary data | Frontend / reporting |
| POST | `/rooms/update` | Updates a room’s occupancy status | Docker simulator |

---

## Example API Response

```json
{
  "rooms": [
    {
      "RoomID": "SAL-101",
      "Building": "Salazar Hall",
      "BuildingCode": "SAL",
      "Floor": 1,
      "RoomName": "Salazar 101",
      "RoomType": "Study Room",
      "Capacity": 8,
      "Status": "empty",
      "LastUpdated": "2026-05-07T17:45:00Z"
    }
  ],
  "count": 1,
  "timestamp": "2026-05-07T17:45:30Z"
}
```

---

## Docker Simulator

Docker is used to seed DynamoDB with room data and optionally simulate occupancy changes.

Docker files are located in:

```text
docker/
```

### Docker Requirements

`docker/requirements.txt`

```text
boto3
botocore[crt]
```

### Build Docker Image

From the `docker/` folder:

```bash
docker build -t ssu-room-simulator .
```

### Seed DynamoDB Once

This seeds room data and exits immediately.

```bash
eval "$(aws configure export-credentials --format env)"

docker run --rm \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
  -e AWS_DEFAULT_REGION=REGION_NAME \
  -e DYNAMODB_TABLE=TABLENAME \
  -e SIMULATE=false \
  ssu-room-simulator
```

### Run Live Simulation

This updates random room statuses every 60 seconds.

```bash
eval "$(aws configure export-credentials --format env)"

docker run --rm \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
  -e AWS_DEFAULT_REGION=REGION_NAME \
  -e DYNAMODB_TABLE=TABLENAME \
  -e SIMULATE=true \
  -e UPDATE_INTERVAL_SECONDS=60 \
  ssu-room-simulator
```

Stop the simulator with:

```text
Ctrl+C
```

---

## AWS CLI Setup

The Docker simulator needs AWS credentials to write to DynamoDB.

Authenticate with AWS:

```bash
aws login
```

Set the correct region:

```bash
aws configure set region us-west-1
```

Verify identity:

```bash
aws sts get-caller-identity
```

Verify region:

```bash
aws configure get region
```

Expected region:

```text
us-west-1
```

---

## IAM Security

Lambda uses an IAM role with least-privilege access.

Role name:

```text
ssu-scanner-lambda-role
```

Attached managed policy:

```text
AWSLambdaBasicExecutionRole
```

Inline DynamoDB policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDBRoomAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-west-1:*:table/SSURooms"
    }
  ]
}
```

This allows Lambda to read and update only the DynamoDB table required by the app.

---

## CORS

The Lambda/API response should restrict browser access to the Render frontend:

```python
CORS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "https://study-room-frontend.onrender.com",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
}
```


---

## Cost Controls

This project is designed to remain very low-cost.

Cost-control decisions:

- Render is used only for static frontend hosting.
- AWS API Gateway is used only for lightweight API requests.
- Lambda uses low memory and short execution time.
- Lambda provisioned concurrency is disabled.
- DynamoDB uses on-demand capacity.
- DynamoDB DAX is not enabled.
- DynamoDB global tables are not enabled.
- DynamoDB streams are not enabled.
- API Gateway caching is not enabled.
- CloudWatch log retention is limited to 7 days.
- Docker simulation is disabled by default.
- The simulator is stopped after testing or demo use.
- AWS Budget alerts are configured.

Expected AWS cost for classroom/demo usage is less than $1/month.

---

## CloudWatch Logging

Lambda logs are stored in CloudWatch.

Log group:

```text
/aws/lambda/ssu-room-scanner
```

Recommended retention:

```text
7 days
```

This keeps enough logs for debugging while limiting long-term storage cost.

---

## Render Deployment

Render is used only for static frontend hosting.

`render.yaml` should define the frontend static site:

```yaml
services:
  - type: web
    name: study-room-frontend
    env: static
    region: oregon
    branch: main
    buildCommand: echo "Static frontend - no build step required"
    staticPublishPath: public
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
```

---

## GitHub Actions

GitHub Actions is used to validate and deploy the project.

Workflows:

```text
ci.yml
cd.yml
```

CI checks should verify:

- `public/index.html` exists
- `render.yaml` points to `public`
- The frontend contains the API Gateway URL

CD should trigger or verify the Render frontend deployment.

---

## Local Development

### Run the Frontend Locally

Because this is a static frontend, you can serve it locally with Python:

```bash
cd public
python3 -m http.server 8080
```

Then open:

```text
http://localhost:8080
```

The local frontend will still call the deployed AWS API Gateway URL.

---

## Demo Steps

1. Open the Render frontend:

```text
https://study-room-frontend.onrender.com
```

2. Show room cards and filters.

3. Open API Gateway route:

```text
https://f01fxvetb3.execute-api.us-west-1.amazonaws.com/prod/rooms
```

4. Run Docker simulation:

```bash
eval "$(aws configure export-credentials --format env)"

docker run --rm \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
  -e AWS_DEFAULT_REGION=us-west-1 \
  -e DYNAMODB_TABLE=SSURooms \
  -e SIMULATE=true \
  -e UPDATE_INTERVAL_SECONDS=60 \
  ssu-room-simulator
```

5. Refresh the frontend and show updated room statuses.

6. Stop the simulator with:

```text
Ctrl+C
```

---

## Course Concept Mapping

| Course Concept | Project Implementation |
|---|---|
| Public cloud | AWS and Render |
| PaaS | Render static site hosting |
| FaaS / serverless | AWS Lambda |
| API Gateway pattern | AWS API Gateway routes requests to Lambda |
| Managed database | DynamoDB |
| Containerization | Docker room seeder/simulator |
| IAM security | Lambda role with least-privilege DynamoDB policy |
| CI/CD | GitHub Actions and Render deployment |
| Scalability | API Gateway, Lambda, and DynamoDB scale automatically |
| Cost analysis | Budget alerts and low-cost serverless settings |
| Observability | CloudWatch Lambda logs |

---

## Known Limitations

This is a classroom prototype. Current limitations include:
- Room occupancy is simulated, not connected to real sensors.
- Authentication is not required for the public room dashboard.
- Admin-only create/delete routes are intentionally not exposed.
- The Docker simulator must be run manually.
- Room data is a representative sample, not a complete official SSU room database.

---

## Future Improvements

Possible future enhancements:
- Add Firebase Google login with SSU email restriction.
- Add admin-only room management routes.
- Connect to real classroom scheduling or sensor data.
- Add CloudFront or custom domain.
- Add more complete campus room data.
- Add historical occupancy analytics.
- Add accessibility testing.
- Add automated backend deployment to Lambda through GitHub Actions.
- Add unit tests for Lambda route handlers.

---

## Academic Integrity Disclosure

This project was built as a CS 385 cloud computing project. Generative AI tools were used to assist with frontend development, planning, debugging, and documentation. The final implementation decisions, AWS configuration, testing, and deployment were completed and verified by our group.

---

## Final Status
Current project status:
- Render frontend deployed.
- API Gateway deployed.
- Lambda backend working.
- DynamoDB table connected.
- Docker seed/simulator working.
- Cost controls implemented.
- Frontend connected to live AWS backend.