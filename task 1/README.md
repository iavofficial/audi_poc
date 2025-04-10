# AWS MSK Kubernetes Operator

This repository contains a **Custom Kubernetes Operator** designed to manage **Topics** and **ACLs (Access Control Lists)** for **AWS MSK (Managed Streaming for Apache Kafka)** services. The operator leverages **Client Certificate Authentication** for secure communication with the MSK cluster and allows the declarative configuration of Kafka topics and ACLs via Kubernetes Custom Resources.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Pre-requisites](#pre-requisites)
4. [How the Operator works](#how-the-operator-works)
5. [Setup and Installation](#setup-and-installation)
6. [Defining Topics and ACLs](#defining-topics-and-acls)
7. [Testing](#testing)
8. [Known Limitations](#known-limitations)
9. [Project Structure](#project-structure)

---

## Overview

The **AWS MSK Kubernetes Operator** simplifies the operational tasks of creating, updating, and deleting Kafka topics and ACLs in AWS MSK clusters, following the Kubernetes declarative style of resource management. The operator is implemented using the `kopf` (Kubernetes Operator Python Framework) library and communicates with AWS MSK using the `boto3` SDK.

### Architecture Overview

1. **Custom Resource Definitions (CRDs)**:
   - `Topic`: Represents Kafka topics.
   - `ACL`: Represents access policies for Kafka topics.
2. **Operator**:
   - Watches for `create`, `update`, and `delete` events on the custom resources.
   - Handles interactions with the AWS MSK API (secured via Client Certificates).

---

## Features

- Declarative management of **Kafka topics** using Kubernetes Custom Resources.
- Declarative management of **Kafka ACLs** for fine-grained access control.
- Secure communication with AWS MSK using **Client Certificate Authentication**.
- Full integration with Kubernetes via CRDs and ConfigMaps.

---

## Pre-requisites

Ensure the following are set up before proceeding:

1. **AWS MSK Cluster** with client certificate-based authentication enabled.
   - You must configure and deploy an AWS MSK Cluster _before_ using this operator.
   - Retrieve the ARN (Amazon Resource Name) of your Kafka cluster from the AWS Console or CLI, as it will be required for the configuration files.
2. **AWS Credentials** with sufficient permissions to manage topics and ACLs (`boto3` will use these credentials).
3. **Certificates Files**:  
   The operator requires the following certificates for client certificate authentication with AWS MSK:

   - `client.crt`: The client certificate.
   - `client.key`: The client's private key.
   - `ca.crt`: The Certificate Authority used to sign the client certificate.

   **If you already have these certificate files** (e.g., provided by your infrastructure team), you can skip the "Certificate Creation" section below.

   **If you need to generate the certificate files yourself** (e.g., for testing or proof-of-concept purposes), follow the steps in the "Certificate Creation" section.

4. **Kubernetes Cluster**:
   - Ensure `kubectl` is installed and connected to your cluster.
5. **Python 3.9+** (if building locally).

---

## How the Operator works

The Kubernetes operator is implemented in the `audi_operator.py` script using the [`kopf`](https://kopf.readthedocs.io/) library. It acts as the "brain" of the operator by watching for events in Kubernetes resources (`topics` and `acls`) and translating them into AWS MSK API calls.

### What `audi_operator.py` Does

- Watches Kubernetes Custom Resources (`topics` and `acls`) created using the associated CRDs (`crd-topics.yaml` and `crd-acls.yaml`).
- Performs **create, update, and delete actions** on Kafka topics and ACLs by interacting with the AWS MSK APIs using the `boto3` SDK.
- Handles communication with the AWS MSK cluster securely using **client certificates** (stored as Kubernetes Secrets).

### How It Handles Events

- When you create, update, or delete a `Topic` or `ACL` Custom Resource in Kubernetes, `kopf` triggers the corresponding handler in `audi_operator.py`:
  - **Topics**:
    - `create_topic`: Creates a Kafka topic with the specifications in the resource.
    - `update_topic`: Logs warnings (MSK does not support dynamic updates such as partition adjustments).
    - `delete_topic`: Deletes the specified Kafka topic.
  - **ACLs (Access Control Lists)**:
    - `create_acl`: Adds a rule to allow/deny access to a Kafka topic for a specific user or service.
    - `update_acl`: Deletes and recreates the ACL with the updated rules.
    - `delete_acl`: Removes the access control rule for the target topic.

### How Communication Works

- The operator uses **client certificates** (`client.crt`, `client.key`, `ca.crt`) stored in a Kubernetes Secret (`msk-certificates`) to authenticate itself with the AWS MSK cluster.
- These certificates are automatically mounted into the operator pod at runtime and used for secure communication.

### What Triggers the Operator

- Creating or applying a `Topic` resource (e.g., `kubectl apply -f topic-example.yaml`) will trigger `audi_operator.py` to create that topic in AWS MSK.
- Applying or modifying an `ACL` resource similarly creates or adjusts an access control rule on the AWS MSK cluster.

### Example Workflow

**Important**: Replace the `clusterArn` placeholder in the `*.yaml` files with the actual ARN of your existing AWS MSK Kafka cluster.

1. **Create a Topic Resource**:
   Applying the following resource definition will trigger the operator to create the topic in AWS MSK:

```yaml
apiVersion: msk.aws.io/v1
kind: Topic
metadata:
  name: example-topic
spec:
  clusterArn: arn:aws:kafka:us-east-1:123456789012:cluster/example-cluster/abcd1234efgh5678ijkl9012mnop3456-1
  name: example-topic
  numPartitions: 3
  replicationFactor: 2
```

Command:

```bash
kubectl apply -f topic-example.yaml
```

Action:

- The operator detects the `create` event for the `Topic` resource.
- It calls `msk_client.create_topic` using the `boto3` client to create the topic in AWS MSK.

2. **Create an ACL Resource**: Similarly, applying this resource will trigger the operator to create the ACL in AWS MSK:

```yaml
apiVersion: msk.aws.io/v1
kind: ACL
metadata:
  name: example-acl
spec:
  clusterArn: arn:aws:kafka:us-east-1:123456789012:cluster/example-cluster/abcd1234efgh5678ijkl9012mnop3456-1
  topicName: example-topic
  principal: 'User:CN=example-user,OU=ExampleOU,O=ExampleOrg,L=ExampleCity,ST=ExampleState,C=ExampleCountry'
  operation: WRITE
  permission: ALLOW
```

Command:

```bash
kubectl apply -f acl-example.yaml
```

Action:

- The operator detects the `create` event for the ACL resource.
- It calls `msk_client.create_acl` using the `boto3` client to create the ACL in AWS MSK.

These examples demonstrate how audi_operator.py processes Kubernetes Custom Resources and interacts with AWS MSK to manage Kafka topics and ACLs.

### Important: Configure AWS Credentials

Before deploying the operator, make sure to configure your AWS credentials in the `src/audi_operator.py` file by replacing the placeholders with valid credentials. Look for the following section in the code:

```python
msk_client = boto3.client(
    "kafka",
    region_name="your-region",
    aws_access_key_id="your-access-key",
    aws_secret_access_key="your-secret-key"
)
```

## Setup and Installation

### Step 1: Create a Secret to Store Certificates

The operator requires certificates (`client.crt`, `client.key`, `ca.crt`) to securely communicate with the AWS MSK cluster.  
If you already have these files, you can skip to the next step and directly create a Kubernetes secret using your existing certificates.

If you don't have these files, the following instructions will guide you through generating the required certificates using OpenSSL. This is especially useful for testing or proof-of-concept scenarios.

**If you don’t have OpenSSL already installed, install it:**

- On macOS: brew install openssl
- On Ubuntu/Debian: sudo apt-get install openssl
- On Windows: Install it via [OpenSSL](https://slproweb.com/products/Win32OpenSSL.html) binaries.

Verify OpenSSL is installed by running:

```bash
openssl version
```

```bash
mkdir src/certificates && cd src/certificates
```

**Generate a Certificate Authority (CA)**
The Certificate Authority (CA) is used to sign the client certificate. Run the following commands:

1. Generate the private key for the CA:

```bash
openssl genrsa -out ca.key 2048
```

This generates a private key file named `ca.key`.

2. Generate the self-signed CA certificate:

```bash
openssl req -x509 -new -nodes -key ca.key -sha256 -days 365 -out ca.crt
```

During this step, OpenSSL will prompt you for a few details (e.g., Country Name, Common Name). These details aren't critical but ensure they are descriptive and consistent.
This generates:

- `ca.crt` (CA certificate, valid for 365 days)
- `ca.key` (private key for CA)
  **Generate a Client Certificate**
  The client certificate allows the operator to authenticate with the AWS MSK cluster.

1. Generate the private key for the client certificate:

```bash
openssl genrsa -out client.key 2048
```

2. Create a Certificate Signing Request (CSR) for the client:

```bash
openssl req -new -key client.key -out client.csr
```

You'll be prompted to supply the same optional details as before, but ensure the Common Name (CN) is distinctive. For example: "msk-client". 3. Sign the CSR using the CA to create the client certificate:

```bash
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365 -sha256
```

This generates:

- `client.crt` (signed client certificate)

**Verify the Certificates**
Ensure you have the following files after completing the steps above:

1. `ca.crt` (Certificate Authority certificate)
2. `client.crt` (Client certificate, signed by CA)
3. `client.key` (Private key for the client certificate)
   You can also verify that the client certificate is signed by the CA:

```bash
openssl verify -CAfile ca.crt client.crt
```

The output should indicate that `client.crt` is valid under `ca.crt`.

Store your Client Certificate, Key, and CA Certificate as a Kubernetes Secret. Run the following command:

```bash
minikube start
```

```bash
kubectl create secret generic msk-certificates \
  --from-file=client.crt=src/certificates/client.crt \
  --from-file=client.key=src/certificates/client.key \
  --from-file=ca.crt=src/certificates/ca.crt
```

Verify the secret creation:

```bash
kubectl get secret msk-certificates
```

### Step 2: Deploy Custom Resource Definitions (CRDs)

Install the CRDs for `Topic` and `ACL` objects:

```bash
kubectl apply -f crd-topics.yaml
kubectl apply -f crd-acls.yaml
```

Verify that the CRDs are applied:

```bash
kubectl get crds
```

### Step 3: Deploy the ConfigMap

Update the `msk-config.yaml` file with your AWS MSK Cluster Information (e.g., `CLUSTER_ARN`) and then apply it:

```bash
kubectl apply -f msk-config.yaml
```

Verify that the ConfigMap was successfully created:

```bash
kubectl get configmap msk-config
```

---

### Step 4: Build and Deploy the Kubernetes Operator

#### **Step 4.1: Build the Docker Image**

Before deploying the Kubernetes operator, you need to first build a Docker image that includes your operator code (`src/audi_operator.py`). Run the following commands to build the image:

```bash
# Navigate to the project root directory
docker build -t audi-operator:latest .
```

This will create a Docker image with the tag `audi-operator:latest`, which will be used in the deployment.

#### **Step 4.2: Push the Docker Image (If Needed)**

If you're using a remote Kubernetes cluster and not running Kubernetes locally (e.g., through Minikube), you need to push the Docker image to a container registry so that it can be pulled by your Kubernetes cluster. For example, if you're using Docker Hub:

```bash
# Tag your image for Docker Hub (replace with your username)
docker tag audi-operator:latest <your-docker-hub-username>/audi-operator:latest

# Push the image to Docker Hub
docker push <your-docker-hub-username>/audi-operator:latest
```

#### **Step 4.3: Update the Deployment File (If Needed)**

If the image name or location has changed (e.g., pushed to Docker Hub or another registry), update the `image` field in `deployment.yaml` to reference the correct image:

```yaml
image: <your-docker-hub-username>/audi-operator:latest
```

#### **Step 4.4: Deploy the Kubernetes Operator**

Now you can deploy the operator as a Kubernetes Deployment:

```bash
kubectl apply -f deployment.yaml
```

Verify that the operator pod is running:

```bash
kubectl get pods
```

---

## Defining Topics and ACLs

### Step 1: Define a Kafka Topic

Create a Custom Resource for a Kafka topic using `topic-example.yaml`. Update the file with your desired topic configuration:

```yaml
apiVersion: msk.aws.io/v1
kind: Topic
metadata:
  name: example-topic
spec:
  clusterArn: arn:aws:kafka:us-east-1:123456789012:cluster/example-cluster/abcd1234efgh5678ijkl9012mnop3456-1
  name: example-topic
  numPartitions: 3
  replicationFactor: 2
```

Once you have updated the topic configuration, apply it as follows:

```bash
kubectl apply -f topic-example.yaml
```

Verify that the topic resource is created:

```bash
kubectl get topics.msk.aws.io
```

### Step 2: Define an ACL

Create a Custom Resource for an ACL using `acl-example.yaml`. Update the file with the required ACL configuration:

```yaml
apiVersion: msk.aws.io/v1
kind: ACL
metadata:
  name: example-acl
spec:
  clusterArn: arn:aws:kafka:us-east-1:123456789012:cluster/example-cluster/abcd1234efgh5678ijkl9012mnop3456-1
  topicName: example-topic
  principal: 'User:CN=example-user,OU=ExampleOU,O=ExampleOrg,L=ExampleCity,ST=ExampleState,C=ExampleCountry'
  operation: WRITE
  permission: ALLOW
```

Once updated, apply it to the Kubernetes cluster:

```bash
kubectl apply -f acl-example.yaml
```

Verify that the ACL resource is created:

```bash
kubectl get acls.msk.aws.io
```

---

## Testing

To ensure everything works as expected, follow these steps:

1. Deploy the **Kafka Topic** and **ACL Custom Resources** (as above).
2. Verify that the operator has successfully created the topic and associated ACL in your AWS MSK cluster.
3. Deploy a test pod that references the `msk-config` to ensure environment variables are correctly loaded:

```bash
kubectl apply -f test-pod.yaml
```

Check the pod's environment variables to verify the `CLUSTER_ARN` is correctly passed:

```bash
kubectl logs test-pod
```

4. Use an AWS MSK client or Kafka tooling to confirm that the topic and ACL are functioning correctly.

---

## Known Limitations

1. **AWS MSK API Constraints:**
   - AWS MSK does not support updating partition counts or replication factors for existing topics.
   - You can delete and recreate topics to change their configuration.
2. **Error Handling:**
   - While the operator logs errors during resource creation, external failure mechanisms (e.g., API errors) need external handling.
3. **Limited Scope:**
   - Only TOPIC ACLs are implemented in this version of the operator. Adding other resource types requires extending the code.

---

## Project Structure

```
├── crd-topics.yaml              # CRD for Kafka Topics
├── crd-acls.yaml                # CRD for ACLs
├── topic-example.yaml           # Example Topic Custom Resource
├── acl-example.yaml             # Example ACL Custom Resource
├── msk-config.yaml              # Kubernetes ConfigMap for operator configuration
├── deployment.yaml              # Kubernetes Deployment for the operator
├── test-pod.yaml                # Test pod for verifying ConfigMap mount
├── src/                         # Source directory for the operator
│   ├── audi_operator.py         # Main operator logic (implemented using Kopf)
│   ├── certificates/            # x.509 certificates for Client Cert Authentication
│       ├── client.key
│       ├── client.crt
│       ├── ca.crt
│       ├── ca.key
│       ├── ca.srl
├── requirements.txt             # Python dependencies for the operator
├── Dockerfile                   # Dockerfile to containerize the operator
└── README.md                    # This readme
```

---

## Verification of Task Completion

The client requested a **Custom Kubernetes Operator for managing Kafka Topics and ACL definitions within AWS MSK**, secured by **Client Certificate Authentication**. Below are the key deliverables we implemented to fulfill the task:

1. **Custom Resources for Topics and ACLs**:

   - `crd-topics.yaml` defines the CRD for Kafka Topics.
   - `crd-acls.yaml` defines the CRD for ACLs.

2. **Declarative Management**:

   - Users can declare Kafka Topics (`topic-example.yaml`) and ACLs (`acl-example.yaml`) in a Kubernetes-native way.

3. **Client Certificate Authentication**:

   - The operator interacts securely with the AWS MSK API using client-side certificates:
     - `client.key` (private key)
     - `client.crt` (certificate)
     - `ca.crt` (Certificate Authority for verification)

4. **Operator Implementation**:

   - The operator (`src/audi_operator.py`) manages the lifecycle of topics and ACLs using the AWS Python SDK (`boto3`) and `kopf`.

5. **Infrastructure as Code**:
   - A Kubernetes `Deployment` (`deployment.yaml`) is provided to run the operator in a Kubernetes cluster.
   - Supporting resources (e.g., ConfigMap, Secrets) have been implemented.

By following this documentation, the client can:

- Deploy the operator.
- Create and manage Kafka Topics and ACLs declaratively.
- Verify the secure communication between the operator and AWS MSK.

---
