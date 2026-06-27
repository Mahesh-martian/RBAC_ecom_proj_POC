// Async event worker Container App.
// No ingress — it consumes the Redis stream `stream:payment.succeeded` (group
// `ecom-workers`) and performs idempotent fulfilment (inventory + email).
// Scaled by KEDA's redis-streams scaler on the consumer group's pending length,
// including scale-to-zero when the stream is idle.

param containerAppName string
param location string
param containerAppEnvId string
param acrLoginServer string
param workerImage string
@secure()
param databaseUrl string
@secure()
param redisConnectionString string
@description('Redis host:port for the KEDA scaler address.')
param redisAddress string
@secure()
param redisPassword string
param redisStream string = 'stream:payment.succeeded'
param consumerGroup string = 'ecom-workers'
param tags object = {}

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${containerAppName}-identity'
  location: location
  tags: tags
}

resource workerApp 'Microsoft.App/containerApps@2023-04-01-preview' = {
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
      // No ingress: background consumer only.
      activeRevisionsMode: 'Single'
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
          name: 'redis-password'
          value: redisPassword
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: workerImage
          command: [
            'python'
            '-m'
            'worker'
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
            {
              name: 'LOG_LEVEL'
              value: 'INFO'
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
              name: 'EVENTS_CONSUMER_GROUP'
              value: consumerGroup
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 10
        rules: [
          {
            name: 'redis-streams-scaling'
            custom: {
              type: 'redis-streams'
              metadata: {
                address: redisAddress
                stream: redisStream
                consumerGroup: consumerGroup
                pendingEntriesCount: '5'
                enableTLS: 'true'
                databaseIndex: '0'
              }
              auth: [
                {
                  secretRef: 'redis-password'
                  triggerParameter: 'password'
                }
              ]
            }
          }
        ]
      }
    }
  }
}

output containerAppId string = workerApp.id
output principalId string = managedIdentity.properties.principalId
