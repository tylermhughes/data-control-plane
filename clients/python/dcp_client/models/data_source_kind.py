from enum import StrEnum


class DataSourceKind(StrEnum):
    BETA_USERS = "beta_users"
    ENTERPRISE_WORKFLOW = "enterprise_workflow"
    EXPERT_NETWORK = "expert_network"
    HUMAN_VENDOR = "human_vendor"
    LICENSED_DATASET = "licensed_dataset"
    RL_ENVIRONMENT = "rl_environment"
    SYNTHETIC = "synthetic"

    def __str__(self) -> str:
        return str(self.value)
