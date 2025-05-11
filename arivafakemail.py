import requests
import time
import random
import string
import json
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich import box
from datetime import datetime

BASE_URL = "https://api.mail.tm"
EMAIL_FILE = "emails.json"
console = Console(style="bold white on #1e1e2e")

accounts = {}

def load_accounts():
    """Kaydedilmiş e-posta hesaplarını JSON dosyasından yükler."""
    global accounts
    if os.path.exists(EMAIL_FILE):
        try:
            with open(EMAIL_FILE, 'r') as f:
                accounts = json.load(f)
            console.print("[green][+] Kaydedilmiş e-posta hesapları yüklendi.[/green]")
        except (json.JSONDecodeError, IOError):
            console.print("[red][-] E-posta hesapları yüklenemedi, dosya bozuk veya boş.[/red]")
            accounts = {}
    else:
        console.print("[yellow][*] Kayıtlı e-posta dosyası bulunamadı, yeni dosya oluşturulacak.[/yellow]")
        accounts = {}

def save_accounts():
    """E-posta hesaplarını JSON dosyasına kaydeder."""
    try:
        with open(EMAIL_FILE, 'w') as f:
            json.dump(accounts, f, indent=4)
        console.print("[green][+] E-posta hesapları kaydedildi.[/green]")
    except IOError:
        console.print("[red][-] E-posta hesapları kaydedilemedi.[/red]")

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def create_account():
    console.print("[yellow][*] Hesap oluşturuluyor...[/yellow]")
    username = generate_random_string()
    domain_data = requests.get(f"{BASE_URL}/domains").json()
    domain = domain_data['hydra:member'][0]['domain']
    email = f"{username}@{domain}"
    password = generate_random_string(12)

    for attempt in range(3):
        res = requests.post(f"{BASE_URL}/accounts", json={"address": email, "password": password})
        if res.status_code == 201:
            token = get_token(email, password)
            if token:
                accounts[email] = {"password": password, "token": token}
                save_accounts()  # Yeni hesabı kaydet
                console.print(f"[green][+] Hesap oluşturuldu: {email}[/green]")
                return email
            return None
        elif res.status_code == 429:
            console.print(f"[yellow][-] Çok fazla istek, {2**attempt} saniye bekleniyor...[/yellow]")
            time.sleep(2**attempt)
            username = generate_random_string()
            email = f"{username}@{domain}"
        elif res.status_code == 422:
            console.print("[red][-] E-posta zaten kayıtlı, yeni bir adres deneniyor.[/red]")
            username = generate_random_string()
            email = f"{username}@{domain}"
        else:
            console.print(f"[red][-] Hesap oluşturulamadı: {res.status_code} - {res.text}[/red]")
            return None
    console.print("[red][-] Maksimum deneme sayısına ulaşıldı, hesap oluşturulamadı.[/red]")
    return None

def get_token(email, password):
    res = requests.post(f"{BASE_URL}/token", json={"address": email, "password": password})
    if res.status_code == 200:
        return res.json()['token']
    else:
        console.print(f"[red][-] Token alınamadı: {res.text}[/red]")
        return None

def check_messages(token):
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/messages", headers=headers)
    if res.status_code == 200:
        return res.json()['hydra:member']
    else:
        console.print(f"[red][-] Mesajlar alınamadı: {res.text}[/red]")
        return []

def read_message(token, msg_id):
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/messages/{msg_id}", headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        console.print(f"[red][-] Mesaj okunamadı: {res.text}[/red]")
        return {}

