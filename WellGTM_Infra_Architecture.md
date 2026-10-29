# Infrastructure Architecture Specification: WellGTM Platform

This document outlines the enterprise-grade production infrastructure configuration for the **WellGTM Market Intelligence Platform**, designed to fulfill the *AI Agent Completeness* and *Deployment & Maintenance Maturity* tracks of the Lotte AX Challenge 2026.

---

## 1. Global Infrastructure Topology Blueprint

The platform uses a fully decoupled, cloud-native microservice topology. The user interface layer is completely separated from the high-compute AI/ML nodes, ensuring asynchronous execution and isolated resource scaling.

```
                  [ PUBLIC CLOUD WAN / USER ACCESS ]
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼ (HTTPS / Content Delivery Network)              ▼ (HTTPS / Secure Gateway)
┌─────────────────────────────────┐               ┌─────────────────────────────────┐
│       FRONTEND UI HOSTING       │               │      COMPUTATIONAL BACKEND      │
│  - Engine: React / Next.js      │               │  - Engine: FastAPI ASGI Server  │
│  - Platform: GitHub / Vercel    │               │  - Platform: Render / AWS EC2   │
│  - Edge: Global CDN Caching     │               │  - Compute: Multi-Core CPU/RAM  │
└─────────────────────────────────┘               └────────────────┬────────────────┘
                                                                   │
         ┌─────────────────────────────────────────────────────────┴─────────┐
         ▼ (Secure Local Ingestion Channels)                                 ▼ (Vector Inbound Context)
┌─────────────────────────────────┐                               ┌─────────────────────────────────┐
│     AUTOMATED INGESTION CRON    │                               │        VECTOR DB STORE          │
│  - Engine: Asynchronous Workers │                               │  - Engine: ChromaDB Instance    │
│  - Action: API Sync at 02:00KST │                               │  - Storage: Persistent Block    │
│  - Target: Trade & Buzz Data    │                               │  - Context: Global Trade Laws   │
└─────────────────────────────────┘                               └─────────────────────────────────┘
```

---

## 2. Infrastructure Layer Breakdown

### 2.1 Presentation & Interface Layer (Frontend UI)
*   **Deployment Target:** Vercel Production Environment or GitHub Pages static asset distribution channels.
*   **Networking & Edge Operations:** Automatic provisioning of global Edge Content Delivery Networks (CDNs) with integrated SSL/TLS certificate management.
*   **Scaling Properties:** Serverless static file hosting. Scale capacity changes automatically based on spikes in daily incoming traffic without needing server hardware provisioning.

### 2.2 Computational Core Layer (Backend API Engine)
*   **Deployment Target:** Render Web Service container or AWS EC2 compute node instance.
*   **Runtime Environment:** Dockerized Linux container utilizing Python 3.11 with an asynchronous Uvicorn ASGI production server gateway interface.
*   **Resource Allocation Baseline:** 
    *   CPU: 2 vCPUs minimum to handle asynchronous API request mapping and multithreaded calculation execution.
    *   RAM: 4GB minimum to maintain standard in-memory Pandas dataframe matrices and host the Prophet time-series models.

### 2.3 Knowledge Base & Vector Core (Context Store)
*   **Deployment Target:** Persistent block storage volumes attached directly to the computational instance.
*   **Database Engine:** ChromaDB or standalone LanceDB vector database instance.
*   **Indexing Properties:** Unstructured customs documents and international trade policies are broken down into chunk structures, indexed via OpenAI `text-embedding-3-large` models, and cached locally to prevent network performance lag.

---

## 3. DevOps Engine: Production Docker Configuration

To guarantee exact environments across *Development*, *Testing*, and *Deployment* pipelines, the following standalone configuration coordinates the cloud build operations.

```dockerfile
# =========================================================================
# PRODUCTION DOCKERFILE FOR WELLGTM BACKEND CORE
# =========================================================================

# Step 1: Initialize baseline python runtime environment
FROM python:3.11-slim

# Step 2: Establish strict system environment controls
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Step 3: Configure isolated secure runtime directory path
WORKDIR /app

# Step 4: Install baseline system dependencies for compilation libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Step 5: Isolate dependency lists and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Step 6: Transfer production runtime source files into image container
COPY . .

# Step 7: Create a non-privileged system user account for security isolation
RUN useradd -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

# Step 8: Expose server access ports to internal web networks
EXPOSE 8000

# Step 9: Launch asynchronous Uvicorn cluster server under production flags
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## 4. Operational Automation Pipeline (Cron & Ingestion Architecture)

To maintain data recency without manual human maintenance, a daily automated execution scheduler is wired directly into the runtime OS container:

```
                  [ CHRONOLOGICAL CRON TRIGGER (02:00 KST) ]
                                      │
                                      ▼
                   ┌──────────────────────────────────────┐
                   │ Async Data Extraction Engine Initiated│
                   └──────────────────┬───────────────────┘
                                      │
         ┌────────────────────────────┴────────────────────────────┐
         ▼ (Fetch Trade Vectors)                                   ▼ (Fetch Consumption Trends)
┌─────────────────────────────────┐                       ┌─────────────────────────────────┐
│       UN Comtrade API Logs      │                       │        Google Trends API        │
│  - HS Codes: 1704, 1806, 1905   │                       │  - Target: Regional Buzz Volume │
└────────────────┬────────────────┘                       └────────────────┬────────────────┘
                 │                                                         │
                 └────────────────────────────┬────────────────────────────┘
                                              ▼
                   ┌──────────────────────────────────────┐
                   │  Vector Normalization & Ingestion    │
                   │  - Executes Multi-Criteria Matrices  │
                   │  - Automatically Updates DB Cache    │
                   └──────────────────┬───────────────────┘
                                      │
                                      ▼
                   ┌──────────────────────────────────────┐
                   │   AI Anomaly Evaluation Complete     │
                   │  - If metric targets surge:          │
                   │  - Automated email/brief generation  │
                   └──────────────────────────────────────┘
```

---

## 5. Architectural Reliability & Security Guardrails

| Infrastructure Segment | Technical Operational Guardrail | Risk Mitigation Vector |
| :--- | :--- | :--- |
| **Data Ingestion Gate** | Streamlit-equivalent caching optimization (`@st.cache_data` logic patterns translated to Redis/Memory caching blocks) | Eliminates API rate-limiting blocks and stabilizes dashboard database reads. |
| **Compute Node Core** | Deployment of dedicated non-privileged user accounts inside Docker (`USER appuser`) | Prevents container escape vectors and guarantees compliance metrics. |
| **AI Inference Engine** | Localized fallback vector query engines running isolated from third-party networks | Guarantees search operations continue smoothly even during external API downtime. |
