import os
import struct
import zlib
import json
import hashlib
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk

# ==================================================
# Configurações e Traduções
# ==================================================

CONFIG_FILE = "config.json"

translations = {
    "pt": {
         "title": "POD5 Toolkit: Terminal Reality (Por Heitor e Denis)",
         "file_label": "Arquivo POD5:",
         "extracted_folder": "Pasta Extraída:",
         "browse": "Procurar",
         "select": "Selecionar",
         "export": "Extrair",
         "import": "Importar",
         "list_files": "Listar Arquivos",
         "config": "Configurações",
         "language": "Idioma",
         "error": "Erro",
         "success": "Sucesso",
         "file_extracted_success": "Arquivos extraídos em:",
         "manifest_not_found": "Manifesto não encontrado na pasta extraída",
         "file_import_success": "Arquivo POD5 atualizado com sucesso!",
         "no_modification": "Nenhum arquivo foi modificado",
         "importing_file": "Importando arquivo...",
         "processing": "Processando...",
         "progress": "Progresso",
         "choose_language": "Escolha o idioma:",
         "apply": "Aplicar",
         "select_pod_file": "Selecione o arquivo POD5",
         "select_folder": "Selecione a pasta",
         "list_tab_title": "Listagem",
         "config_tab_title": "Configurações"
    },
    "en": {
         "title": "POD5 Toolkit: Terminal Reality (By Heitor and Denis)",
         "file_label": "POD5 File:",
         "extracted_folder": "Extracted Folder:",
         "browse": "Browse",
         "select": "Select",
         "export": "Extract",
         "import": "Import",
         "list_files": "List Files",
         "config": "Settings",
         "language": "Language",
         "error": "Error",
         "success": "Success",
         "file_extracted_success": "Files extracted to:",
         "manifest_not_found": "Manifest not found in the extracted folder",
         "file_import_success": "POD5 file updated successfully!",
         "no_modification": "No file was modified",
         "importing_file": "Importing file...",
         "processing": "Processing...",
         "progress": "Progress",
         "choose_language": "Choose language:",
         "apply": "Apply",
         "select_pod_file": "Select POD5 file",
         "select_folder": "Select folder",
         "list_tab_title": "File Listing",
         "config_tab_title": "Settings"
    },
    "es": {
         "title": "POD5 Toolkit: Terminal Reality (Por Heitor y Denis)",
         "file_label": "Archivo POD5:",
         "extracted_folder": "Carpeta Extraída:",
         "browse": "Buscar",
         "select": "Seleccionar",
         "export": "Extraer",
         "import": "Importar",
         "list_files": "Listar Archivos",
         "config": "Configuraciones",
         "language": "Idioma",
         "error": "Error",
         "success": "Éxito",
         "file_extracted_success": "Archivos extraídos en:",
         "manifest_not_found": "Manifiesto no encontrado en la carpeta extraída",
         "file_import_success": "¡Archivo POD5 actualizado con éxito!",
         "no_modification": "Ningún archivo fue modificado",
         "importing_file": "Importando archivo...",
         "processing": "Procesando...",
         "progress": "Progreso",
         "choose_language": "Elige el idioma:",
         "apply": "Aplicar",
         "select_pod_file": "Seleccione archivo POD5",
         "select_folder": "Seleccione carpeta",
         "list_tab_title": "Listado de Archivos",
         "config_tab_title": "Configuraciones"
    }
}

# Mapeamento para nomes de pastas extraídas (sem underscore no final)
extracted_mapping = {
    "pt": "_extraido",  # Alterado para remover o acento
    "en": "_extracted",
    "es": "_extraido"
}

# Dicionários para nomes completos dos idiomas
language_full_names = {
    "pt": "Português",
    "en": "Inglês",
    "es": "Espanhol"
}
full_name_to_code = {v: k for k, v in language_full_names.items()}

# Carregar e salvar configuração (idioma)
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("language", "pt")
    return "pt"

def save_config(lang):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"language": lang}, f)

current_language = load_config()

# ==================================================
# Funções de Processamento POD5
# ==================================================

def calculate_hash(data):
    return hashlib.sha256(data).hexdigest()

