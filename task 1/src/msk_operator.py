# copyright IAV GmbH 2025

import kopf
import boto3
import logging
import certifi
import os
from botocore.exceptions import ClientError

# Initialize AWS MSK client
msk_client = boto3.client("kafka")


# Define the logic for creating/updating topics
@kopf.on.create('msk.aws.io', 'v1', 'topics')
def create_topic(spec, **kwargs):
    cluster_arn = spec['clusterArn']
    topic_name = spec['name']
    num_partitions = spec.get('numPartitions', 1)
    replication_factor = spec.get('replicationFactor', 1)

    try:
        # Create a new topic in MSK
        response = msk_client.create_topic(
            ClusterArn=cluster_arn,
            Topic={
                'TopicName': topic_name,
                'NumberOfPartitions': num_partitions,
                'ReplicationFactor': replication_factor,
            }
        )
        logging.info(f"Created topic {topic_name}: {response}")
    except ClientError as e:
        raise kopf.PermanentError(f"Failed to create topic: {e}")

    return {"message": f"Topic {topic_name} created on {cluster_arn}"}

@kopf.on.update('msk.aws.io', 'v1', 'topics')
def update_topic(spec, **kwargs):
    # Extract the updated configuration
    cluster_arn = spec['clusterArn']
    topic_name = spec['name']
    num_partitions = spec.get('numPartitions', 1)
    replication_factor = spec.get('replicationFactor', 1)

    # Logic to handle updates (e.g., adjust num_partitions)
    # AWS MSK does not allow partition/replication factor changes via API
    # Emit a warning if changes cannot be applied dynamically
    logging.warning(f"Update to topic {topic_name}: AWS MSK does not allow dynamic reconfiguration.")
    return {"message": f"Topic {topic_name} update attempted but MSK features are limited."}


@kopf.on.delete('msk.aws.io', 'v1', 'topics')
def delete_topic(spec, **kwargs):
    cluster_arn = spec['clusterArn']
    topic_name = spec['name']

    try:
        # Delete the topic from MSK
        response = msk_client.delete_topic(ClusterArn=cluster_arn, TopicName=topic_name)
        logging.info(f"Deleted topic {topic_name}: {response}")
    except ClientError as e:
        raise kopf.PermanentError(f"Failed to delete topic: {e}")

    return {"message": f"Topic {topic_name} deleted from {cluster_arn}"}


@kopf.on.create('msk.aws.io', 'v1', 'acls')
def create_acl(spec, **kwargs):
    cluster_arn = spec['clusterArn']
    topic_name = spec['topicName']
    principal = spec['principal']
    operation = spec['operation']
    permission = spec['permission']

    try:
        # Create an ACL for the topic
        response = msk_client.create_acl(
            ClusterArn=cluster_arn,
            ResourceName=topic_name,
            ResourceType='TOPIC',  # Specific to topics
            Principal=principal,
            Operation=operation,  # Examples: "WRITE", "READ", etc.
            Permission=permission  # Examples: "ALLOW", "DENY"
        )
        logging.info(f"Created ACL for {topic_name} and principal {principal}: {response}")
    except ClientError as e:
        raise kopf.PermanentError(f"Failed to create ACL: {e}")

    return {"message": f"ACL created for topic {topic_name}, principal {principal}"}


@kopf.on.delete('msk.aws.io', 'v1', 'acls')
def delete_acl(spec, **kwargs):
    cluster_arn = spec['clusterArn']
    topic_name = spec['topicName']
    principal = spec['principal']
    operation = spec['operation']

    try:
        # Delete the ACL for the topic
        response = msk_client.delete_acl(
            ClusterArn=cluster_arn,
            ResourceName=topic_name,
            ResourceType='TOPIC',  # Specific to topics
            Principal=principal,
            Operation=operation
        )
        logging.info(f"Deleted ACL for {topic_name} and principal {principal}: {response}")
    except ClientError as e:
        raise kopf.PermanentError(f"Failed to delete ACL: {e}")

    return {"message": f"ACL deleted for topic {topic_name}, principal {principal}"}

@kopf.on.update('msk.aws.io', 'v1', 'acls')
def update_acl(spec, **kwargs):
    cluster_arn = spec['clusterArn']
    topic_name = spec['topicName']
    principal = spec['principal']
    operation = spec['operation']
    permission = spec['permission']

    # For simplification: Delete the existing ACL and recreate it
    try:
        # Delete the old ACL (pseudo-code assumes previous parameters are stored)
        msk_client.delete_acl(
            ClusterArn=cluster_arn,
            ResourceName=topic_name,
            ResourceType='TOPIC',
            Principal=principal,
            Operation=operation,
        )
        # Create the updated ACL
        msk_client.create_acl(
            ClusterArn=cluster_arn,
            ResourceName=topic_name,
            ResourceType='TOPIC',
            Principal=principal,
            Operation=operation,
            Permission=permission,
        )
        logging.info(f"Updated ACL for {topic_name} and principal {principal}")
    except ClientError as e:
        raise kopf.PermanentError(f"Failed to update ACL: {e}")

    return {"message": f"ACL updated for topic {topic_name}, principal {principal}"}