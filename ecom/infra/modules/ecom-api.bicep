// RAG service Container App (FastAPI, port 8000) — the "rag-api".
// Grounds policy answers via Azure OpenAI + AI Search, sources product
// recommendations from shopease-api, and publishes payment events to Redis.

param containerAppName string
param location string
param containerAppEnvId string
param acrLoginServer string
param ragImage string
param databaseUrl string
@secure()
param redisConnectionString string
@description('Internal/External URL of shopease-api for product recommendations.')
param shopeaseApiUrl string
param corsOrigins string
@secure()
param azureOpenAiKey string = ''
param azureOpenAiEndpoint string = ''
param azureOpenAiChatDeployment string = ''
param azureOpenAiEmbeddingDeployment string = ''
param azureOpenAiApiVersion string = '2024-12-01-preview'
@secure()
param azureSearchKey string = ''
param azureSearchEndpoint string = ''
param ragProvider string = 'hybrid'
param tags object = {}

// User-assigned managed identity
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${containerAppName}-identity'
  location: location
  tags: tags
}

// Container App - RAG service
resource ecomApiApp 'Microsoft.App/containerApps@2023-04-01-preview' = {
  name: containerAppName
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppEnvId
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
      registries: [
        {
          server: acrLoginServer
          identity: managedIdentity.id
        }
      ]
      secrets: [
        {
          name: 'db-url'
          value: databaseUrl
        }
        {
          name: 'redis-url'
          value: redisConnectionString
        }
        {
          name: 'jwt-secret'
          value: 'your-production-jwt-secret-minimum-32-chars'
        }
        {
          name: 'stripe-api-key'
          value: 'sk_live_your_stripe_key'
        }
        {
          name: 'stripe-webhook-secret'
          value: 'whsec_your_webhook_secret'
        }
        {
          name: 'azure-openai-key'
          value: azureOpenAiKey
        }
        {
          name: 'azure-search-key'
          value: azureSearchKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'rag-api'
          image: ragImage
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
            {
              name: 'DEBUG'
              value: 'false'
            }
            {
              name: 'DATABASE_URL'
              secretRef: 'db-url'
            }
            {
              name: 'REDIS_URL'
              secretRef: 'redis-url'
            }
            {
              name: 'JWT_SECRET'
              secretRef: 'jwt-secret'
            }
            {
              name: 'STRIPE_API_KEY'
              secretRef: 'stripe-api-key'
            }
            {
              name: 'STRIPE_WEBHOOK_SECRET'
              secretRef: 'stripe-webhook-secret'
            }
            {
              name: 'RAG_PROVIDER'
              value: ragProvider
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAiEndpoint
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'azure-openai-key'
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT'
              value: azureOpenAiChatDeployment
            }
            {
              name: 'AZURE_OPENAI_CHAT_DEPLOYMENT'
              value: azureOpenAiChatDeployment
            }
            {
              name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
              value: azureOpenAiEmbeddingDeployment
            }
            {
              name: 'AZURE_OPENAI_API_VERSION'
              value: azureOpenAiApiVersion
            }
            {
              name: 'AZURE_SEARCH_ENDPOINT'
              value: azureSearchEndpoint
            }
            {
              name: 'AZURE_SEARCH_ADMIN_KEY'
              secretRef: 'azure-search-key'
            }
            {
              name: 'SHOPEASE_PRODUCTS_ENABLED'
              value: 'true'
            }
            {
              name: 'SHOPEASE_API_URL'
              value: shopeaseApiUrl
            }
            {
              name: 'LOG_LEVEL'
              value: 'INFO'
            }
            {
              name: 'CORS_ORIGINS'
              value: corsOrigins
            }
            {
              name: 'PORT'
              value: '8000'
            }
          ]
          probes: [
            {
              type: 'liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 30
              timeoutSeconds: 3
              failureThreshold: 3
            }
            {
              type: 'readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 5
              periodSeconds: 10
              timeoutSeconds: 3
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: 2
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
output fqdn string = ecomApiApp.properties.configuration.ingress.fqdn
output url string = 'https://${ecomApiApp.properties.configuration.ingress.fqdn}'
output containerAppId string = ecomApiApp.id
