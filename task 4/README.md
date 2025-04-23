**Requirement:** 

Configuration and deployment of the OTEL collector that will collect logs, metrics and span - and store them in a multi tenant Grafana stack deployment.


**Assumptions:**
* Flux-cd is deployed along with Application in Kubernetes cluster.
* Grafana is deployed and configured in the k8s cluster.
* OTEL is installed and configured.


**Pre-requisites:**
1. Tenant Ids
2. Grafana Account
3. Data Source
4. Otel


**Github Folder Structure:**

```
my-otel-repo
│   README.md                       		 # Documentation about the Flux deployment process
│
├── namespaces
│   └── monitoring.yaml            			 # Namespace definition for "monitoring"
│
├── flux
│   └── kustomization.yaml                   # Flux deployment, GitRepository, and Kustomization manifests
│
├── otel-collector
│   └── base
│       ├── kustomization.yaml   			 # Kustomize base for OTEL Collector
│       ├── otel-collector-deployment.yaml 		 # OTEL Collector Deployment manifest
│       └── otel-collector-config.yaml 			 # OTEL Collector configuration (config map or file)
│
├── kustomizations
│   └── monitoring.yaml           			 # Aggregated kustomization referencing all components
│
└── grafana-stack
    ├── provisioning
    │   └── datasources
    │       └── datsources.yaml				 # Automates the setup and management of data sources in Grafana
    │
    ├── loki
    │   └── base
    │       ├── kustomization.yaml    		 # Kustomize base for Loki
    │       ├── loki-deployment.yaml 
    │       ├── loki-service.yaml
    │       └── loki-config.yaml
    │
    ├── tempo
    │   └── base
    │       ├── kustomization.yaml    		 # Kustomize base for Tempo
    │       ├── tempo-deployment.yaml    
    │       ├── tempo-service.yaml
    │       └── tempo-config.yaml
    │
    └── mimir
        └── base
            ├── kustomization.yaml    		 # Kustomize base for Mimir (Grafana's metrics backend)
            ├── mimir-deployment.yaml 
            ├── mimir-service.yaml
            └── mimir-config.yam

```


## Breakout of the Github Structure: ##

***namespaces/monitoring.yaml -*** Defines the monitoring Kubernetes namespace where all monitoring components will be deployed. In Kubernetes, namespaces help you organize your cluster resources, providing scope for objects and a way to divide cluster resources amongst users and teams.

***flux/kustomization.yaml -*** This file configures Flux to continuously reconcile the cluster state with the desired state defined in Git. It specifies the source Git repository (including branch and path) and defines how often Flux should check for changes (interval), and whether to prune resources (prune: true). It's key for automating the deployment process. Basically this file contains Flux-specific Kustomize configuration. Flux is a GitOps operator that syncs Kubernetes manifests from Git repositories to the cluster. This file tells Flux what to deploy and where, enabling automated and continuous deployment of your monitoring stack.

***otel-collector/base:*** 

This directory contains the base manifests for deploying the OpenTelemetry Collector, which is responsible for collecting, processing, and exporting telemetry data.

*kustomization.yaml -* This Kustomize file defines the basis for customizing the OTEL Collector deployment. It specifies the resources that Kustomize should use to generate the final deployment configuration.

*deployment.yaml -* This contains the core manifests for deploying the OpenTelemetry Collector. Describes the Kubernetes Deployment for the OpenTelemetry Collector. It specifies the application's container image, number of replicas, and volume mounts. Kubernetes Deployment manifest defining the OpenTelemetry Collector pod(s), including container images, resource requests, environment variables, and other deployment details.

*config.yaml -* contains the collector’s pipeline and exporter configuration. Configures the OTEL Collector by defining which receivers, processors, and exporters to enable. It's typically mounted as a ConfigMap, making the configuration separate from the application code and easy to adjust. Configuration file for the OpenTelemetry Collector itself. It defines pipelines, receivers (e.g., OTLP, Jaeger), processors, and exporters (e.g., sending data to Loki, Tempo, or Mimir).


