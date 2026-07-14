// ShopEase storefront API Container App (FastAPI, port 5002).
// External ingress (browser + frontend call it). Talks to the RAG service for the
// shopping-assistant chatbot via RAG_SERVICE_URL.

param containerAppName string
param location string
param containerAppEnvId string
param acrLoginServer string
param shopeaseImage string
@secure()
param databaseUrl string
@description('Internal/External URL of the RAG service for the chatbot.')
param ragServiceUrl string
param corsOrigins string
param tags object = {}

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${containerAppName}-identity'
  location: location
  tags: tags
}

resource shopeaseApp 'Microsoft.App/containerApps@2023-04-01-preview' = {
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
        targetPort: 5002
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
          name: 'jwt-secret'
          value: 'your-production-jwt-secret-minimum-32-chars'
        }
        {
          name: 'jwt-refresh-secret'
          value: 'your-production-refresh-secret-minimum-32-chars'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'shopease-api'
          image: shopeaseImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'NODE_ENV'
              value: 'production'
            }
            {
              name: 'PORT'
              value: '5002'
            }
            {
              name: 'DATABASE_URL'
              secretRef: 'db-url'
            }
            {
              name: 'JWT_SECRET'
              secretRef: 'jwt-secret'
            }
            {
              name: 'JWT_REFRESH_TOKEN_SECRET'
              secretRef: 'jwt-refresh-secret'
            }
            {
              name: 'RAG_SERVICE_URL'
              value: ragServiceUrl
            }
            {
              name: 'CORS_ORIGINS'
              value: corsOrigins
            }
          ]
          probes: [
            {
              type: 'liveness'
              httpGet: {
                path: '/health'
                port: 5002
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
                port: 5002
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
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

output fqdn string = shopeaseApp.properties.configuration.ingress.fqdn
output url string = 'https://${shopeaseApp.properties.configuration.ingress.fqdn}'
output containerAppId string = shopeaseApp.id
