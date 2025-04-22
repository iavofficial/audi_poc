import kopf
import boto3
import secrets
import string
from kubernetes import client, config

# Load K8s config
try:
    # For local testing
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

k8s_client = client.CoreV1Api()

# AWS RDS client, adjust region_name if necessary
rds_client = boto3.client('rds', region_name='eu-central-1')


def generate_password(length=16):
    """
    Generate strong random password using letters, digits and special chars.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_"
    return ''.join(secrets.choice(alphabet) for i in range(length))


def create_k8s_secret(namespace, name, data):
    """
    Create or update K8s secret to store credentials securely.
    """
    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
        type="Opaque",
        data={key: data[key].encode("utf-8") for key in data},
    )
    try:
        k8s_client.create_namespaced_secret(namespace=namespace, body=secret)
    except client.exceptions.ApiException as e:
        if e.status == 409:  # Conflict - Secret already exists, update it
            k8s_client.replace_namespaced_secret(name=name, namespace=namespace, body=secret)
        else:
            raise e


@kopf.on.create('rdsinstances.aws.audi.de', version='v1')
def create_rds_instance(spec, namespace, name, **kwargs):
    """
    Handler for creating RDS instances. Generates credentials, provisions the DB,
    and saves credentials in a K8s Secret.
    """
    # Extract spec details
    db_name = spec.get('name')
    stage = spec.get('stage')
    engine = spec.get('engine')
    instance_class = spec.get('instanceClass', 'db.t3.micro')
    allocated_storage = spec.get('allocatedStorage', 20)
    username = spec.get('username', 'admin')  # Default username

    # Generate strong random password
    password = generate_password()

    # Generate unique DB instance identifier (name + stage)
    db_instance_identifier = f"{name}-{stage}"

    # Add tags for stage (pre-live, dev, int)
    tags = [{'Key': 'Environment', 'Value': stage}]

    # Provision the RDS DB instance on AWS
    try:
        response = rds_client.create_db_instance(
            DBName=db_name,
            DBInstanceIdentifier=db_instance_identifier,
            Engine=engine,
            MasterUsername=username,
            MasterUserPassword=password,
            DBInstanceClass=instance_class,
            AllocatedStorage=allocated_storage,
            Tags=tags,
        )
    except Exception as e:
        raise kopf.TemporaryError(f"RDS instance creation error: {e}", delay=30)

    # Get the DB endpoint address (might be pending during creation)
    db_instance_endpoint = response['DBInstance'].get('Endpoint', {}).get('Address', 'PENDING')

    # Save credentials in the namespace as k8s secret
    create_k8s_secret(
        namespace=namespace,
        name=f"{name}-db-credentials",
        data={
            "username": username,
            "password": password,
            "endpoint": db_instance_endpoint,
            "db_name": db_name,
        }
    )

    return {'message': f'RDS instance {db_instance_identifier} successfully created.'}


@kopf.on.delete('rdsinstances.aws.audi.de', version='v1')
def delete_rds_instance(spec, name, namespace, **kwargs):
    """
    Delete RDS instances when not needed.
    """
    stage = spec.get('stage')
    db_instance_identifier = f"{name}-{stage}"

    # Delete RDS instance on AWS
    try:
        rds_client.delete_db_instance(
            DBInstanceIdentifier=db_instance_identifier,
            SkipFinalSnapshot=True
        )
    except Exception as e:
        raise kopf.TemporaryError(f"Error deleting RDS instance: {e}", delay=30)

    # Delete the associated K8s secret
    try:
        k8s_client.delete_namespaced_secret(name=f"{name}-db-credentials", namespace=namespace)
    except client.exceptions.ApiException as e:
        if e.status != 404:  # 404 Secret already deleted or doesn't exist
            raise e
    return {'message': f'RDS instance {db_instance_identifier} successfully deleted.'}