***kustomizations/monitoring.yaml -***  This YAML file acts as the root kustomization that references all the component kustomizations like OpenTelemetry Collector, Grafana stack components. It's used to aggregate all the individual deployments into a single deployable unit, orchestrating the deployment of the entire observability stack in one go. 



***grafana-stack:*** 

Each Grafana component (Tempo, Loki, Mimir) has its own directory with base manifests.


**tempo/base::**

*kustomization.yaml -* Like for the OTEL Collector, it's used by Kustomize to customize the Tempo deployment.

*deployment.yaml/service.yaml -* Tempo is used for trace data storage. These YAML files set up the Tempo service for storing and querying trace data, making it part of a full-stack observability setup alongside Prometheus, Loki, and Grafana.



**loki/base::**

*kustomization.yaml -* Similar to above, it's for customizing Loki's Kubernetes resources.

*deployment.yaml/service.yaml -* Loki is a highly scalable, multi-tenant log aggregation system. These YAMLs set up Loki, enabling centralized and distributed logging from all the components and services in the Kubernetes cluster.



**mimir/base::**

*kustomization.yaml -* Customizes Mimir's Kubernetes resources.

*deployment.yaml/service.yaml -* Grafana Mimir is a modern, scalable, and highly available metrics system. These YAML files deploy Mimir, enabling strong consistency and high availability for metrics, complementing the log aggregation with Loki.

**provisioning/datasources/datasources.yaml** - The YAML file lists one or more data sources (such as Prometheus, Loki, Tempo, MySQL, etc.), specifying their names, types, URLs, access methods, credentials, and other options. Its purpose is to automate the setup and management of data sources in Grafana by defining them as code, rather than configuring them manually through the Grafana web UI.


***Integration and Connectivity:***

The otel-collector/base/otel-collector-config.yaml is where you define how the collector receives, processes, and exports telemetry data.

*Receivers:* Set up OTLP, Prometheus, or other receivers to accept data from instrumented applications.

*Exporters:* Configure exporters to send metrics, traces, and logs to the respective Grafana stack components.

Below is the more detailed overview of the process:

1. Data Collection and Export (OpenTelemetry/Otel Collector)

Instrumentation: Applications are instrumented with OpenTelemetry SDKs or agents to generate telemetry data (metrics, logs, traces).
(*Instrumentation* is the process of modifying your application—either by adding code or using external agents—so it can emit telemetry data)

Otel Collector: The Otel Collector receives this data via the OTLP (OpenTelemetry Protocol) receiver, which supports both gRPC and HTTP endpoints.



2. Data Routing to Storage Backends (Grafana Stack Data Sources)

The Otel Collector exports each type of telemetry data to a specialized backend:

*Metrics:* Exported to Prometheus or Grafana Mimir using a Prometheus remote write exporter.

*Logs:* Exported to Loki using a Loki exporter.

*Traces:* Exported to Tempo using an OTLP exporter.

Each backend is optimized for its data type:

*Prometheus/Mimir:* Stores and indexes metrics.

*Loki:* Stores and indexes logs.

*Tempo:* Stores and indexes traces.


3. Visualization and Analysis (Grafana)

Grafana connects to these backends as data sources:

Prometheus/Mimir for metrics
Loki for logs
Tempo for traces


**Key Points:**

* Otel Collector acts as a central hub, receiving telemetry from applications and routing it to the appropriate backend.

* Grafana connects to these backends as data sources, enabling visualization and analysis.

* Communication between components typically uses OTLP for traces/logs/metrics, Prometheus Remote Write for metrics, and specific exporters for logs and traces

* Grafana queries these data sources to power dashboards, alerts, and analytics.

* Users visualize and analyze telemetry data in Grafana, leveraging its rich dashboarding and query capabilities.

```
[Applications]
     │
     ▼
[Otel Collector]
     │
     ├─── Metrics ───► [Prometheus/Mimir]
     │
     ├─── Logs ──────► [Loki]
     │
     └─── Traces ────► [Tempo]
                          │
                          ▼
                       [Grafana]

```
