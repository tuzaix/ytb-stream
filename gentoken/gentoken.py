import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import sys
import os
import threading
import queue

# Ensure we can find the project root
# Only modify path if NOT frozen (not running as exe)
if not getattr(sys, 'frozen', False):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)

# # Force explicit imports for PyInstaller detection
# try:
#     import google.auth
#     import google.auth.transport.requests
#     import google.oauth2.credentials
#     import google_auth_oauthlib.flow
#     import googleapiclient.discovery
#     import googleapiclient.http
# except ImportError:
#     pass

import_error_msg = None
try:
    from youtube.client import YouTubeClient
except ImportError as e:
    import_error_msg = str(e)
    # We will handle this in the GUI if it fails at runtime
    YouTubeClient = None
except Exception as e:
    import_error_msg = f"Unexpected error during import: {e}"
    YouTubeClient = None

class GenTokenGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google OAuth Token 生成器")
        self.root.geometry("600x500")

        # Instructions
        tk.Label(root, text="使用 client_secret.json 生成 token.json", font=("Arial", 10, "bold")).pack(pady=10)

        # Auth Dir
        tk.Label(root, text="认证目录 (包含 client_secret.json):").pack(pady=(5, 5), padx=10, anchor="w")
        self.auth_dir_frame = tk.Frame(root)
        self.auth_dir_frame.pack(fill=tk.X, padx=10)
        
        self.auth_dir_var = tk.StringVar()
        self.auth_dir_entry = tk.Entry(self.auth_dir_frame, textvariable=self.auth_dir_var)
        self.auth_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Button(self.auth_dir_frame, text="浏览", command=self.browse_auth_dir).pack(side=tk.RIGHT, padx=5)

        # Proxy Settings
        tk.Label(root, text="代理设置 (可选):").pack(pady=(10, 5), padx=10, anchor="w")
        self.proxy_frame = tk.Frame(root)
        self.proxy_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(self.proxy_frame, text="IP:").pack(side=tk.LEFT)
        self.proxy_ip_var = tk.StringVar(value="127.0.0.1")
        tk.Entry(self.proxy_frame, textvariable=self.proxy_ip_var, width=15).pack(side=tk.LEFT, padx=(5, 10))
        
        tk.Label(self.proxy_frame, text="端口:").pack(side=tk.LEFT)
        self.proxy_port_var = tk.StringVar(value="7897")
        tk.Entry(self.proxy_frame, textvariable=self.proxy_port_var, width=8).pack(side=tk.LEFT, padx=5)

        # Button
        tk.Button(root, text="生成 Token", command=self.start_generation, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(pady=20)

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Output
        tk.Label(root, text="日志输出:").pack(padx=10, anchor="w")
        self.output_area = scrolledtext.ScrolledText(root, height=12)
        self.output_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Queue for thread-safe GUI updates
        self.log_queue = queue.Queue()
        self.update_output()

    def browse_auth_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.auth_dir_var.set(directory)

    def start_generation(self):
        auth_dir = self.auth_dir_var.get()
        proxy_ip = self.proxy_ip_var.get().strip()
        proxy_port = self.proxy_port_var.get().strip()
        
        proxy = None
        if proxy_ip and proxy_port:
            proxy = f"http://{proxy_ip}:{proxy_port}"
        elif proxy_ip or proxy_port:
             messagebox.showwarning("警告", "代理 IP 和端口必须同时填写，或同时留空。将忽略不完整的代理设置。")

        if not auth_dir:
            messagebox.showerror("错误", "请选择认证目录。")
            return
        
        if not os.path.exists(os.path.join(auth_dir, "client_secret.json")):
            messagebox.showerror("错误", "选定目录中未找到 client_secret.json。")
            return

        self.output_area.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.log(f"开始生成 Token...\n认证目录: {auth_dir}\n代理: {proxy if proxy else '无'}\n")
        
        # Run in thread
        threading.Thread(target=self.generate_token, args=(auth_dir, proxy), daemon=True).start()

    def generate_token(self, auth_dir, proxy):
        # Redirect stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StdoutRedirector(self.log_queue)
        sys.stderr = StdoutRedirector(self.log_queue)
        
        try:
            self.set_progress(10) # Started
            
            if YouTubeClient is None:
                raise ImportError(f"无法导入 YouTubeClient。\n详情: {import_error_msg}\n请检查构建中是否包含 'youtube' 模块。")

            token_path = os.path.join(auth_dir, "token.json")
            client_secret_path = os.path.join(auth_dir, "client_secret.json")

            self.log("正在初始化 YouTubeClient...\n")
            self.set_progress(50) # Initializing

            if os.path.exists(token_path):
                 self.log(f"注意: token.json 已存在于 {token_path}。将使用/刷新它。\n")
                 self.set_progress(100)

            # Instantiating YouTubeClient triggers the auth flow in _build_youtube_service
            # The library might print "Please visit this URL..." to stdout, which we catch in update_output
            client = YouTubeClient(
                client_secret_path,
                token_path,
                proxy=proxy
            )
            
            # If we reach here, it means credentials are valid or were generated
            self.set_progress(100) # Generated
            self.log("\n成功: Token 生成/验证成功!\n")
            self.log(f"Token 保存至: {token_path}\n")
            
            # Verify by making a simple call?
            # try:
            #     self.log("正在使用测试 API 调用验证 Token...\n")
            #     self.set_progress(90) # Verifying
            #     request = client.youtube.channels().list(part="id,snippet", mine=True)
            #     response = request.execute()
            #     if 'items' in response:
            #         title = response['items'][0]['snippet']['title']
            #         self.log(f"验证成功! 找到频道: {title}\n")
            #     else:
            #         self.log("验证警告: 未找到频道, 但 Token 似乎有效。\n")
            # except Exception as e:
            #     self.log(f"验证失败 (但 Token 可能已保存): {e}\n")

            # self.set_progress(100) # Done

        except Exception as e:
            self.log(f"\n错误: {e}\n")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.log("\n完成。\n")

    def log(self, message):
        self.log_queue.put(message)

    def set_progress(self, value):
        self.log_queue.put(("PROGRESS", value))

    def update_output(self):
        while not self.log_queue.empty():
            try:
                item = self.log_queue.get_nowait()
                if isinstance(item, tuple) and item[0] == "PROGRESS":
                    self.progress_var.set(item[1])
                else:
                    text = str(item)
                    # Check for keywords to update progress dynamically
                    if "Please visit this URL" in text:
                         self.progress_var.set(50) # Waiting for user input
                    
                    self.output_area.insert(tk.END, text)
                    self.output_area.see(tk.END)
            except queue.Empty:
                break
        self.root.after(100, self.update_output)

class StdoutRedirector:
    def __init__(self, queue):
        self.queue = queue
    def write(self, string):
        self.queue.put(string)
    def flush(self):
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = GenTokenGUI(root)
    root.mainloop()
