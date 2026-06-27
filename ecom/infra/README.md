# Infrastructure as Code - E-Commerce API on Azure

This directory contains Bicep templates for deploying the E-Commerce API to Azure Container Apps.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         Azure Container Apps (Managed)              │
│  ┌──────────────────────────────────────────────┐   │
│  │  E-Commerce API Container App                │   │
│  │  - FastAPI application                       │   │
│  │  - Auto-scaling (2-10 replicas)              │   │
│  │  - HTTPS ingress on port 8000                │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
         ↓                                    ↓
  ┌──────────────┐              ┌──────────────────────┐
  │ PostgreSQL   │              │ Application Insights │
  │ Flexible     │              │ & Log Analytics      │
  │ Server       │              │                      │
  └──────────────┘              └──────────────────────┘
         ↓
  ┌──────────────────┐
  │ Azure Storage    │
  │ (Product Images) │
  └──────────────────┘
```

## File Structure

```
infra/
├── main.bicep                    # Main orchestrator template
├── parameters.json               # Default parameter values
├── parameters.prod.json          # Production override parameters
├── README.md                     # This file
└── modules/
    ├── postgres.bicep            # PostgreSQL Flexible Server
    ├── storage.bicep             # Azure Storage Account
    ├── logging.bicep             # Log Analytics Workspace
    ├── monitoring.bicep          # Application Insights
    ├── keyvault.bicep            # Azure Key Vault
    ├── acr.bicep                 # Azure Container Registry
    ├── containerapp-env.bicep    # Container App Environment
    └── ecom-api.bicep            # E-Commerce API Container App
```

## Deployment

### Prerequisites

- Azure CLI installed and logged in
- Bicep CLI (installed with recent Azure CLI versions)
- Appropriate permissions to create resources

### Quick Deploy (Development)

```bash
# Set variables
RESOURCE_GROUP="fashionstore-rg"
LOCATION="eastus"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Deploy infrastructure
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file main.bicep \
  --parameters parameters.json
```

### Production Deploy

```bash
# Create production resource group
az group create --name fashionstore-prod-rg --location eastus

# Deploy with production parameters
az deployment group create \
  --resource-group fashionstore-prod-rg \
  --template-file main.bicep \
  --parameters parameters.prod.json
```

### Custom Parameters

Override specific values:

```bash
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file main.bicep \
  --parameters parameters.json \
    projectName=mystore \
    environment=staging \
    location=westus2
```

## Post-Deployment Steps

### 1. Build and Push Container Image

```bash
# Get ACR login credentials
ACR_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main \
  --query properties.outputs.containerRegistryUrl.value -o tsv)

# Login to ACR
az acr login --name $ACR_NAME

# Build and push image
docker build -t $ACR_NAME/fashionstore-ecom:latest -f ../Dockerfile ..
docker push $ACR_NAME/fashionstore-ecom:latest
```

### 2. Update Container App

```bash
# The Container App will automatically pull the latest image
# Monitor deployment status:
az containerapp show \
  --resource-group $RESOURCE_GROUP \
  --name fashionstore-prod-api \
  --query properties.latestRevisionFqdn
```

### 3. Configure Secrets

Add secrets to Key Vault:

```bash
KEY_VAULT_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main \
  --query properties.outputs.? -o tsv)

# Add Stripe keys
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name stripe-api-key \
  --value sk_live_your_key

# Add JWT secret
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name jwt-secret \
  --value "your-production-secret-minimum-32-chars"
```

### 4. Configure Custom Domain (Optional)

```bash
# Add custom domain to Container App
az containerapp ingress cors update \
  --resource-group $RESOURCE_GROUP \
  --name fashionstore-prod-api \
  --allowed-origins "https://fashionstore.com" "https://www.fashionstore.com"
```

## Monitoring & Observability

### View Application Logs

```bash
# Get latest logs from Application Insights
az monitor app-insights query \
  --app $(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name main \
    --query properties.outputs.appInsightsKey.value -o tsv) \
  --analytics-query "traces | take 50"
```

### Container App Logs

```bash
# Stream logs in real-time
az containerapp logs show \
  --resource-group $RESOURCE_GROUP \
  --name fashionstore-prod-api \
  --follow
```

### Performance Metrics

```bash
# View Container App metrics
az monitor metrics list \
  --resource /subscriptions/{subId}/resourceGroups/{rg}/providers/Microsoft.App/containerApps/fashionstore-prod-api \
  --metric "EffectiveInboundBandwidth" "EffectiveOutboundBandwidth" "CpuUsagePercentage" "MemoryUsagePercentage"