def display_messages(messages, token):
    if not messages:
        console.print("[yellow][-] Gelen kutusunda mesaj yok.[/yellow]")
        return

    table = Table(title="📩 Gelen Mesajlar", show_header=True, header_style="bold #ff79c6", row_styles=["#3b3b3b", "#2b2b2b"])
    table.add_column("ID", style="cyan", min_width=36)
    table.add_column("Kimden", style="green", overflow="ellipsis")
    table.add_column("Konu", style="yellow", overflow="ellipsis")

    for msg in messages:
        table.add_row(msg['id'], msg.get('from', {}).get('address', 'Bilinmiyor'), msg.get('subject', 'Konu Yok'))

    console.print(table)

    msg_id = Prompt.ask("[bold cyan]Okumak istediğiniz mesajın ID'sini girin (iptal için boş bırakın)[/bold cyan]")
    if msg_id:
        console.print("[yellow][*] Mesaj okunuyor...[/yellow]")
        full_msg = read_message(token, msg_id)
        if full_msg:
            content = (
                f"[bold green]Kimden:[/bold green] {full_msg.get('from', {}).get('address', 'Bilinmiyor')}\n"
                f"[bold yellow]Konu:[/bold yellow] {full_msg.get('subject', 'Konu Yok')}\n\n"
                f"[bold white]İçerik:[/bold white]\n{full_msg.get('text', 'İçerik Yok')}"
            )
            console.print(Panel(content, title="📜 Mesaj Detayları", border_style="blue", box=box.ROUNDED))

def select_email():
    if not accounts:
        console.print("[red][-] Henüz e-posta adresi oluşturulmadı![/red]")
        return None

    table = Table(title="📧 Kayıtlı E-posta Adresleri", show_header=True, header_style="bold #ff79c6", row_styles=["#3b3b3b", "#2b2b2b"])
    table.add_column("No", style="cyan", width=5)
    table.add_column("E-posta", style="green", overflow="ellipsis")

    for i, email in enumerate(accounts.keys(), 1):
        table.add_row(str(i), email)

    console.print(table)
    choice = Prompt.ask("[bold cyan]E-posta seçin (numara girin, iptal için boş bırakın)[/bold cyan]")
    if choice and choice.isdigit() and 1 <= int(choice) <= len(accounts):
        return list(accounts.keys())[int(choice) - 1]
    return None

def delete_email():
    email = select_email()
    if email:
        confirm = Prompt.ask(f"[bold red]'{email}' adresini silmek istediğinize emin misiniz? (e/h)[/bold red]", choices=["e", "h"], default="h")
        if confirm == "e":
            del accounts[email]
            save_accounts()  # Silinen hesabı güncelle
            console.print(f"[green][+] '{email}' adresi silindi.[/green]")
            return "E-posta silindi"
        else:
            console.print("[yellow][*] Silme işlemi iptal edildi.[/yellow]")
            return "Silme iptal edildi"
    return "E-posta silme başarısız"

def show_intro():
    title = Text(justify="center")
    for i, char in enumerate("Ariva"):
        title.append(char, style=f"bold #{hex(0x1e90ff - i*0x111111)[2:].zfill(6)}")
        console.print(title)
        time.sleep(0.1)
    console.print(Panel(
        Text("Ariva", style="bold cyan", justify="center") +
        Text("\n\nDeveloper: @MaskeUndLicht\nEğitim amaçlıdır, kötüye kullanımdan kullanıcı sorumludur.", style="italic yellow", justify="center"),
        border_style="magenta", box=box.ROUNDED, expand=False
    ))

def show_status(active_email, last_action):
    status_text = (
        f"[bold white]📧 Aktif E-posta:[/bold white] {active_email or 'Yok'} | "
        f"[bold white]📥 Toplam E-posta:[/bold white] {len(accounts)} | "
        f"[bold white]🕒 Son İşlem:[/bold white] {last_action} | "
        f"[bold white]⏰ Son Güncelleme:[/bold white] {datetime.now().strftime('%H:%M:%S')}"
    )
    console.print(Panel(status_text, title="ℹ️ Durum", border_style="cyan", box=box.ROUNDED, expand=False))

def show_menu():
    console.print(Panel(
        "[1] 📧 Yeni E-posta Oluştur\n"
        "[2] 📬 Gelen Kutusunu Kontrol Et\n"
        "[3] 🔄 Otomatik Yenileme Modu\n"
        "[4] 👤 E-posta Seç\n"
        "[5] ♻️ E-posta Sil\n"
        "[6] 🚪 Çıkış",
        title="🎛️ Menü",
        border_style="green", box=box.ROUNDED, expand=False
    ))
    return Prompt.ask("[bold cyan]Seçiminizi yapın[/bold cyan]", choices=["1", "2", "3", "4", "5", "6"], default="2")

