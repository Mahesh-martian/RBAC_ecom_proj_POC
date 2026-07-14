// Azure Cache for Redis — event-bus transport (Redis Streams) for the async worker
// plus general cache / rate-limit store. The worker consumes the
// `stream:payment.succeeded` stream; KEDA scales the worker on its pending length.

param name string
param location string
@description('Redis SKU: Basic | Standard | Premium')
param skuName string = 'Standard'
@description('Capacity: 0-6 for Basic/Standard (C-family), 1-5 for Premium (P-family)')
param capacity int = 1
param tags object = {}

resource redis 'Microsoft.Cache/redis@2023-08-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: skuName
      family: skuName == 'Premium' ? 'P' : 'C'
      capacity: capacity
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    redisConfiguration: {
      // Keep keyspace small; streams are trimmed by the producer/worker.
      'maxmemory-policy': 'volatile-lru'
    }
  }
}

// rediss:// (TLS) connection string for application clients (redis-py / KEDA).
var primaryKey = redis.listKeys().primaryKey

output hostName string = redis.properties.hostName
output sslPort int = redis.properties.sslPort
output resourceId string = redis.id
output connectionString string = 'rediss://:${primaryKey}@${redis.properties.hostName}:${redis.properties.sslPort}/0'
// Host:port form KEDA's redis-streams scaler expects in `address`.
output kedaAddress string = '${redis.properties.hostName}:${redis.properties.sslPort}'
output primaryKey string = primaryKey
