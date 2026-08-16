# RouteXAI

## AI-Powered Dynamic Logistics Intelligence Platform

**RouteXAI** is an AI-powered last-mile logistics intelligence platform designed to optimize delivery routes, improve ETA accuracy, enhance fleet visibility, and enable intelligent real-time route adaptation.

The platform combines **Google OR-Tools VRPTW, K-Means clustering, A* pathfinding, XGBoost-based ETA prediction, self-learning ML feedback, and hardware-triggered dynamic rerouting** into a unified logistics optimization system.

---

## Key Features

### 🚚 Intelligent Route Optimization

* Vehicle Routing Problem with Time Windows (**VRPTW**) using Google OR-Tools
* K-Means-based delivery clustering
* A*-based shortest-path routing
* Dynamic route recalculation
* Vehicle and delivery constraints
* Hardware-triggered route adaptation

### 🤖 AI & Machine Learning

* XGBoost-based ETA prediction
* Predicted-vs-actual ETA analysis
* ML feedback collection
* Self-learning model retraining pipeline
* ML-powered operational insights

### 📦 Order & Fleet Management

* Manual order creation and management
* CSV and JSON order import
* Order CRUD operations
* Vehicle CRUD operations
* Role-based access control
* Delivery rider management and assignment

### 📊 Analytics & Reporting

* Daily analytics
* Weekly analytics
* Monthly analytics
* Yearly analytics
* Operational performance insights
* ML Insights dashboard
* Predicted-vs-actual ETA analysis
* Report export functionality

### 🔄 Dynamic Rerouting

RouteXAI supports hardware-generated events such as:

* `BLOCK_DETECTED`
* `BLOCK_CLEARED`

When a road blockage is detected, the system can dynamically recalculate the affected vehicle's route using **A* pathfinding**.

---

# System Architecture

```text
                    ┌─────────────────────────┐
                    │      React Frontend     │
                    │ Vite + TypeScript       │
                    │ Tailwind + Leaflet      │
                    └────────────┬────────────┘
                                 │
                              REST API
                                 │
                    ┌────────────▼────────────┐
                    │      FastAPI Backend    │
                    │ Authentication & RBAC   │
                    │ Business Logic           │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
 ┌─────────────────┐   ┌──────────────────┐   ┌─────────────────┐
 │ Route Optimizer │   │ ML ETA Engine    │   │ Dynamic Routing │
 │ OR-Tools VRPTW  │   │ XGBoost          │   │ A*              │
 │ K-Means         │   │ Feedback Loop    │   │ Event Handling  │
 └─────────────────┘   └──────────────────┘   └─────────────────┘
                                 │
                         ┌───────▼────────┐
                         │   PostgreSQL   │
                         │    Database    │
                         └────────────────┘
```

---

# Technology Stack

### Frontend

* React.js
* Vite
* TypeScript
* Tailwind CSS
* React Router
* Axios
* React Leaflet
* Leaflet

### Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* Uvicorn
* JWT Authentication

### Database

* PostgreSQL

### AI & Optimization

* Google OR-Tools
* K-Means Clustering
* A* Pathfinding
* XGBoost
* Scikit-learn

### DevOps

* Docker
* Docker Compose

---

# Quick Start

## Backend

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

python -m seed.seed_data

uvicorn app.main:app --reload --port 8000
```

Backend API documentation:

```text
http://localhost:8000/docs
```

## Frontend

Open a separate terminal:

```bash
cd frontend

npm install

cp .env.example .env

npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# Docker Deployment

RouteXAI includes Docker Compose support for running the application stack together.

```bash
docker compose up --build
```

Services:

| Service               | URL                          |
| --------------------- | ---------------------------- |
| Frontend              | `http://localhost:3000`      |
| Backend API           | `http://localhost:8000`      |
| Swagger Documentation | `http://localhost:8000/docs` |

---

# Real vs. Simulated Components

RouteXAI clearly distinguishes between fully implemented backend functionality, algorithmic approximations, and intentionally simulated analytics.

## Fully Implemented

The following components use actual backend implementations and database interactions:

* JWT authentication
* Role-based authorization
* User management
* Order CRUD
* Vehicle CRUD
* CSV/JSON processing
* OR-Tools VRPTW optimization
* K-Means clustering
* A* pathfinding
* XGBoost model training and inference
* ML feedback and retraining
* Hardware event logging
* Hardware-triggered single-vehicle rerouting
* ML Insights
* Predicted-vs-actual ETA data
* Report export

## Routing Approximation

The current routing implementation calculates estimated road distance using:

```text
Haversine Distance × 1.3 Detour Factor
```

This is a documented approximation because a live road-routing service such as OSRM or Google Directions is not currently integrated.

Therefore, the current implementation should not be interpreted as providing literal road-network distances or live traffic-aware routing.

## Analytics Data

The Analysis page's general chart and summary datasets are intentionally simulated according to the project specification.

The following components use real backend data:

* ML Insights
* Predicted-vs-Actual ETA
* ML prediction results
* Feedback/retraining data

The UI clearly distinguishes these data sources.

---

# Current Development Status

The core RouteXAI platform is functionally implemented and verified through backend testing and live application smoke testing.

The remaining enhancements are primarily focused on production readiness:

* [ ] Implement the 15-minute order-status automatic synchronization job
* [ ] Add the Settings page
* [ ] Complete end-to-end Docker Compose verification
* [ ] Integrate a live road-routing API
* [ ] Integrate real-time traffic data for advanced dynamic routing

---

# Repository Structure

```text
RouteXAI/
│
├── backend/
│   ├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── ml/
│   ├── seed/
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── .env.example
│   └── README.md
│
├── docker-compose.yml
└── README.md
```

---

# Core Intelligence Pipeline

```text
Delivery Orders
       │
       ▼
K-Means Clustering
       │
       ▼
OR-Tools VRPTW
       │
       ▼
Optimized Delivery Routes
       │
       ▼
XGBoost ETA Prediction
       │
       ▼
Real-Time Monitoring
       │
       ├── Normal ───────────────► Continue Route
       │
       └── Block Detected ───────► A* Rerouting
                                      │
                                      ▼
                              Updated Route
                                      │
                                      ▼
                             Delivery Feedback
                                      │
                                      ▼
                              ML Retraining
```

---

## Project Status

**RouteXAI is a functional AI-powered logistics intelligence platform combining route optimization, machine learning, geospatial pathfinding, fleet management, analytics, and dynamic rerouting in a unified full-stack application.**
