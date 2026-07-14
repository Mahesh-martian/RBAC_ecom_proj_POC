// Container App Environment module

param name string
param location string
param workspaceResourceId string
param appInsightsConnectionString string
param tags object = {}

// Container App Environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2023-04-01-preview' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(workspaceResourceId, '2021-12-01-preview').customerId
        sharedKey: listKeys(workspaceResourceId, '2021-12-01-preview').primarySharedKey
      }
    }
  }
}

// Outputs
output environmentId string = containerAppEnvironment.id
output environmentName string = containerAppEnvironment.name
output defaultDomain string = containerAppEnvironment.properties.defaultDomain