```

## Scaling Configuration

### Current Configuration

- **Minimum replicas**: 2 (for high availability)
- **Maximum replicas**: 10 (auto-scaling limit)
- **CPU threshold**: 50% (scale up when exceeded)
- **Memory threshold**: 70% (scale up when exceeded)

### Adjust Scaling

Edit `ecom-api.bicep` and modify the `scale` section:

```bicep
scale: {
  minReplicas: 2
  maxReplicas: 10
  rules: [
    {
      name: 'cpu-scaling'
      custom: {
        metric: 'cpu'
        threshold: '50'  // Adjust this value
      }
    }
  ]
}
```

Then redeploy:

```bash
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file main.bicep \
  --parameters parameters.json
```

## Networking

### Ingress Configuration

- **Type**: External (public internet)
- **Port**: 8000
- **Transport**: auto (HTTP/HTTPS)
- **Protocol**: HTTPS enforced

### CORS

Configure allowed origins in `ecom-api.bicep` `CORS_ORIGINS` environment variable.

### Firewall Rules

PostgreSQL firewall:
- ✅ Allow Azure services (Container Apps)
- ✅ Requires SSL connection
- ❌ No public internet access

## Security

### Managed Identity

- Container App uses User-Assigned Managed Identity
- Automatic secret rotation via Key Vault

### Secrets Management

All sensitive values stored in Azure Key Vault:
- Database credentials
- JWT secret
- Stripe API keys
- CORS origins

### Network Security

- ✅ HTTPS enforced for Container App
- ✅ SSL required for PostgreSQL connections
- ✅ Storage account private endpoint ready
- ✅ Key Vault firewall can be configured

## Cost Optimization

### Current Configuration

| Resource | SKU | Estimated Cost/Month |
|----------|-----|---------------------|
| Container Apps | Consumption | $10-50 |
| PostgreSQL | Standard_B1ms | $30-50 |
| Application Insights | Per GB ingestion | $5-20 |
| Storage Account | Standard LRS | $5-10 |
| Key Vault | Standard | $0.50 |
| **Total** | - | **$50-130** |

### Cost Reduction Tips

1. **Container Apps**: Use more efficient memory allocation
2. **PostgreSQL**: Use smaller compute tier (B-series)
3. **Storage**: Archive old images to blob tiers
4. **Monitoring**: Adjust retention policies

## Troubleshooting

### Deployment Fails

```bash
# Check deployment status
az deployment group list --resource-group $RESOURCE_GROUP \
  --query "[].{Name:name, State:properties.provisioningState}"

# View detailed errors
az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main \
  --query properties.error
```

### Container App Won't Start

```bash
# Check Container App revision status
az containerapp revision list \
  --resource-group $RESOURCE_GROUP \
  --name fashionstore-prod-api \
  --query "[].{Revision:name, Status:properties.provisioningState}"

# View Container App logs
az containerapp logs show \
  --resource-group $RESOURCE_GROUP \
  --name fashionstore-prod-api
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity
psql -h <server>.postgres.database.azure.com \
     -U pgadmin@<server> \
     -d ecommerce \
     -c "SELECT 1;"
```

## Cleanup

### Delete All Resources

```bash
# WARNING: This deletes everything
az group delete --name fashionstore-prod-rg --yes --no-wait
```

### Delete Specific Resources

```bash
# Delete Container App
az containerapp delete \
  --resource-group $RESOURCE_GROUP \
  --name fashionstore-prod-api

# Delete database
az postgres flexible-server delete \
  --resource-group $RESOURCE_GROUP \
  --name fashionstore-prod-db --yes
```

## Next Steps

1. **[Deploy Frontend React SPA](../ecom-frontend/README.md)** - Deploy React frontend
2. **[Setup CI/CD Pipeline](../.github/workflows/)** - Automate deployments
3. **[Configure Custom Domain](https://learn.microsoft.com/azure/container-apps/custom-domain)** - Add custom domain
4. **[Setup WAF](https://learn.microsoft.com/azure/web-application-firewall/ag/overview)** - Add Web Application Firewall

## References

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [PostgreSQL Flexible Server](https://learn.microsoft.com/azure/postgresql/flexible-server/)
- [Application Insights](https://learn.microsoft.com/azure/azure-monitor/app/app-insights-overview)
