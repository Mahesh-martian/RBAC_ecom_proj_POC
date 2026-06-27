// Azure Key Vault module

param name string
param location string
param tags object = {}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: []
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: false
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

// PostgreSQL password secret
resource postgresPassword 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'postgres-password'
  properties: {
    value: 'GenerateSecurePassword123!'
  }
}

// Outputs
output vaultId string = keyVault.id
output vaultUri string = keyVault.properties.vaultUri
output postgresPassword string = postgresPassword.properties.value
