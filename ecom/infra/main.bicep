// Main Bicep template for the ShopEase microservices stack on Azure.
// Deploys: PostgreSQL (ecommerce + shopease DBs), Azure Cache for Redis (event
// bus + cache), ACR, Container Apps Environment, and four Container Apps:
//   - shopease-api  (storefront API, external :5002)
//   - rag-api       (RAG service, external :8000)
//   - worker        (async event consumer, no ingress, KEDA redis-streams scaler)
//   - frontend      (Next.js storefront, external :3000)
//
// Deploy with:
//   az deployment group create -g <rg> --template-file main.bicep --parameters parameters.json

param projectName string = 'shopease'
param environment string = 'dev' // dev, staging, prod
param location string = resourceGroup().location

@description('Container image tag to deploy across services.')
param imageTag string = 'latest'

// Azure OpenAI / AI Search wiring for the RAG service (set via parameters/CI secrets).
@secure()
param azureOpenAiKey string = ''
param azureOpenAiEndpoint string = ''
param azureOpenAiChatDeployment string = ''
param azureOpenAiEmbeddingDeployment string = ''
param azureOpenAiApiVersion string = '2024-12-01-preview'
@secure()
param azureSearchKey string = ''
param azureSearchEndpoint string = ''

@description('Deployment timestamp tag (leave as default).')
param deploymentTime string = utcNow('u')

// Generate unique suffix for global resources
var uniqueSuffix = substring(uniqueString(resourceGroup().id), 0, 6)
var appName = '${projectName}-${environment}'

// Resource naming
var postgresName = '${appName}-db'
var redisName = '${appName}-redis-${uniqueSuffix}'
var acrName = '${projectName}${environment}acr'
var containerAppEnvName = '${appName}-env'
var ragApiName = '${appName}-rag'
var shopeaseApiName = '${appName}-api'
var workerName = '${appName}-worker'
var frontendName = '${appName}-frontend'
var keyVaultName = '${appName}-kv-${uniqueSuffix}'
var appInsightsName = '${appName}-insights'
var logAnalyticsName = '${appName}-logs'

// Container images (worker shares the rag image with a different command)
var ragImage = '${acr.outputs.loginServer}/${projectName}-rag:${imageTag}'
var shopeaseImage = '${acr.outputs.loginServer}/${projectName}-shopease:${imageTag}'
var frontendImage = '${acr.outputs.loginServer}/${projectName}-frontend:${imageTag}'

// Tags for all resources
var commonTags = {
  project: projectName
  environment: environment
  createdDate: deploymentTime
}

// ============ Foundation ============

module logAnalytics 'modules/logging.bicep' = {
  name: 'logging'
  params: {
    name: logAnalyticsName
    location: location
    tags: commonTags
  }
}

module appInsights 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    name: appInsightsName
    location: location
    workspaceResourceId: logAnalytics.outputs.workspaceId
    tags: commonTags
  }
}

module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    name: keyVaultName
    location: location
    tags: commonTags
  }
}

// ============ Data layer ============

module postgres 'modules/postgres.bicep' = {
  name: 'postgres'
  params: {
    serverName: postgresName
    location: location
    administratorLogin: 'pgadmin'
    administratorLoginPassword: keyVault.outputs.postgresPassword
    databaseNames: [
      'ecommerce'
      'shopease'
    ]
    tags: commonTags
  }
}

module redis 'modules/redis.bicep' = {
  name: 'redis'
  params: {
    name: redisName
    location: location
    skuName: environment == 'prod' ? 'Standard' : 'Basic'
    capacity: environment == 'prod' ? 1 : 0
    tags: commonTags
  }
}

module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    name: acrName
    location: location
    tags: commonTags
  }
}

// ============ Container Apps Environment ============

module containerAppEnv 'modules/containerapp-env.bicep' = {
  name: 'containerapp-env'
  params: {
    name: containerAppEnvName
    location: location
    workspaceResourceId: logAnalytics.outputs.workspaceId
    appInsightsConnectionString: appInsights.outputs.connectionString
    tags: commonTags
  }
}

// Deterministic public URLs (names + env default domain are known up front, so we
// can wire cross-service URLs without creating a circular module dependency).
var defaultDomain = containerAppEnv.outputs.defaultDomain
var ragApiUrl = 'https://${ragApiName}.${defaultDomain}'
var shopeaseApiUrl = 'https://${shopeaseApiName}.${defaultDomain}'
var frontendUrl = 'https://${frontendName}.${defaultDomain}'
var corsOriginsJson = '["${frontendUrl}"]'

// ============ Container Apps ============

// ShopEase storefront API (calls rag-api for the chatbot)
module shopeaseApi 'modules/shopease-api.bicep' = {
  name: 'shopease-api'
  params: {
    containerAppName: shopeaseApiName
    location: location
    containerAppEnvId: containerAppEnv.outputs.environmentId
    acrLoginServer: acr.outputs.loginServer
    shopeaseImage: shopeaseImage
    databaseUrl: postgres.outputs.shopeaseConnectionString
    ragServiceUrl: ragApiUrl
    corsOrigins: corsOriginsJson
    tags: commonTags
  }
}

// RAG service (grounds answers; sources products from shopease-api; emits events)
module ragApi 'modules/ecom-api.bicep' = {
  name: 'rag-api'
  params: {
    containerAppName: ragApiName
    location: location
    containerAppEnvId: containerAppEnv.outputs.environmentId
    acrLoginServer: acr.outputs.loginServer
    ragImage: ragImage
    databaseUrl: postgres.outputs.ecommerceConnectionString
    redisConnectionString: redis.outputs.connectionString
    shopeaseApiUrl: '${shopeaseApiUrl}/api/v1'
    corsOrigins: corsOriginsJson
    azureOpenAiKey: azureOpenAiKey
    azureOpenAiEndpoint: azureOpenAiEndpoint
    azureOpenAiChatDeployment: azureOpenAiChatDeployment
    azureOpenAiEmbeddingDeployment: azureOpenAiEmbeddingDeployment
    azureOpenAiApiVersion: azureOpenAiApiVersion
    azureSearchKey: azureSearchKey
    azureSearchEndpoint: azureSearchEndpoint
    tags: commonTags
  }
}

// Async event worker (consumes Redis stream; KEDA scale-to-zero)
module worker 'modules/worker.bicep' = {
  name: 'worker'
  params: {
    containerAppName: workerName
    location: location
    containerAppEnvId: containerAppEnv.outputs.environmentId
    acrLoginServer: acr.outputs.loginServer
    workerImage: ragImage
    databaseUrl: postgres.outputs.ecommerceConnectionString
    redisConnectionString: redis.outputs.connectionString
    redisAddress: redis.outputs.kedaAddress
    redisPassword: redis.outputs.primaryKey
    tags: commonTags
  }
}

// Next.js storefront
module frontend 'modules/frontend.bicep' = {
  name: 'frontend'
  params: {
    containerAppName: frontendName
    location: location
    containerAppEnvId: containerAppEnv.outputs.environmentId
    acrLoginServer: acr.outputs.loginServer
    frontendImage: frontendImage
    tags: commonTags
  }
}

// ============ Outputs ============

output frontendUrl string = frontend.outputs.url
output shopeaseApiUrl string = shopeaseApi.outputs.url
output ragApiUrl string = ragApi.outputs.url
output databaseHost string = postgres.outputs.fullyQualifiedDomainName
output redisHost string = redis.outputs.hostName
output containerRegistryUrl string = acr.outputs.loginServer
output logAnalyticsWorkspaceId string = logAnalytics.outputs.workspaceId

