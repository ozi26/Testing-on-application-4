// Central configuration for the streaming JavaScript service.
// Export the port and service name. {8102} is the default port for this service, but it can be overridden by setting the STREAMING_PORT environment variable.

// This is just a harmless comment to test the analyzer...

module.exports = { port: Number(process.env.STREAMING_PORT || 8102), serviceName: 'streaming-service' }; 
