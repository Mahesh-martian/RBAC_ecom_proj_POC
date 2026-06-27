// Azure Container Registry module

param name string
param location string
param adminUserEnabled bool = true
param tags object = {}

// Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: adminUserEnabled
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      trustPolicy: {
        clrEnabled: false
        status: 'disabled'
      }
      retentionPolicy: {
        days: 30
        enabled: true
      }
    }
  }
}

// Get credentials
var acrCredentials = acr.listCredentials()

// Outputs
output registryId string = acr.id
output loginServer string = acr.properties.loginServer
output adminUsername string = acrCredentials.username
output adminPassword string = acrCredentials.passwords[0].value
