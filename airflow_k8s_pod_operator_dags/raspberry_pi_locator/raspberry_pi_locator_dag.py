# (C) Markham Lee
# https://github.com/MarkhamLee/productivity-music-stocks-weather-IoT-dashboard
# DAG to monitor the Raspberry Pi Locator RSS feed, and send Slack alerts when
# there are product update alerts that are less than a given maximum age.
from datetime import datetime, timedelta
from kubernetes.client import models as k8s
from airflow import DAG
from airflow.providers.cncf.kubernetes.secret import Secret
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator  # noqa: E501

# define instance specific variables
env_variables = {"MAX_AGE": "24",
                 "RPI_BASE_URL": "https://rpilocator.com/feed/?country=",  # noqa: E501
                 "RPI_PRODUCT": "PI5",
                 "RPI_COUNTRY": "US",
                 "RPI5_TABLE": "rpi_alert_data"}

resource_limits = k8s.V1ResourceRequirements(
            requests={
                'cpu': '400m',
                'memory': '256Mi'
                },
            limits={
                'cpu': '800m',
                'memory': '512Mi'
                },
            )

# load config maps from Kubernetes
configmaps = [
    k8s.V1EnvFromSource(config_map_ref=k8s.V1ConfigMapEnvSource(name="key-etl-variables"))]  # noqa: E501

# load all the required secrets from Kubernetes
secret_env1 = Secret(deploy_type="env", deploy_target="POSTGRES_USER",
                     secret="postgres-secrets", key="POSTGRES_USER")

secret_env2 = Secret(deploy_type="env", deploy_target="POSTGRES_PASSWORD",
                     secret="postgres-secrets", key="POSTGRES_PASSWORD")

secret_env3 = Secret(deploy_type="env", deploy_target="PRODUCT_WEBHOOK",
                     secret="slack-webhook-rpi-alerts",
                     key="SLACK_WEBHOOK_RPI5")

secret_env4 = Secret(deploy_type="env", deploy_target="ALERT_WEBHOOK",
                     secret="slack-webhook-pipeline-failures",
                     key="WEBHOOK_ETL_ALERTS")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 24),
    'retries': 0
}

with DAG(
    dag_id='rpi5_locator',
    schedule=timedelta(hours=1),
    default_args=default_args,
    catchup=False,
    tags=['k8s-pod-operator-container', 'Python'],
) as dag:
    k = KubernetesPodOperator(
        namespace='airflow',
        container_resources=resource_limits,
        node_selector={'node_type': 'arm64_worker'},
        image_pull_secrets=[k8s.V1LocalObjectReference("dockersecrets")],
        image="markhamlee/rpi_stock:latest",
        env_vars=env_variables,
        env_from=configmaps,
        secrets=[secret_env1, secret_env2, secret_env3, secret_env4],
        cmds=["python3"],
        arguments=["main.py"],
        name="raspberry_pi_five_locator",
        task_id="rpi5_locator_rss",
        is_delete_operator_pod=True,
        hostnetwork=False,
        get_logs=True,
        log_events_on_failure=True,
        in_cluster=True,
        startup_timeout_seconds=180
    )
