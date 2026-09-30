// Central configuration for the streaming JavaScript service.

// Export the port and service name. {8102} is the default port for this service, but it can be overridden by setting the STREAMING_PORT environment variable.

module.exports = { port: Number(process.env.STREAMING_PORT || 8110), serviceName: 'streaming-service' }; 
