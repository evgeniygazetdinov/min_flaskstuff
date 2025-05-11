import typer
import subprocess
from typing import Optional
from pathlib import Path
import json

app = typer.Typer()


def run_command(command: list[str]) -> tuple[str, str]:
    """Run a shell command and return stdout and stderr"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        raise typer.BadParameter(f"Command failed: {e.stderr}")


@app.command()
def generate_keys() -> dict:
    """Generate a new WireGuard private and public key pair"""
    private_key, _ = run_command(["wg", "genkey"])
    private_key = private_key.strip()

    public_key, _ = run_command(["echo", private_key, "|", "wg", "pubkey"])
    public_key = public_key.strip()

    return {"private_key": private_key, "public_key": public_key}


@app.command()
def create_interface(
    name: str,
    private_key: str,
    listen_port: int,
    address: str,
    dns: Optional[str] = None,
) -> None:
    """Create a new WireGuard interface"""
    # Create config directory if it doesn't exist
    config_dir = Path("wireguard_configs")
    config_dir.mkdir(exist_ok=True)
    
    config = [
        "[Interface]",
        f"PrivateKey = {private_key}",
        f"ListenPort = {listen_port}",
        f"Address = {address}",
    ]

    if dns:
        config.append(f"DNS = {dns}")

    config_path = config_dir / f"{name}.conf"
    config_path.write_text("\n".join(config))
    
    # Note: wg-quick up requires root privileges
    # For testing/development, we'll just create the config file
    # In production, you would need to run this with sudo
    print(f"Configuration written to {config_path}")
    print("Note: To activate the interface, run:")
    print(f"sudo wg-quick up {config_path}")


@app.command()
def add_peer(
    interface: str,
    public_key: str,
    allowed_ips: str,
    endpoint: Optional[str] = None,
    persistent_keepalive: Optional[int] = None,
) -> None:
    """Add a peer to a WireGuard interface"""
    command = ["wg", "set", interface, "peer", public_key, "allowed-ips", allowed_ips]

    if endpoint:
        command.extend(["endpoint", endpoint])

    if persistent_keepalive:
        command.extend(["persistent-keepalive", str(persistent_keepalive)])

    run_command(command)


@app.command()
def remove_peer(interface: str, public_key: str) -> None:
    """Remove a peer from a WireGuard interface"""
    run_command(["wg", "set", interface, "peer", public_key, "remove"])


@app.command()
def get_interface_info(interface: str) -> dict:
    """Get information about a WireGuard interface"""
    stdout, _ = run_command(["wg", "show", interface, "dump"])
    lines = stdout.strip().split("\n")

    if not lines:
        raise typer.BadParameter(f"Interface {interface} not found")

    interface_info = {"name": interface, "peers": []}

    for line in lines:
        parts = line.split("\t")
        if len(parts) >= 4:
            peer = {
                "public_key": parts[0],
                "preshared_key": parts[1],
                "endpoint": parts[2],
                "allowed_ips": parts[3],
                "latest_handshake": parts[4] if len(parts) > 4 else None,
                "transfer_rx": parts[5] if len(parts) > 5 else None,
                "transfer_tx": parts[6] if len(parts) > 6 else None,
                "persistent_keepalive": parts[7] if len(parts) > 7 else None,
            }
            interface_info["peers"].append(peer)

    return interface_info


@app.command()
def sync_config(config_file: Path) -> None:
    """Sync WireGuard configuration from a JSON file"""
    if not config_file.exists():
        raise typer.BadParameter(f"Config file {config_file} does not exist")

    config = json.loads(config_file.read_text())

    for interface in config.get("interfaces", []):
        name = interface["name"]
        create_interface(
            name=name,
            private_key=interface["private_key"],
            listen_port=interface["listen_port"],
            address=interface["address"],
            dns=interface.get("dns"),
        )

        for peer in interface.get("peers", []):
            add_peer(
                interface=name,
                public_key=peer["public_key"],
                allowed_ips=peer["allowed_ips"],
                endpoint=peer.get("endpoint"),
                persistent_keepalive=peer.get("persistent_keepalive"),
            )


if __name__ == "__main__":
    app()
