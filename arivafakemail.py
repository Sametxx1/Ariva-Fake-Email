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
LANG_DIR = "lang"
console = Console(style="bold white on #1e1e2e")

accounts = {}
current_lang = {}

def load_language(lang_code):
    global current_lang
    lang_file = os.path.join(LANG_DIR, f"{lang_code}.json")
    try:
        with open(lang_file, 'r', encoding='utf-8') as f:
            current_lang = json.load(f)
        console.print(f"[green][+] {lang_code.upper()} dili yüklendi.[/green]")
    except (json.JSONDecodeError, IOError):
        console.print(f"[red][-] {lang_code.upper()} dili yüklenemedi, varsayılan dil (Türkçe) kullanılıyor.[/red]")
        current_lang = {
            "intro_title": "Ariva",
            "intro_dev": "Geliştirici: @MaskeUndLicht\nEğitim amaçlıdır, kötüye kullanımdan kullanıcı sorumludur.",
            "status_email": "📧 Aktif E-posta",
            "status_total": "📥 Toplam E-posta",
            "status_last_action": "🕒 Son İşlem",
            "status_updated": "⏰ Son Güncelleme",
            "menu_title": "🎛️ Menü",
            "menu_create": "[1] 📧 Yeni E-posta Oluştur",
            "menu_check": "[2] 📬 Gelen Kutusunu Kontrol Et",
            "menu_auto": "[3] 🔄 Otomatik Yenileme Modu",
            "menu_select": "[4] 👤 E-posta Seç",
            "menu_delete": "[5] ♻️ E-posta Sil",
            "menu_exit": "[6] 🚪 Çıkış",
            "menu_prompt": "Seçiminizi yapın",
            "creating_account": "Hesap oluşturuluyor...",
            "account_created": "Hesap oluşturuldu: {}",
            "account_failed": "Hesap oluşturulamadı: {} - {}",
            "too_many_requests": "Çok fazla istek, {} saniye bekleniyor...",
            "email_exists": "E-posta zaten kayıtlı, yeni bir adres deneniyor.",
            "max_attempts": "Maksimum deneme sayısına ulaşıldı, hesap oluşturulamadı.",
            "token_failed": "Token alınamadı: {}",
            "checking_inbox": "Gelen kutusu kontrol ediliyor...",
            "messages_failed": "Mesajlar alınamadı: {}",
            "no_messages": "Gelen kutusunda mesaj yok.",
            "reading_message": "Mesaj okunuyor...",
            "message_failed": "Mesaj okunamadı: {}",
            "messages_title": "📩 Gelen Mesajlar",
            "messages_id": "ID",
            "messages_from": "Kimden",
            "messages_subject": "Konu",
            "message_prompt": "Okumak istediğiniz mesajın ID'sini girin (iptal için boş bırakın)",
            "message_from": "Kimden",
            "message_subject": "Konu",
            "message_content": "İçerik",
            "message_details": "📜 Mesaj Detayları",
            "no_emails": "Henüz e-posta adresi oluşturulmadı!",
            "emails_title": "📧 Kayıtlı E-posta Adresleri",
            "emails_no": "No",
            "emails_address": "E-posta",
            "select_prompt": "E-posta seçin (numara girin, iptal için boş bırakın)",
            "delete_confirm": "'{}' adresini silmek istediğinize emin misiniz? (e/h)",
            "delete_success": "'{}' adresi silindi.",
            "delete_cancelled": "Silme işlemi iptal edildi.",
            "delete_failed": "E-posta silme başarısız",
            "auto_start": "Otomatik yenileme modu başlatıldı (çıkmak için Ctrl+C).",
            "auto_stop": "Otomatik yenileme modu durduruldu.",
            "auto_wait": "10 saniye sonra tekrar kontrol edilecek...",
            "no_email_selected": "Önce bir e-posta seçmelisiniz veya oluşturmalısınız!",
            "email_selected": "Aktif e-posta: {}",
            "select_cancelled": "E-posta seçimi iptal edildi",
            "exit": "Programdan çıkılıyor...",
            "emails_loaded": "Kaydedilmiş e-posta hesapları yüklendi.",
            "emails_load_failed": "E-posta hesapları yüklenemedi, dosya bozuk veya boş.",
            "emails_not_found": "Kayıtlı e-posta dosyası bulunamadı, yeni dosya oluşturulacak.",
            "emails_saved": "E-posta hesapları kaydedildi.",
            "emails_save_failed": "E-posta hesapları kaydedilemedi.",
            "lang_menu_title": "🌐 Dil Seçimi",
            "lang_menu": "[1] Türkçe\n[2] İngilizce\n[3] Almanca\n[4] Rusça",
            "lang_prompt": "Bir dil seçin"
        }

