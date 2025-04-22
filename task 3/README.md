# AWS RDS Kubernetes Operator

Task: As part of the platform we are providing a database as a service that teams can request. Please create a custom 
k8s operator for offering AWS RDS instance to a given stage, where credentials are stored as k8s secrets.

Overview: The AWS RDS Kubernetes Operator (rds_operator.py) is a custom K8s operator built using Python with the `kopf` framework. This operator
provides a "Database-as-a-Service" (DBaaS) model where teams can request AWS RDS instances (PostgreSQL or MySQL) using a
custom resource in K8s.

Assumptions: 
- Our solution has been tailored for AWS.
- An existing AWS EKS Cluster.
- 3 environments names have been assumed `pre-live`, `dev` and `int` where the DB would operate.
- Supports Postgres or MySQL DB engines within AWS RDS.

Features:
- Kubernetes Secrets management: The operator securely stores database credentials (username, password, endpoint).
- Integrated IAM authentication using AWS SSO/IAM Roles via IRSA.

## Folder Structure
<pre> <code>
├── .gitignore
├── Dockerfile 
├── README.md 
├── requirements.txt 
├── operator/ # Python operator logic 
│    ├── rds_operator.py  
├── manifests/ # All Kubernetes manifests (CRD, RBAC, Deployments) 
│    ├── rdsinstance_crd.yaml  
│    ├── rds_operator_deploy.yaml  
│    ├── rds_operator_irsa.yaml  
│    ├── rds_operator_rbac.yaml 
│    ├── postgres_cr.yaml 
</code> </pre>


## Prerequisites
- `aws-cli` is installed and configured
- Setup AWS SSO.
- AWS EKS Cluster is setup
- `kubectl` CLI installed and configured.
- Proper AWS access setup (IAM Roles or AWS SSO).
- IAM Role for Service Account (IRSA)

## Installation Steps
```bash
cd task 3/
```
### 1. Deploy the Custom Resource Definition (CRD)
```bash
kubectl apply -f manifests/rdsinstance_crd.yaml
```

### 2. Configure RBAC Permissions for the operator
```bash
kubectl apply -f manifests/rds_operator_rbac.yaml
```

### 3. Operator deployment
First build and push the operator docker image
```bash
docker build -t <your-dockerhub-username>/aws-rds-operator:latest .
docker push <your-dockerhub-username>/aws-rds-operator:latest
```

Apply the operator deployment manifest
```bash
kubectl apply -f manifests/rds_operator_deploy.yaml
```

### 4. Deploy the postgres DB as custom resource
Create an RDSInstance custom resource in dev env.
```bash
kubectl apply -f manifests/postgres_cr.yaml
```

### 5. Delete the RDS CR along with its credentials
```bash
kubectl delete rdsinstance dev-database -n dev
```



