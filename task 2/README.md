
1. Requirement
2. Assumptions
3. Pre-requisites
4. Github Folder Structure
5. Breakout of the Github Structure
6. Connectivity and Integration


# Requirement

As we are using GitOps principle as our main deployment strategy -leveraging flux cd - please describe how to configure a multi-tenant deployment of flux cd where each tenant has a product or a development team. How to extend flux cd to export alerting and notification of failed flux execution to Rocket Chat and PagerDuty?


# Assumptions

1. Flux is deployed along with the application in K8s cluster.
2. Pagerduty and Rocket chat are deployed along with the application.


# Pre-requisites

1. Folder structure
2. Isolating the tenants
3. Set Namespace, service account and role bindings in rbac.yaml (role based access control) file.


*Service Accounts: Ensure that each tenant uses a specific service account for deployments.

*Role Bindings: Limit access to only the assigned namespaces


Github Folder structure::
```
├── clusters
│   ├── production
│   └── staging
├── infrastructure
│   ├── kyverno
│   ├── kyverno-policies
│   ├── notifications
│   │   ├── pagerduty-provider.yaml
│   │   ├── pagerduty-alert.yaml
│   │   ├── rocket-chat-provider.yaml
│   │   ├── rocket-chat-alert.yaml
│   │   └── kustomization.yaml
│   ├── rbac
│   │   └── rbac.yaml                 
│   ├── secrets
│   │   └── rocket-chat-secret.yaml
│   └── services
│       └── rocket-chat-notifier.yaml
└── tenants
    ├── team 1
    │   ├── base
    │   │   ├── kustomization.yaml
    │   │   ├── podinfo-release.yaml
    │   │   └── podinfo-repository.yaml
    │   ├── production
    │   │   ├── kustomization.yaml
    │   │   └── podinfo-values.yaml
    │   └── staging
    │       ├── kustomization.yaml
    │       └── podinfo-values.yaml
    └── team2
        ├── base
        │   ├── kustomization.yaml
        │   ├── podinfo-release.yaml
        │   └── podinfo-repository.yaml
        ├── production
        │   ├── kustomization.yaml
        │   └── podinfo-values.yaml
        └── staging
            ├── kustomization.yaml
            └── podinfo-values.yaml

```	


# Breakout of the Github structure

**Root level structure -**

```
├── clusters
├── infrastructure
└── tenants
```

*clusters:* Contains cluster-specific configurations.

*infrastructure:* Holds shared infrastructure components and services.

*tenants:* Contains tenant-specific applications and configurations, organized by teams.


1. ***Cluster:***

```
├── production
└── staging
```

**Purpose:** Store cluster-wide configurations and manifests for different environments.

**production:** Manifests and configurations specific to the production Kubernetes cluster ensuring high availability, performance optimization, and stringent security measures.
staging: Manifests and configurations specific to the staging Kubernetes cluster, which may mirror production but might scale down resources or vary in configuration to mimic a non-production environment.

**Example content:** Cluster-level resources like network policies, ingress controllers, cluster roles, or environment-specific settings.




2. ***Infrastructure:***

```
├── kyverno
├── kyverno-policies
├── notifications
│   ├── pagerduty-provider.yaml
│   ├── pagerduty-alert.yaml
│   ├── rocket-chat-provider.yaml
│   ├── rocket-chat-alert.yaml
│   └── kustomization.yaml
├── secrets
│   └── rocket-chat-secret.yaml
└── services
    └── rocket-chat-notifier.yaml
```

**Purpose:** Contains shared infrastructure components and configurations used across clusters and tenants.


**Subdirectories:**

*kyverno (Optional):* Likely contains Kyverno controllers or related manifests. Contains manifests and configuration for Kyverno, a Kubernetes-native policy engine, allowing for the enforcement of policies across the entire Kubernetes environment, ensuring compliance and security


*kyverno-policies (Optional):* Contains Kyverno policies for enforcing security, compliance, or best practices on Kubernetes resources. Houses custom Kyverno policies that define specific rules and constraints to govern deployments, resource configuration, network policies, etc., across the clusters.


*notifications:* Configurations for alerting and notification systems.

*pagerduty-provider.yaml & pagerduty-alert.yaml:* PagerDuty integration manifests. Configures PagerDuty as a notification provider and defines specific alerts that trigger PagerDuty incidents.

*rocket-chat-provider.yaml & rocket-chat-alert.yaml:* Rocket.Chat integration manifests which configures Rocket.Chat for receiving alerts via webhooks from the Kubernetes environment.
kustomization.yaml: Kustomize file to build the notification manifests which orchestrates the deployment of notification providers and alert configurations, often leveraging overlays for different environments.

*rocket-chat-alert.yaml -* This file is essential for defining alerting rules and configurations within a Kubernetes cluster when using FluxCD. It specifies the conditions under which notifications should be triggered and ensures that Rocket.Chat receives alerts about events in the cluster.