def extract_pod5(input_file, output_dir, lang="pt"):
    manifest = []
    with open(input_file, 'rb') as f:
        # Ler cabeçalho
        idstring = f.read(4)
        if idstring != b'POD5':
            raise ValueError("Arquivo POD5 inválido")

        f.seek(0x58)
        files = struct.unpack('<I', f.read(4))[0]
        
        f.seek(0x108)
        info_off = struct.unpack('<I', f.read(4))[0]
        f.read(4)  # ZERO
        names_size = struct.unpack('<I', f.read(4))[0]
        
        file_size = os.fstat(f.fileno()).st_size
        names_off = file_size - names_size
        entry_size = (names_off - info_off) // files

        # Ler todas as entradas
        entries = []
        f.seek(info_off)
        for _ in range(files):
            name_off = struct.unpack('<I', f.read(4))[0]
            zsize = struct.unpack('<I', f.read(4))[0]
            offset = struct.unpack('<I', f.read(4))[0]
            size = struct.unpack('<I', f.read(4))[0]
            entries.append((name_off, zsize, offset, size))
            f.seek(f.tell() + entry_size - 16)  # Pular o resto da entrada

        # Processar cada arquivo e gerar o manifesto
        for i, (name_off, zsize, offset, size) in enumerate(entries):
            f.seek(names_off + name_off)
            filename = ""
            while True:
                byte = f.read(1)
                if byte == b'\x00' or not byte:
                    break
                filename += byte.decode('ascii')
            
            # Mantém o nome original para compatibilidade com o manifesto.
            # Se necessário, outras adaptações podem ser feitas somente na interface.
            
            # Extrair dados
            f.seek(offset)
            if zsize == size:
                data = f.read(size)
            else:
                data = zlib.decompress(f.read(zsize))
            
            file_hash = calculate_hash(data)
            manifest.append({
                "index": i,
                "name": filename,
                "original_zsize": zsize,
                "original_size": size,
                "original_offset": offset,
                "hash": file_hash,
                "compressed": (zsize != size)
            })

            # Salvar arquivo extraído
            output_path = os.path.join(output_dir, filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as out_file:
                out_file.write(data)

    # Salvar manifesto
    manifest_path = os.path.join(output_dir, "_manifest.json")
    with open(manifest_path, 'w') as mf:
        json.dump(manifest, mf, indent=2)

def import_pod5(original_file, extracted_dir, manifest_path, progress_callback=None):
    # Carrega o manifesto
    with open(manifest_path, 'r') as mf:
        manifest = json.load(mf)

    # Ler todo o arquivo original
    with open(original_file, 'rb') as f:
        original_data = f.read()
    original_file_size = len(original_data)
    header = bytearray(original_data)

    # Extrair informações do header:
    info_off = struct.unpack('<I', header[0x108:0x10C])[0]
    names_size = struct.unpack('<I', header[0x110:0x114])[0]
    old_names_off = original_file_size - names_size

    files = len(manifest)
    entry_size = (old_names_off - info_off) // files

    # Parte 1: Dados originais (até o início da tabela)
    part1 = original_data[:info_off]

    # Parte 3: Tabela de entradas original
    original_table = bytearray(original_data[info_off:old_names_off])
    new_table = bytearray(original_table)

    # Determinar quais entradas foram modificadas
    modified_data = {}
    for item in manifest:
        index = item['index']
        file_path = os.path.join(extracted_dir, item['name'])
        try:
            with open(file_path, 'rb') as f:
                current_data = f.read()
        except Exception as e:
            raise Exception(f"Erro ao ler '{item['name']}': {e}")
        if calculate_hash(current_data) != item['hash']:
            modified_data[index] = current_data

    if not modified_data:
        return False

    # Parte 2: Novo bloco de dados para entradas modificadas.
    part2 = bytearray()
    new_offsets = {}
    modified_keys = sorted(modified_data.keys())
    total_modified = len(modified_keys)
    for idx, index in enumerate(modified_keys):
        new_data = modified_data[index]
        new_offset = len(part1) + len(part2)
        new_size = len(new_data)
        new_offsets[index] = (new_offset, new_size)
        part2.extend(new_data)
        if progress_callback:
            progress = (idx + 1) / total_modified * 100
            progress_callback(progress, translations[current_language]['processing'])

    # Parte 4: Seção de nomes (inalterada)
    part4 = original_data[old_names_off:]

    # Atualizar a tabela de entradas (Parte 3)
    for i in range(files):
        entry_offset_in_table = i * entry_size
        if i in new_offsets:
            new_off, new_size = new_offsets[i]
            new_table[entry_offset_in_table + 4: entry_offset_in_table + 8] = struct.pack('<I', new_size)
            new_table[entry_offset_in_table + 8: entry_offset_in_table + 12] = struct.pack('<I', new_off)
            new_table[entry_offset_in_table + 12: entry_offset_in_table + 16] = struct.pack('<I', new_size)

    new_info_off = len(part1) + len(part2)
    new_file_data = bytearray()
    new_file_data.extend(part1)
    new_file_data.extend(part2)
    new_file_data.extend(new_table)
    new_file_data.extend(part4)
    new_file_size = len(new_file_data)

    new_file_data[0x108:0x10C] = struct.pack('<I', new_info_off)

    base_name = os.path.splitext(original_file)[0]
    new_file = f"{base_name}_new.pod"
    with open(new_file, 'wb') as f:
        f.write(new_file_data)

    return True

def list_pod_files(input_file):
    """Retorna uma lista de dicionários com informações de cada entrada do arquivo POD."""
    files_list = []
    with open(input_file, 'rb') as f:
        idstring = f.read(4)
        if idstring != b'POD5':
            raise ValueError("Arquivo POD5 inválido")
        f.seek(0x58)
        files = struct.unpack('<I', f.read(4))[0]
        f.seek(0x108)
        info_off = struct.unpack('<I', f.read(4))[0]
        f.read(4)  # ZERO
        names_size = struct.unpack('<I', f.read(4))[0]
        file_size = os.fstat(f.fileno()).st_size
        names_off = file_size - names_size
        entry_size = (names_off - info_off) // files

        entries = []
        f.seek(info_off)
        for _ in range(files):
            name_off = struct.unpack('<I', f.read(4))[0]
            zsize = struct.unpack('<I', f.read(4))[0]
            offset = struct.unpack('<I', f.read(4))[0]
            size = struct.unpack('<I', f.read(4))[0]
            entries.append((name_off, zsize, offset, size))
            f.seek(f.tell() + entry_size - 16)
        for i, (name_off, zsize, offset, size) in enumerate(entries):
            f.seek(names_off + name_off)
            filename = ""
            while True:
                byte = f.read(1)
                if byte == b'\x00' or not byte:
                    break
                filename += byte.decode('ascii')
            files_list.append({
                "index": i,
                "name": filename,
                "zsize": zsize,
                "size": size,
                "offset": offset,
                "compressed": (zsize != size)
            })
    return files_list

# ==================================================
# Interface Gráfica com Notebook (Dark Mode)
# ==================================================

class POD5ExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(translations[current_language]['title'])
        self.root.configure(bg="#2e2e2e")
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TLabel", background="#2e2e2e", foreground="#ffffff")
        self.style.configure("TButton", background="#4a4a4a", foreground="#ffffff")
        self.style.configure("TEntry", fieldbackground="#4a4a4a", foreground="#ffffff")
        self.style.configure("TCombobox", fieldbackground="#4a4a4a", foreground="#ffffff")
        
        self.current_lang = current_language
        
        self.input_file = tk.StringVar()
        self.extracted_dir = tk.StringVar()
        self.list_file = tk.StringVar()
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_main = tk.Frame(self.notebook, bg="#2e2e2e")
        self.notebook.add(self.tab_main, text=translations[self.current_lang]['title'])
        
        self.tab_list = tk.Frame(self.notebook, bg="#2e2e2e")
        self.notebook.add(self.tab_list, text=translations[self.current_lang]['list_tab_title'])
        
        self.tab_config = tk.Frame(self.notebook, bg="#2e2e2e")
        self.notebook.add(self.tab_config, text=translations[self.current_lang]['config_tab_title'])
        
        self.create_main_tab()
        self.create_list_tab()
        self.create_config_tab()

    def update_texts(self):
        lang = self.current_lang
        self.root.title(translations[lang]['title'])
        self.lbl_input.config(text=translations[lang]['file_label'])
        self.lbl_extracted.config(text=translations[lang]['extracted_folder'])
        self.btn_browse.config(text=translations[lang]['browse'])
        self.btn_select.config(text=translations[lang]['select'])
        self.btn_export.config(text=translations[lang]['export'])
        self.btn_import.config(text=translations[lang]['import'])
        self.btn_list_browse.config(text=translations[lang]['browse'])
        self.btn_list.config(text=translations[lang]['list_files'])
        self.lbl_config_lang.config(text=translations[lang]['choose_language'])
        self.btn_apply.config(text=translations[lang]['apply'])
        self.notebook.tab(1, text=translations[lang]['list_tab_title'])
        self.notebook.tab(2, text=translations[lang]['config_tab_title'])

    def log_message(self, message):
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", message + "\n")
        self.txt_log.see("end")
        self.txt_log.config(state="disabled")
    
    def update_progress(self, value, message=""):
        self.progress_bar["value"] = value
        if message:
            self.log_message(message)
        self.root.update_idletasks()
    
    def create_main_tab(self):
        lang = self.current_lang
        self.lbl_input = tk.Label(self.tab_main, text=translations[lang]['file_label'], bg="#2e2e2e", fg="#ffffff")
        self.lbl_input.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.ent_input = tk.Entry(self.tab_main, textvariable=self.input_file, width=50, bg="#4a4a4a", fg="#ffffff")
        self.ent_input.grid(row=0, column=1, padx=5, pady=5)
        self.btn_browse = ttk.Button(self.tab_main, text=translations[lang]['browse'], command=self.browse_pod5)
        self.btn_browse.grid(row=0, column=2, padx=5, pady=5)
        
        self.lbl_extracted = tk.Label(self.tab_main, text=translations[lang]['extracted_folder'], bg="#2e2e2e", fg="#ffffff")
        self.lbl_extracted.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.ent_extracted = tk.Entry(self.tab_main, textvariable=self.extracted_dir, width=50, bg="#4a4a4a", fg="#ffffff")
        self.ent_extracted.grid(row=1, column=1, padx=5, pady=5)
        self.btn_select = ttk.Button(self.tab_main, text=translations[lang]['select'], command=self.browse_extracted)
        self.btn_select.grid(row=1, column=2, padx=5, pady=5)
        
        self.btn_export = ttk.Button(self.tab_main, text=translations[lang]['export'], command=self.export_files)
        self.btn_export.grid(row=2, column=0, padx=5, pady=10)
        self.btn_import = ttk.Button(self.tab_main, text=translations[lang]['import'], command=self.import_files)
        self.btn_import.grid(row=2, column=2, padx=5, pady=10)
        
        self.progress_bar = ttk.Progressbar(self.tab_main, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=3, column=0, columnspan=3, padx=5, pady=5)
        self.progress_bar["value"] = 0
        
        self.txt_log = tk.Text(self.tab_main, height=8, bg="#4a4a4a", fg="#ffffff", state="disabled")
        self.txt_log.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.tab_main.grid_rowconfigure(4, weight=1)
    
    def create_list_tab(self):
        lang = self.current_lang
        lbl = tk.Label(self.tab_list, text=translations[lang]['file_label'], bg="#2e2e2e", fg="#ffffff")
        lbl.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.ent_list = tk.Entry(self.tab_list, textvariable=self.list_file, width=50, bg="#4a4a4a", fg="#ffffff")
        self.ent_list.grid(row=0, column=1, padx=5, pady=5)
        self.btn_list_browse = ttk.Button(self.tab_list, text=translations[lang]['browse'], command=self.browse_list_file)
        self.btn_list_browse.grid(row=0, column=2, padx=5, pady=5)
        
        self.btn_list = ttk.Button(self.tab_list, text=translations[lang]['list_files'], command=self.list_files)
        self.btn_list.grid(row=1, column=1, padx=5, pady=5)
        
        self.tree = ttk.Treeview(self.tab_list, columns=("index", "name", "size", "compressed"), show="headings")
        self.tree.heading("index", text="Index")
        self.tree.heading("name", text="Name")
        self.tree.heading("size", text="Size")
        self.tree.heading("compressed", text="Compressed")
        self.tree.column("index", width=50, anchor="center")
        self.tree.column("name", width=250)
        self.tree.column("size", width=80, anchor="center")
        self.tree.column("compressed", width=80, anchor="center")
        self.tree.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(self.tab_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=2, column=3, sticky="ns")
        
        self.tab_list.grid_rowconfigure(2, weight=1)
    
    def create_config_tab(self):
        lang = self.current_lang
        self.lbl_config_lang = tk.Label(self.tab_config, text=translations[lang]['choose_language'], bg="#2e2e2e", fg="#ffffff")
        self.lbl_config_lang.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.lang_var = tk.StringVar(value=language_full_names[self.current_lang])
        self.cmb_lang = ttk.Combobox(self.tab_config, textvariable=self.lang_var, state="readonly",
                                     values=list(language_full_names.values()))
        self.cmb_lang.grid(row=0, column=1, padx=5, pady=5)
        
        self.btn_apply = ttk.Button(self.tab_config, text=translations[lang]['apply'], command=self.apply_config)
        self.btn_apply.grid(row=1, column=0, columnspan=2, padx=5, pady=10)
    
    def browse_pod5(self):
        lang = self.current_lang
        file_path = filedialog.askopenfilename(
            title=translations[lang]['select_pod_file'],
            filetypes=[("Arquivos POD5", "*.pod"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            self.input_file.set(file_path)
            base = os.path.splitext(file_path)[0]
            self.extracted_dir.set(base + extracted_mapping[self.current_lang])
    
    def browse_extracted(self):
        lang = self.current_lang
        dir_path = filedialog.askdirectory(title=translations[lang]['select_folder'])
        if dir_path:
            self.extracted_dir.set(dir_path)
    
    def browse_list_file(self):
        lang = self.current_lang
        file_path = filedialog.askopenfilename(
            title=translations[lang]['select_pod_file'],
            filetypes=[("Arquivos POD5", "*.pod"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            self.list_file.set(file_path)
    
    def export_files(self):
        lang = self.current_lang
        input_path = self.input_file.get()
        output_dir = self.extracted_dir.get()
        
        if not input_path:
            messagebox.showerror(translations[lang]['error'], translations[lang]['select_pod_file'])
            return
            
        try:
            extract_pod5(input_path, output_dir, lang)
            messagebox.showinfo(translations[lang]['success'], f"{translations[lang]['file_extracted_success']}\n{output_dir}")
            self.log_message(f"{translations[lang]['export']} concluído.")
        except Exception as e:
            messagebox.showerror(translations[lang]['error'], f"Falha na extração:\n{str(e)}")
            self.log_message(f"Erro: {str(e)}")
    
    def import_files(self):
        lang = self.current_lang
        input_path = self.input_file.get()
        extracted_path = self.extracted_dir.get()
        manifest_path = os.path.join(extracted_path, "_manifest.json")
        
        if not os.path.exists(manifest_path):
            messagebox.showerror(translations[lang]['error'], translations[lang]['manifest_not_found'])
            return
        
        self.log_message(translations[lang]['importing_file'])
        self.progress_bar["value"] = 0
        try:
            success = import_pod5(input_path, extracted_path, manifest_path, self.update_progress)
            if success:
                messagebox.showinfo(translations[lang]['success'], translations[lang]['file_import_success'])
                self.log_message(translations[lang]['file_import_success'])
            else:
                messagebox.showinfo(translations[lang]['success'], translations[lang]['no_modification'])
                self.log_message(translations[lang]['no_modification'])
        except Exception as e:
            messagebox.showerror(translations[lang]['error'], f"Falha na importação:\n{str(e)}")
            self.log_message(f"Erro: {str(e)}")
        self.progress_bar["value"] = 0
    
    def list_files(self):
        lang = self.current_lang
        file_path = self.list_file.get()
        if not file_path:
            messagebox.showerror(translations[lang]['error'], translations[lang]['select_pod_file'])
            return
        try:
            files = list_pod_files(file_path)
            for item in self.tree.get_children():
                self.tree.delete(item)
            for file_info in files:
                self.tree.insert("", "end", values=(
                    file_info["index"],
                    file_info["name"],
                    file_info["size"],
                    "Sim" if file_info["compressed"] else "Não"
                ))
            self.log_message("Listagem concluída.")
        except Exception as e:
            messagebox.showerror(translations[lang]['error'], f"Erro na listagem:\n{str(e)}")
            self.log_message(f"Erro: {str(e)}")
    
    def apply_config(self):
        selected_full = self.lang_var.get()
        self.current_lang = full_name_to_code[selected_full]
        global current_language
        current_language = self.current_lang
        save_config(self.current_lang)
        self.update_texts()
        self.log_message("Configurações atualizadas.")

if __name__ == "__main__":
    root = tk.Tk()
    app = POD5ExtractorApp(root)
    root.mainloop()
