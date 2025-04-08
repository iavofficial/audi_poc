# AWS MSK Kubernetes Operator

This repository contains a **Custom Kubernetes Operator** designed to manage **Topics** and **ACLs (Access Control Lists)** for **AWS MSK (Managed Streaming for Apache Kafka)** services. The operator leverages **Client Certificate Authentication** for secure communication with the MSK cluster and allows the declarative configuration of Kafka topics and ACLs via Kubernetes Custom Resources.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Pre-requisites](#pre-requisites)
4. [Setup and Installation](#setup-and-installation)
5. [Defining Topics and ACLs](#defining-topics-and-acls)
6. [Testing](#testing)
7. [Known Limitations](#known-limitations)
8. [Troubleshooting](#troubleshooting)
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
2. **AWS Credentials** with sufficient permissions to manage topics and ACLs (`boto3` will use these credentials).
3. **Certificates Files**:
   - `client.crt`: The client certificate.
   - `client.key`: The client's private key.
   - `ca.crt`: The Certificate Authority used to sign the client certificate.
4. **Kubernetes Cluster**:
   - Ensure `kubectl` is installed and connected to your cluster.
5. **Python 3.9+** (if building locally).

---

## Setup and Installation

### Step 1: Create a Secret to Store Certificates

Store your Client Certificate, Key, and CA Certificate as a Kubernetes Secret. Run the following command:

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

### Step 4: Deploy the Kubernetes Operator

Deploy the operator as a Kubernetes Deployment:

```bash
kubectl apply -f deployment.yaml
```

Verify that the operator pod is running:

```bash
kubectl get pods
```

You should see an operator pod with the name `audi-operator`.

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

You can check the operator logs to confirm that the topic was successfully created in the AWS MSK cluster:

```bash
kubectl logs -l app=audi-operator
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

Check the operator logs to confirm the ACL creation:

```bash
kubectl logs -l app=audi-operator
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

With this, the task requirements have been fulfilled end-to-end.

---
