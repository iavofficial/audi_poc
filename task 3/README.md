# AWS RDS K8s Operator

Task: As part of the platform we are providing a database as a service (DBaaS) that teams can request. Please create a custom 
k8s operator for offering AWS RDS instance to a given stage, where credentials are stored as k8s secrets.

Overview: The AWS RDS k8s Operator (rds_operator.py) is a custom K8s operator built using Python with the `kopf` framework. This operator
provides a DBaaS model where teams can request AWS RDS instances with PostgreSQL or MySQL as DB engines using a
custom resource in K8s.

Assumptions: 
- Our solution has been tailored for AWS. 
- An existing AWS EKS Cluster in combination with AWS IAM SSO. 
- 3 environments names have been assumed `pre-live`, `dev` and `int` where the DB would operate.
- Multiple options of DB engine within RDS are possible, but in our solution we use Postgres and MySQL as examples.

Note: For scenarios using Azure AKS Cluster, something similar can be done with Azure AD (SSO) and storing DB credentials 
securely in K8s secrets.

Features:
- Kubernetes Secrets management: The operator securely stores database credentials (username, password, endpoint).
- Integrated IAM authentication using AWS SSO/IAM Roles via IRSA.

## Folder Structure
<pre> <code>
task 3/
├── manifests/ # All Kubernetes manifests (CRD, RBAC, Deployments) 
│    ├── mysql_cr.yaml
│    ├── postgres_cr.yaml
│    ├── rds_operator_deploy.yaml  
│    ├── rds_operator_irsa.yaml  
│    ├── rds_operator_rbac.yaml 
│    ├── rdsinstance_crd.yaml 
├── operator/ # Python operator logic 
├──  ├── __init__.py 
│    ├── rds_operator.py
├── .gitignore
├── Dockerfile 
├── README.md 
├── requirements.txt
</code> </pre>

## How it works
- RDS Operator uses CRDs and kopf handlers to provision, manage and delete RDS instances.
  - CRDs
    - @kopf.on.create listens for the creation of RDSInstance resources and:
      - Provisions an AWS RDS instance using the AWS RDS API (boto3).
      - Generates strong random credentials. 
      - Stores these credentials and connection details as k8s Secret.

    - @kopf.on.delete listens for the deletion of RDSInstance resources and:
      - Deletes the corresponding RDS instance in AWS. 
      - Deletes the associated k8s secret.
  
  - Environment/Stage specific isolation as RDS instances are scoped to different K8s namespaces based on stage/env names
    (`pre-live`, `dev` and `int`).

## Prerequisites
- `aws-cli` is installed and configured
- Setup AWS SSO.
```bash
aws configure sso # To authenticate with AWS SSO.
```
- AWS EKS Cluster is setup and reachable.
- Set AWS EKS to the SSO user to your region. 
```bash
aws eks --region eu-central-1 update-kubeconfig --name aws-eks-cluster-name --profile aws-sso-user-profile
```
- `kubectl` CLI installed and configured.
- To reach existing EKS Cluster
```bash
kubectl get nodes
```
- Proper AWS access setup (IAM Roles or AWS SSO).
- IAM Role for Service Account (IRSA)
- Reachable Docker Repository

## Installation Steps
### 1. Deploy the Custom Resource Definition (CRD)
```bash
kubectl apply -f manifests/rdsinstance_crd.yaml
```
Note: DB requirements are defined in the `rdsinstance_crd.yaml` file, properties of which can be further adjusted/customized.

### 2. Configure RBAC Permissions for the operator
- We use `ClusterRole` to grant permission to manage RDSInstance resources and K8s secrets across namespaces.
- We use `ClusterRoleBinding` to tie the `ClusterRole` to operators SA, configured in the default namespace.
#### Apply the RBAC Config for the operator
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
Create an RDSInstance custom resource in dev env with postgres as DB engine.
```bash
kubectl apply -f manifests/postgres_cr.yaml
```
Note: namespace/stage, instance size, storage among others can be customized.

**OR**

Create an RDSInstance custom resource in int env with mysql as DB engine.
```bash
kubectl apply -f manifests/mysql_cr.yaml
```
Note: namespace/stage, instance size, storage among others can be customized.

### 5. Delete the RDS CR along with its credentials
```bash
kubectl delete rdsinstance dev-database -n dev
```
Note: DB name to be adjusted corresponding to what was deployed in ***Step 4***

## Validation
### Check operator pod running in the `default` namespace
```bash
kubectl get pods -n default
```
### View operator logs
```bash
kubectl logs -l app=rds-operator -n default
```
### Use AWS CLI to verify RDS instance has been created
```bash
aws rds describe-db-instances
```


