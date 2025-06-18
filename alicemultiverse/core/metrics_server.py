"""Prometheus metrics server for AliceMultiverse."""

import asyncio

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse

# from ..database.config import get_pool_monitor
# from ..database.pool_manager import get_pool_diagnostics
from ..providers.health_monitor import health_monitor
from .metrics import get_metrics, get_metrics_content_type
from .structured_logging import get_logger

logger = get_logger(__name__)

# Create FastAPI app for metrics
app = FastAPI(title="AliceMultiverse Metrics", version="1.0.0")


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    # Update dynamic metrics before serving
    await update_dynamic_metrics()

    # Get metrics data
    metrics_data = get_metrics()

    return Response(
        content=metrics_data,
        media_type=get_metrics_content_type()
    )


@app.get("/health")
async def health_endpoint():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "alicemultiverse-metrics"
    }


async def update_dynamic_metrics():
    """Update metrics that need to be fetched dynamically."""
    from ..core.metrics import update_provider_health_metrics

    logger.debug("Database pool metrics not available")

    # Update provider health metrics
    try:
        for provider_name, breaker in health_monitor.circuit_breakers.items():
            health_data = {
                'is_healthy': breaker.metrics.is_healthy,
                'circuit_state': breaker.state.value,
                'error_rate': breaker.metrics.failure_rate
            }
            update_provider_health_metrics(provider_name, health_data)
    except Exception as e:
        logger.error(
            "Failed to update provider health metrics",
            error=str(e),
            exc_info=True
        )


class MetricsServer:
    """Manages the Prometheus metrics server."""

    def __init__(self, host: str = "0.0.0.0", port: int = 9090) -> None:
        """Initialize metrics server.

        Args:
            host: Host to bind to
            port: Port to listen on
        """
        self.host = host
        self.port = port
        self._server_task: asyncio.Task | None = None

    async def start(self):
        """Start the metrics server."""
        logger.info(
            "Starting Prometheus metrics server",
            host=self.host,
            port=self.port,
            url=f"http://{self.host}:{self.port}/metrics"
        )

        # Start periodic metric updates
        asyncio.create_task(self._update_metrics_loop())

        # Run the server
        config = uvicorn.Config(
            app,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False
        )
        server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(server.serve())

    async def stop(self):
        """Stop the metrics server."""
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics server stopped")

    async def _update_metrics_loop(self):
        """Periodically update dynamic metrics."""
        while True:
            try:
                await update_dynamic_metrics()
                await asyncio.sleep(10)  # Update every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Error in metrics update loop",
                    error=str(e),
                    exc_info=True
                )
                await asyncio.sleep(10)


# CLI command to run metrics server
def run_metrics_server(host: str = "0.0.0.0", port: int = 9090) -> None:
    """Run the metrics server standalone.

    Args:
        host: Host to bind to
        port: Port to listen on
    """
    import asyncio

    async def main():
        server = MetricsServer(host, port)
        await server.start()

        # Keep running until interrupted
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down metrics server")
            await server.stop()

    asyncio.run(main())


if __name__ == "__main__":
    # Run directly
    run_metrics_server()
