import tkinter as tk
import eGela
import helper

def check_credentials():
    egela.check_credentials(username.get(), password.get())

root = tk.Tk()
root.geometry('250x150')
root.title('Test eGela')

egela = eGela.eGela(root)

login_frame = tk.Frame(root, padx=10, pady=10)
login_frame.pack(fill=tk.BOTH, expand=True)

tk.Label(login_frame, text="User name:").pack()
username = tk.Entry(login_frame, width=16)
username.pack()

tk.Label(login_frame, text="Password:").pack()
password = tk.Entry(login_frame, width=16, show="*")
password.pack()

tk.Button(login_frame, text="Login", command=check_credentials).pack(pady=8)

root.mainloop()

if egela._login:
    print("\n✅ Login correcto!")
    print(f"Cookie: {egela._cookie}")
    print(f"Curso URI: {egela._curso}")

    # PDF lista lortu
    pdfs = egela.get_pdf_refs()
    print(f"\n✅ {len(pdfs)} PDF aurkitu:")
    for pdf in pdfs:
        print(f"  - {pdf['pdf_name']}")

    # Lehenengo PDF deskargatu
    if pdfs:
        name, content = egela.get_pdf(0)
        print(f"\n✅ PDF deskargatuta: {name} ({len(content)} bytes)")
else:
    print("❌ Login incorrecta")