def get_text(key, *args):
    text = current_lang.get(key, key)
    return text.format(*args) if args else text

def show_language_menu():
    console.print(Panel(
        get_text("lang_menu"),
        title=get_text("lang_menu_title"),
        border_style="cyan",
        box=box.ROUNDED,
        expand=False
    ))
    choice = Prompt.ask(get_text("lang_prompt"), choices=["1", "2", "3", "4"], default="1")
    lang_map = {"1": "tr", "2": "en", "3": "de", "4": "ru"}
    load_language(lang_map[choice])

def load_accounts():
    global accounts
    if os.path.exists(EMAIL_FILE):
        try:
            with open(EMAIL_FILE, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
            console.print(f"[green][+] {get_text('emails_loaded')}[/green]")
        except (json.JSONDecodeError, IOError):
            console.print(f"[red][-] {get_text('emails_load_failed')}[/red]")
            accounts = {}
    else:
        console.print(f"[yellow][*] {get_text('emails_not_found')}[/yellow]")
        accounts = {}

def save_accounts():
    try:
        with open(EMAIL_FILE, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, indent=4, ensure_ascii=False)
        console.print(f"[green][+] {get_text('emails_saved')}[/green]")
    except IOError:
        console.print(f"[red][-] {get_text('emails_save_failed')}[/red]")

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def create_account():
    console.print(f"[yellow][*] {get_text('creating_account')}[/yellow]")
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
                save_accounts()
                console.print(f"[green][+] {get_text('account_created', email)}[/green]")
                return email
            return None
        elif res.status_code == 429:
            console.print(f"[yellow][-] {get_text('too_many_requests', 2**attempt)}[/yellow]")
            time.sleep(2**attempt)
            username = generate_random_string()
            email = f"{username}@{domain}"
        elif res.status_code == 422:
            console.print(f"[red][-] {get_text('email_exists')}[/red]")
            username = generate_random_string()
            email = f"{username}@{domain}"
        else:
            console.print(f"[red][-] {get_text('account_failed', res.status_code, res.text)}[/red]")
            return None
    console.print(f"[red][-] {get_text('max_attempts')}[/red]")
    return None

def get_token(email, password):
    res = requests.post(f"{BASE_URL}/token", json={"address": email, "password": password})
    if res.status_code == 200:
        return res.json()['token']
    else:
        console.print(f"[red][-] {get_text('token_failed', res.text)}[/red]")
        return None

def check_messages(token):
    console.print(f"[yellow][*] {get_text('checking_inbox')}[/yellow]")
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/messages", headers=headers)
    if res.status_code == 200:
        return res.json()['hydra:member']
    else:
        console.print(f"[red][-] {get_text('messages_failed', res.text)}[/red]")
        return []

def read_message(token, msg_id):
    console.print(f"[yellow][*] {get_text('reading_message')}[/yellow]")
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/messages/{msg_id}", headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        console.print(f"[red][-] {get_text('message_failed', res.text)}[/red]")
        return {}

def display_messages(messages, token):
    if not messages:
        console.print(f"[yellow][-] {get_text('no_messages')}[/yellow]")
        return

    table = Table(title=get_text('messages_title'), show_header=True, header_style="bold #ff79c6", row_styles=["#3b3b3b", "#2b2b2b"])
    table.add_column(get_text('messages_id'), style="cyan", min_width=36)
    table.add_column(get_text('messages_from'), style="green", overflow="ellipsis")
    table.add_column(get_text('messages_subject'), style="yellow", overflow="ellipsis")

    for msg in messages:
        table.add_row(msg['id'], msg.get('from', {}).get('address', 'Bilinmiyor'), msg.get('subject', 'Konu Yok'))

    console.print(table)

    msg_id = Prompt.ask(f"[bold cyan]{get_text('message_prompt')}[/bold cyan]")
    if msg_id:
        full_msg = read_message(token, msg_id)
        if full_msg:
            content = (
                f"[bold green]{get_text('message_from')}:[/bold green] {full_msg.get('from', {}).get('address', 'Bilinmiyor')}\n"
                f"[bold yellow]{get_text('message_subject')}:[/bold yellow] {full_msg.get('subject', 'Konu Yok')}\n\n"
                f"[bold white]{get_text('message_content')}:[/bold white]\n{full_msg.get('text', 'İçerik Yok')}"
            )
            console.print(Panel(content, title=get_text('message_details'), border_style="blue", box=box.ROUNDED))

def select_email():
    if not accounts:
        console.print(f"[red][-] {get_text('no_emails')}[/red]")
        return None

    table = Table(title=get_text('emails_title'), show_header=True, header_style="bold #ff79c6", row_styles=["#3b3b3b", "#2b2b2b"])
    table.add_column(get_text('emails_no'), style="cyan", width=5)
    table.add_column(get_text('emails_address'), style="green", overflow="ellipsis")

    for i, email in enumerate(accounts.keys(), 1):
        table.add_row(str(i), email)

    console.print(table)
    choice = Prompt.ask(f"[bold cyan]{get_text('select_prompt')}[/bold cyan]")
    if choice and choice.isdigit() and 1 <= int(choice) <= len(accounts):
        return list(accounts.keys())[int(choice) - 1]
    return None

def delete_email():
    email = select_email()
    if email:
        confirm = Prompt.ask(
            f"[bold red]{get_text('delete_confirm', email)}[/bold red]",
            choices=["e", "h"] if current_lang.get("lang_prompt") == "Seçiminizi yapın" else ["y", "n"],
            default="h" if current_lang.get("lang_prompt") == "Seçiminizi yapın" else "n"
        )
        if confirm == ("e" if current_lang.get("lang_prompt") == "Seçiminizi yapın" else "y"):
            del accounts[email]
            save_accounts()
            console.print(f"[green][+] {get_text('delete_success', email)}[/green]")
            return get_text('delete_success', email)
        else:
            console.print(f"[yellow][*] {get_text('delete_cancelled')}[/yellow]")
            return get_text('delete_cancelled')
    return get_text('delete_failed')

def show_intro():
    title = Text(justify="center")
    for i, char in enumerate(get_text('intro_title')):
        title.append(char, style=f"bold #{hex(0x1e90ff - i*0x111111)[2:].zfill(6)}")
        console.print(title)
        time.sleep(0.1)
    console.print(Panel(
        Text(get_text('intro_title'), style="bold cyan", justify="center") +
        Text(f"\n\n{get_text('intro_dev')}", style="italic yellow", justify="center"),
        border_style="magenta",
        box=box.ROUNDED,
        expand=False
    ))

def show_status(active_email, last_action):
    status_text = (
        f"[bold white]{get_text('status_email')}:[/bold white] {active_email or 'Yok'} | "
        f"[bold white]{get_text('status_total')}:[/bold white] {len(accounts)} | "
        f"[bold white]{get_text('status_last_action')}:[/bold white] {last_action} | "
        f"[bold white]{get_text('status_updated')}:[/bold white] {datetime.now().strftime('%H:%M:%S')}"
    )
    console.print(Panel(status_text, title="ℹ️ Durum", border_style="cyan", box=box.ROUNDED, expand=False))

def show_menu():
    console.print(Panel(
        f"{get_text('menu_create')}\n"
        f"{get_text('menu_check')}\n"
        f"{get_text('menu_auto')}\n"
        f"{get_text('menu_select')}\n"
        f"{get_text('menu_delete')}\n"
        f"{get_text('menu_exit')}",
        title=get_text('menu_title'),
        border_style="green",
        box=box.ROUNDED,
        expand=False
    ))
    return Prompt.ask(f"[bold cyan]{get_text('menu_prompt')}[/bold cyan]", choices=["1", "2", "3", "4", "5", "6"], default="2")

def auto_refresh(token):
    console.print(f"[yellow][*] {get_text('auto_start')}[/yellow]")
    try:
        while True:
            console.print(f"[yellow][*] {get_text('checking_inbox')}[/yellow]")
            messages = check_messages(token)
            
            table = Table(title=get_text('messages_title'), show_header=True, header_style="bold #ff79c6", row_styles=["#3b3b3b", "#2b2b2b"])
            table.add_column(get_text('messages_id'), style="cyan", min_width=36)
            table.add_column(get_text('messages_from'), style="green", overflow="ellipsis")
            table.add_column(get_text('messages_subject'), style="yellow", overflow="ellipsis")

            for msg in messages:
                table.add_row(msg['id'], msg.get('from', {}).get('address', 'Unknown'), msg.get('subject', 'No Subject'))

            with Live(table, console=console, refresh_per_second=4):
                time.sleep(2)
            if not messages:
                console.print(f"[yellow][-] {get_text('no_messages')}[/yellow]")
            else:
                msg_id = Prompt.ask(f"[bold cyan]{get_text('message_prompt')}[/bold cyan]")
                if msg_id:
                    console.print(f"[yellow][*] {get_text('reading_message')}[/yellow]")
                    full_msg = read_message(token, msg_id)
                    if full_msg:
                        content = (
                            f"[bold green]{get_text('message_from')}:[/bold green] {full_msg.get('from', {}).get('address', 'Unknown')}\n"
                            f"[bold yellow]{get_text('message_subject')}:[/bold yellow] {full_msg.get('subject', 'No Subject')}\n\n"
                            f"[bold white]{get_text('message_content')}:[/bold white]\n{full_msg.get('text', 'No Content')}"
                        )
                        console.print(Panel(content, title=get_text('message_details'), border_style="blue", box=box.ROUNDED))

            console.print(f"[yellow][*] {get_text('auto_wait')}[/yellow]")
            time.sleep(10)
    except KeyboardInterrupt:
        console.print(f"[bold magenta][*] {get_text('auto_stop')}[/bold magenta]")

def main():
    if not os.path.exists(LANG_DIR):
        os.makedirs(LANG_DIR)
    load_language("tr")
    show_language_menu()
    load_accounts()
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
                console.print(Panel(f"[bold green]📧 {get_text('status_email')}:[/bold green] {active_email}", border_style="cyan", box=box.ROUNDED))
                last_action = get_text('account_created', '')
            else:
                last_action = get_text('account_failed', '', '')

        elif choice == "2":
            if not active_email or active_email not in accounts:
                console.print(f"[red][-] {get_text('no_email_selected')}[/red]")
                last_action = get_text('no_email_selected')
                continue
            messages = check_messages(accounts[active_email]["token"])
            display_messages(messages, accounts[active_email]["token"])
            last_action = get_text('checking_inbox')

        elif choice == "3":
            if not active_email or active_email not in accounts:
                console.print(f"[red][-] {get_text('no_email_selected')}[/red]")
                last_action = get_text('no_email_selected')
                continue
            auto_refresh(accounts[active_email]["token"])
            last_action = get_text('auto_start')

        elif choice == "4":
            selected_email = select_email()
            if selected_email:
                active_email = selected_email
                console.print(f"[green][+] {get_text('email_selected', active_email)}[/green]")
                last_action = get_text('email_selected', active_email)
            else:
                last_action = get_text('select_cancelled')

        elif choice == "5":
            last_action = delete_email()

        elif choice == "6":
            console.print(f"[bold magenta][*] {get_text('exit')}[/bold magenta]")
            break

if __name__ == "__main__":
    main()
