# Forge Production Deployment Guide

> [!IMPORTANT]
> This guide outlines the necessary steps and best practices for deploying Forge in a production environment. Please ensure you have reviewed all security and scaling considerations before deployment.

## Secrets Management

In a production environment, hardcoding secrets or storing them in plain text `.env` files is highly discouraged. We recommend using a dedicated secrets management solution to handle sensitive data such as LLM API keys, database credentials, and signing certificates.

### Recommended Solutions
- **HashiCorp Vault:** Provides robust secret storage, dynamic secret generation, and strong access control policies.
- **AWS Secrets Manager / GCP Secret Manager:** Ideal if you are deploying within an AWS or GCP ecosystem. They integrate seamlessly with IAM roles for secure, identity-based access.

> [!CAUTION]
> Never commit LLM API keys to your version control system. A compromised key can result in substantial financial loss and unauthorized access to your AI models.

## Authentication and Authorization

While JWTs are sufficient for local development and simple setups, enterprise deployments require more robust identity management.

### Advanced Authentication Protocols
- **OAuth 2.0 / OIDC:** Implement OpenID Connect for federated authentication, allowing users to log in via enterprise identity providers (IdPs) like Okta, Auth0, or Azure AD.
- **Role-Based Access Control (RBAC):** Ensure that access to sensitive knowledge graphs and CLI operations is restricted based on user roles defined in your IdP.

> [!TIP]
> Use short-lived access tokens and configure refresh token rotation to minimize the risk of token theft.

## Scaling the Vector Database

Forge relies heavily on vector databases for similarity search and knowledge retrieval. For production, a single instance is often insufficient.

### Qdrant Clustering and Replication
- **Clustering:** Deploy Qdrant in a distributed cluster to handle increased read/write loads and ensure high availability.
- **Replication:** Configure replication across multiple nodes to prevent data loss in the event of a hardware failure.
- **Resource Allocation:** Ensure sufficient RAM for vector index caching, as disk I/O can become a bottleneck during large-scale semantic searches.

> [!NOTE]
> Refer to the [Qdrant Distributed Deployment Documentation](https://qdrant.tech/documentation/guides/distributed_deployment/) for specific configuration parameters.

## Orchestration

Managing Forge's microservices, background workers, and databases requires a reliable container orchestration platform.

### Kubernetes (K8s) Basics for Forge
- **Deployments:** Use Kubernetes Deployments to manage the lifecycle of Forge API servers and worker nodes.
- **StatefulSets:** Utilize StatefulSets for the Qdrant database to maintain stable network identities and persistent storage.
- **Services & Ingress:** Configure ClusterIP services for internal communication and Ingress controllers (like NGINX or Traefik) to expose the Forge API securely to external traffic.

### Docker Swarm Alternative
For smaller teams or simpler setups, Docker Swarm offers an easier learning curve while still providing essential orchestration features like service discovery and scaling.

> [!WARNING]
> Ensure network policies are strictly configured to prevent unauthorized access between microservices, especially restricting direct access to the vector database from the public internet.
