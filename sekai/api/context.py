from sekai.api.configs import ServerConfig

server_config = ServerConfig.load("server")
cache_ttl = server_config.cache_ttl.total_seconds()