def auto_refresh(token):
    console.print("[yellow][*] Otomatik yenileme modu başlatıldı (çıkmak için Ctrl+C).[/yellow]")
    try:
        while True:
            console.print("[yellow][*] Gelen kutusu kontrol ediliyor...[/yellow]")
            messages = check_messages(token)
            
            table = Table(title="📩 Gelen Mesajlar", show_header=True, header_style="bold #ff79c6", row_styles=["#3b3b3b", "#2b2b2b"])
            table.add_column("ID", style="cyan", min_width=36)
            table.add_column("Kimden", style="green", overflow="ellipsis")
            table.add_column("Konu", style="yellow", overflow="ellipsis")

            for msg in messages:
                table.add_row(msg['id'], msg.get('from', {}).get('address', 'Bilinmiyor'), msg.get('subject', 'Konu Yok'))

            with Live(table, console=console, refresh_per_second=4):
                time.sleep(2)
            if not messages:
                console.print("[yellow][-] Gelen kutusunda mesaj yok.[/yellow]")
            else:
                msg_id = Prompt.ask("[bold cyan]Okumak istediğiniz mesajın ID'sini girin (iptal için boş bırakın)[/bold cyan]")
                if msg_id:
                    console.print("[yellow][*] Mesaj okunuyor...[/yellow]")
                    full_msg = read_message(token, msg_id)
                    if full_msg:
                        content = (
                            f"[bold green]Kimden:[/bold green] {full_msg.get('from', {}).get('address', 'Bilinmiyor')}\n"
                            f"[bold yellow]Konu:[/bold yellow] {full_msg.get('subject', 'Konu Yok')}\n\n"
                            f"[bold white]İçerik:[/bold white]\n{full_msg.get('text', 'İçerik Yok')}"
                        )
                        console.print(Panel(content, title="📜 Mesaj Detayları", border_style="blue", box=box.ROUNDED))

            console.print("[yellow][*] 10 saniye sonra tekrar kontrol edilecek...[/yellow]")
            time.sleep(10)
    except KeyboardInterrupt:
        console.print("[bold magenta][*] Otomatik yenileme modu durduruldu.[/bold magenta]")

def main():
    load_accounts()  # Program başlangıcında hesapları yükle
    show_intro()
    active_email = None
    last_action = "Başlangıç"

    while True:
        show_status(active_email, last_action)
        choice = show_menu()

        if choice == "1":
            new_email = create_account()
            if new_email:
                active_email = new_email
                console.print(Panel(f"[bold green]📧 Geçici Mail:[/bold green] {active_email}", border_style="cyan", box=box.ROUNDED))
                last_action = "Yeni e-posta oluşturuldu"
            else:
                last_action = "E-posta oluşturma başarısız"

        elif choice == "2":
            if not active_email or active_email not in accounts:
                console.print("[red][-] Önce bir e-posta seçmelisiniz veya oluşturmalısınız![/red]")
                last_action = "E-posta kontrolü başarısız: E-posta yok"
                continue
            console.print("[yellow][*] Gelen kutusu kontrol ediliyor...[/yellow]")
            messages = check_messages(accounts[active_email]["token"])
            display_messages(messages, accounts[active_email]["token"])
            last_action = "Gelen kutusu kontrol edildi"

        elif choice == "3":
            if not active_email or active_email not in accounts:
                console.print("[red][-] Önce bir e-posta seçmelisiniz veya oluşturmalısınız![/red]")
                last_action = "Otomatik yenileme başarısız: E-posta yok"
                continue
            auto_refresh(accounts[active_email]["token"])
            last_action = "Otomatik yenileme çalıştırıldı"

        elif choice == "4":
            selected_email = select_email()
            if selected_email:
                active_email = selected_email
                console.print(f"[green][+] Aktif e-posta: {active_email}[/green]")
                last_action = f"E-posta seçildi: {active_email}"
            else:
                last_action = "E-posta seçimi iptal edildi"

        elif choice == "5":
            last_action = delete_email()

        elif choice == "6":
            console.print("[bold magenta][*] 🚪 Programdan çıkılıyor...[/bold magenta]")
            break

if __name__ == "__main__":
    main()