* provider.yaml - you specify pagerduty url and integration key.
* alert.yaml - Specifies the conditions under which notifications should be sent to PagerDuty.

*rbac:*

1. older dedicated to Role-Based Access Control manifests.
2. rbac.yaml contains definitions of Roles, ClusterRoles, RoleBindings, and ClusterRoleBindings.
3. Centralizes access control configuration to manage permissions and security.


**secrets:** Stores sensitive information like credentials or tokens.

*rocket-chat-secret.yaml:* Secret for Rocket.Chat integration. Specifies a Kubernetes Secret for securely storing sensitive information relevant to Rocket.Chat notifications, such as API tokens.


**services:** Contains shared service manifests.

*rocket-chat-notifier.yaml:* Deployment/service manifest for Rocket.Chat notifier. Provides a deployment or service that manages and sends notifications to Rocket.Chat, possibly as a Kubernetes deployment or job.




3. ***Tenants:***

```
├── team 1
│   ├── base
│   │   ├── kustomization.yaml
│   │   ├── podinfo-release.yaml
│   │   └── podinfo-repository.yaml
│   ├── production
│   │   ├── kustomization.yaml
│   │   └── podinfo-values.yaml
│   └── staging
│       ├── kustomization.yaml
│       └── podinfo-values.yaml
└── team2
    ├── base
    │   ├── kustomization.yaml
    │   ├── podinfo-release.yaml
    │   └── podinfo-repository.yaml
    ├── production
    │   ├── kustomization.yaml
    │   └── podinfo-values.yaml
    └── staging
        ├── kustomization.yaml
        └── podinfo-values.yaml

```

Each subdirectory represents a separate team or project within the organization, highlighting a method to manage multi-tenancy in Kubernetes.

**Purpose:** Organize tenant-specific applications and environment overlays.


**team 1 and team2:** Separate folders for each team or tenant, enabling multi-tenancy. Team 1 and Team 2 reflect two distinct teams, each with their own environments (base, production, staging). This hierarchical setup allows for team-specific configurations while also providing shared base configurations for application deployment.



**Subdirectories per team:**

***base:***

Contains the base manifests common to all environments for that team.

*kustomization.yaml:* Defines how to build the base resources. Configures the base setup, including deployments and Helm charts (indicated by podinfo-release.yaml and podinfo-repository.yaml). This is a shared baseline that all environments (production, staging) inherit from

*podinfo-release.yaml:* Kubernetes manifests for the application release, defining the Helm chart release to deploy.

*podinfo-repository.yaml:* Possibly Helm repository or image repository info.

** These files (podinfo-release.yaml & podinfo-repository.yaml) suggest a Helm-based deployment for a fictional or placeholder application (podinfo), defining the Helm chart release to deploy and the repository from which to pull the charts.



***production:***

Environment-specific overlays for production.

*kustomization.yaml:* References base and applies production-specific patches or configurations. This is a environment-specific kustomization file that overlay and customize the base configurations for each environment's unique needs.

*podinfo-values.yaml:* Configuration values specific to production environment. Helm values files for the podinfo application, specifying configurations such as environment settings, resource limits, and other parameters tailored to each environment.



***staging:***

* Environment-specific overlays for staging.

* Similar structure as production but with staging-specific configs.





# Connectivity and Integration

***Pager duty:***

We have to generate an Integration key from pager duty's console and then save it to kebernetes secrets which will make flux cd and pagerduty communicate with each other as we are gonna mention the integration key in provider yaml file.

(* provider.yaml - you specify pagerduty url and integration key.)


*To generate the YOUR_PAGERDUTY_INTEGRATION_KEY, follow these steps:*

1. Log in to your PagerDuty account.
2. Navigate to Service Directory: Go to Services > Service Directory. Or, click Configuration > Services > Add Service.
3. Add a New Service:
4. Click on New Service or Add New Service button.
5. Specify the service details such as Name and Description.
6. Choose the Escalation Policy to apply to the service.
7. Integration Settings: Under Integration Settings > Integration Type, choose Events API v2 or select Site24x7 from the available services.
8. Add Integration: Click Add Integration or Add Service button.
9. Copy the Integration Key: Once the service is created, copy the Integration Key (also referred to as routing key). This key will be displayed on your screen.
10. The integration key is used to route events from your monitoring system (in this case, Flux CD) to the correct PagerDuty service. Make sure to keep it secure.



***Rocket Chat:***


1. Create a rocket-chat webhook and use it for Flux-cd to communicate with rocket-chat.
2. Or login to rocketchat with the sso enabled account and navigate to this path in your profile Avatar > Account > Personal Access Tokens, and then generate a personal access token.
3. This token will act as your authentication key for API calls.
4. Store the encoded token in rocket-chat-secret.yaml file. We have to refer that secret file in rocket-chat-provider.yaml file.
5. Use the below commands to encode your values -

```
echo -n 'your-user-id' | base64
echo -n 'your-auth-token' | base64
```




