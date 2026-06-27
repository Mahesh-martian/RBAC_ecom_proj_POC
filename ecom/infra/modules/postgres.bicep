// PostgreSQL Flexible Server module

param serverName string
param location string
param administratorLogin string
@secure()
param administratorLoginPassword string
param skuName string = 'Standard_B1ms'
param storageSizeGB int = 32
param backupRetentionDays int = 7
param geoRedundantBackup bool = false
@description('Databases to create on the server (one per microservice).')
param databaseNames array = [
  'ecommerce'
  'shopease'
]
param tags object = {}

// PostgreSQL Server
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: serverName
  location: location
  tags: tags
  sku: {
    name: skuName
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: administratorLogin
    administratorLoginPassword: administratorLoginPassword
    version: '15'
    storage: {
      storageSizeGB: storageSizeGB
    }
    backup: {
      backupRetentionDays: backupRetentionDays
      geoRedundantBackup: geoRedundantBackup ? 'Enabled' : 'Disabled'
    }
    network: {
      delegatedSubnetResourceId: ''
      privateDnsZoneArmResourceId: ''
    }
    highAvailability: {
      mode: 'Disabled'
    }
    maintenanceWindow: {
      customWindow: 'Disabled'
      dayOfWeek: 0
      startHour: 0
      startMinute: 0
    }
  }
}

// Firewall rule to allow Azure services
resource allowAzureServices 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-12-01-preview' = {
  parent: postgresServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// One database per microservice (ecommerce for rag-api, shopease for shopease-api)
resource databases 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = [
  for dbName in databaseNames: {
    parent: postgresServer
    name: dbName
    properties: {
      charset: 'UTF8'
      collation: 'en_US.utf8'
    }
  }
]

// Outputs
output fullyQualifiedDomainName string = postgresServer.properties.fullyQualifiedDomainName
output serverId string = postgresServer.id
output ecommerceConnectionString string = 'postgresql+asyncpg://${administratorLogin}:${administratorLoginPassword}@${postgresServer.properties.fullyQualifiedDomainName}:5432/ecommerce?ssl=require'
output shopeaseConnectionString string = 'postgresql+asyncpg://${administratorLogin}:${administratorLoginPassword}@${postgresServer.properties.fullyQualifiedDomainName}:5432/shopease?ssl=require'
