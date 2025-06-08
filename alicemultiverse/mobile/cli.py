"""CLI commands for mobile companion app."""

import click
import asyncio
from pathlib import Path
from typing import Optional
import qrcode
import socket

from .server import MobileServer
from .token_manager import TokenManager
from ..interface.timeline_preview import Timeline, TimelineClip


@click.group()
def mobile():
    """Manage mobile companion app."""
    pass


@mobile.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', type=int, default=8080, help='Port to listen on')
@click.option('--media-dir', type=click.Path(exists=True), help='Media directory')
def server(host: str, port: int, media_dir: Optional[str]):
    """Start mobile companion server."""
    media_path = Path(media_dir) if media_dir else None
    
    # Get local IP for mobile access
    local_ip = get_local_ip()
    
    click.echo(f"\n🚀 Starting Alice Mobile Companion Server")
    click.echo(f"=" * 50)
    click.echo(f"Local access: http://localhost:{port}")
    click.echo(f"Mobile access: http://{local_ip}:{port}")
    click.echo(f"\nGenerate access token with: alice mobile token generate")
    click.echo(f"=" * 50)
    
    server = MobileServer(
        host=host,
        port=port,
        media_dir=media_path
    )
    
    # Add sample timeline for testing
    sample_timeline = create_sample_timeline(media_path)
    if sample_timeline:
        asyncio.run(server.add_timeline("sample", sample_timeline))
    
    server.run()


@mobile.group()
def token():
    """Manage access tokens."""
    pass


@token.command()
@click.option('--name', default='default', help='Token name/description')
@click.option('--expires', type=int, default=24, help='Hours until expiration')
@click.option('--qr', is_flag=True, help='Generate QR code')
def generate(name: str, expires: int, qr: bool):
    """Generate a new access token."""
    manager = TokenManager()
    token = manager.generate_token(name, expires)
    
    click.echo(f"\n🔑 Generated Access Token")
    click.echo(f"=" * 50)
    click.echo(f"Name: {name}")
    click.echo(f"Expires: {expires} hours")
    click.echo(f"\nToken: {token}")
    click.echo(f"=" * 50)
    
    if qr:
        # Generate QR code for easy mobile scanning
        local_ip = get_local_ip()
        url = f"http://{local_ip}:8080?token={token}"
        
        qr_code = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_code.add_data(url)
        qr_code.make(fit=True)
        
        # Print QR code to terminal
        qr_code.print_ascii()
        click.echo(f"\nScan QR code or visit: {url}")


@token.command()
def list():
    """List all tokens."""
    manager = TokenManager()
    tokens = manager.list_tokens()
    
    if not tokens:
        click.echo("No tokens found.")
        return
    
    click.echo(f"\n📋 Active Tokens")
    click.echo(f"=" * 60)
    click.echo(f"{'Token':<12} {'Name':<15} {'Created':<20} {'Uses':<8}")
    click.echo(f"=" * 60)
    
    for token_id, info in tokens.items():
        created = info['created'][:19]  # Trim to date and time
        click.echo(
            f"{token_id:<12} {info['name']:<15} {created:<20} {info['usage_count']:<8}"
        )


@token.command()
@click.argument('token_prefix')
def revoke(token_prefix: str):
    """Revoke a token (provide first 8 chars)."""
    manager = TokenManager()
    
    # Find matching token
    tokens = manager.list_tokens()
    matched = None
    
    for token_id in tokens:
        if token_id.startswith(token_prefix):
            matched = token_id
            break
    
    if matched:
        # Need to find full token - this is a limitation
        click.echo(f"⚠️  Cannot revoke partial token. Need full token to revoke.")
    else:
        click.echo(f"❌ No token found matching: {token_prefix}")


@token.command()
def cleanup():
    """Remove expired tokens."""
    manager = TokenManager()
    removed = manager.cleanup_expired()
    
    if removed > 0:
        click.echo(f"✅ Removed {removed} expired tokens")
    else:
        click.echo("No expired tokens to remove")


@mobile.command()
@click.option('--demo', is_flag=True, help='Load demo timeline')
def test(demo: bool):
    """Test mobile companion connectivity."""
    local_ip = get_local_ip()
    
    click.echo(f"\n📱 Mobile Companion Test")
    click.echo(f"=" * 50)
    click.echo(f"Local IP: {local_ip}")
    click.echo(f"Default port: 8080")
    
    # Test if server is running
    import requests
    try:
        response = requests.get(f"http://localhost:8080", timeout=2)
        if response.status_code == 200:
            click.echo("✅ Server is running")
        else:
            click.echo("❌ Server returned error")
    except:
        click.echo("❌ Server is not running")
        click.echo("\nStart server with: alice mobile server")
    
    if demo:
        click.echo("\n📦 Demo Timeline")
        click.echo("Start server with --demo flag to load sample timeline")


def get_local_ip() -> str:
    """Get local IP address for mobile access."""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"


def create_sample_timeline(media_dir: Optional[Path] = None) -> Optional[Timeline]:
    """Create a sample timeline for testing."""
    if not media_dir:
        media_dir = Path.home() / "Pictures" / "AI"
    
    if not media_dir.exists():
        return None
    
    # Find some images
    images = list(media_dir.glob("**/*.jpg"))[:10]
    images.extend(list(media_dir.glob("**/*.png"))[:10])
    
    if not images:
        return None
    
    # Create timeline
    timeline = Timeline(name="Sample Timeline")
    
    for i, img_path in enumerate(images[:5]):
        clip = TimelineClip(
            id=f"clip_{i}",
            file_path=img_path,
            duration=3.0  # 3 seconds per clip
        )
        timeline.add_clip(clip)
    
    return timeline


if __name__ == "__main__":
    mobile()