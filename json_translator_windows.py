import json, os, re, threading, time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

TOKEN_RE = re.compile(r'(\\N\[\d+\]|\\n|\\N|\$[A-Za-z0-9_]+|%[sdif]|%\d+\$[sdif]|<[^>]+>|\{[^{}]+\})')
SEX_RE = re.compile(r'(?i)(porn|hentai|rape|molest|sexual|sexually|intercourse|penetrat|cum|semen|masturb|orgasm|genital|vagina|penis|breast|nude|nudity|erotic|incest|paedoph|pedoph|loli|lolicon|underage|child\s*sex|minor\s*sex)')

LANG = {
    "ru": {
        "title":"JSON Game Translator", "subtitle":"Перевод JSON с сохранением прогресса и автоматическим продолжением после ошибок.",
        "file":"1. Исходный JSON", "choose":"Выбрать JSON", "settings":"2. Настройки перевода",
        "key":"API key:", "model":"Модель:", "url":"API URL:", "batch":"Пакет строк:",
        "skip":"Пропускать строки, где уже есть кириллица", "translate":"▶ Перевести", "save":"💾 Сохранить",
        "stop":"Остановить после текущего пакета", "lang":"Язык интерфейса:", "ready":"Готово. Выберите JSON.",
        "loaded":"Загружено строк: {}", "opened":"Открыт файл: {}", "count":"Строковых значений: {}",
        "found":"Найден checkpoint — прогресс можно продолжить автоматически.",
        "jsonerr":"Ошибка JSON", "no_file":"Нет файла", "choose_first":"Сначала выберите JSON.",
        "no_key":"Нет API key", "enter_key":"Введите API key.", "batch_err":"Пакет",
        "batch_num":"Пакет строк должен быть числом.", "resume":"Продолжение: готово {} из {}. Осталось перевести: {}.",
        "rowerr":"Ошибка строки {}: {}. Оставлена исходная, продолжим.", "processed":"Обработано: {}/{}",
        "stopping":"Остановка после текущего пакета…", "stopped":"Остановлено. Прогресс сохранён — можно нажать «Перевести» снова.",
        "done":"Готово. Нажмите «Сохранить», чтобы выбрать итоговый файл.", "progress_saved":"Прогресс сохранён.",
        "save_err":"Ошибка сохранения", "saved":"Сохранено: {}", "final_saved":"Итоговый файл сохранён: {}",
        "done_title":"Готово", "saved_msg":"JSON сохранён.", "placeholder":"Потерян placeholder",
        "translate_prompt":"Translate the following game localization string into Russian. Preserve meaning, tone, punctuation, line breaks and placeholders exactly. Return ONLY the translation, no commentary."
    },
    "en": {
        "title":"JSON Game Translator", "subtitle":"Translate JSON with progress saving and automatic continuation after errors.",
        "file":"1. Source JSON", "choose":"Choose JSON", "settings":"2. Translation settings",
        "key":"API key:", "model":"Model:", "url":"API URL:", "batch":"Strings per batch:",
        "skip":"Skip strings that already contain Cyrillic", "translate":"▶ Translate", "save":"💾 Save",
        "stop":"Stop after current batch", "lang":"Interface language:", "ready":"Ready. Choose a JSON file.",
        "loaded":"Loaded strings: {}", "opened":"Opened file: {}", "count":"String values: {}",
        "found":"Checkpoint found — progress can be resumed automatically.",
        "jsonerr":"JSON error", "no_file":"No file", "choose_first":"Choose a JSON file first.",
        "no_key":"No API key", "enter_key":"Enter the API key.", "batch_err":"Batch",
        "batch_num":"Strings per batch must be a number.", "resume":"Resume: {} of {} complete. Remaining to translate: {}.",
        "rowerr":"Error on {}: {}. Original kept; continuing.", "processed":"Processed: {}/{}",
        "stopping":"Stopping after current batch…", "stopped":"Stopped. Progress saved — press Translate to continue.",
        "done":"Done. Press Save to choose the final file.", "progress_saved":"Progress saved.",
        "save_err":"Save error", "saved":"Saved: {}", "final_saved":"Final file saved: {}",
        "done_title":"Done", "saved_msg":"JSON saved.", "placeholder":"Placeholder lost",
        "translate_prompt":"Translate the following game localization string into Russian. Preserve meaning, tone, punctuation, line breaks and placeholders exactly. Return ONLY the translation, no commentary."
    }
}

class App:
    def __init__(self, root):
        self.root=root
        self.lang_code="ru"
        self.data=None; self.flat=[]; self.src=""; self.out=""; self.ckpt=""; self.running=False; self.stop=False
        self.settings_snapshot={}
        self._ui()
        self.apply_language()

    def tr(self, key, *args):
        s=LANG[self.lang_code][key]
        return s.format(*args) if args else s

    def _ui(self):
        self.root.geometry("900x700"); self.root.minsize(800,620)
        p=ttk.Frame(self.root,padding=14); p.pack(fill="both",expand=True)
        self.title_lbl=ttk.Label(p,font=("Segoe UI",18,"bold")); self.title_lbl.pack(anchor="w")
        self.subtitle_lbl=ttk.Label(p); self.subtitle_lbl.pack(anchor="w",pady=(2,10))

        top=ttk.Frame(p); top.pack(fill="x",pady=(0,8))
        self.lang_lbl=ttk.Label(top); self.lang_lbl.pack(side="right",padx=(8,4))
        self.lang_combo=ttk.Combobox(top,state="readonly",width=12,values=["Русский","English"])
        self.lang_combo.current(0); self.lang_combo.pack(side="right")
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_language)

        f=ttk.LabelFrame(p,padding=10); f.pack(fill="x")
        self.file_frame=f
        self.srcvar=tk.StringVar()
        ttk.Entry(f,textvariable=self.srcvar).pack(side="left",fill="x",expand=True)
        self.choose_btn=ttk.Button(f,command=self.choose_src); self.choose_btn.pack(side="left",padx=(8,0))

        f=ttk.LabelFrame(p,padding=10); f.pack(fill="x",pady=10)
        self.settings_frame=f
        self.labels={}
        self.labels["key"]=ttk.Label(f); self.labels["key"].grid(row=0,column=0,sticky="w")
        self.key=tk.StringVar(); ttk.Entry(f,textvariable=self.key,show="*",width=54).grid(row=0,column=1,sticky="ew",padx=8)
        self.labels["model"]=ttk.Label(f); self.labels["model"].grid(row=1,column=0,sticky="w",pady=(8,0))
        self.model=tk.StringVar(value="gpt-4.1-mini"); ttk.Entry(f,textvariable=self.model).grid(row=1,column=1,sticky="ew",padx=8,pady=(8,0))
        self.labels["url"]=ttk.Label(f); self.labels["url"].grid(row=2,column=0,sticky="w",pady=(8,0))
        self.url=tk.StringVar(value="https://api.openai.com/v1"); ttk.Entry(f,textvariable=self.url).grid(row=2,column=1,sticky="ew",padx=8,pady=(8,0))
        self.labels["batch"]=ttk.Label(f); self.labels["batch"].grid(row=3,column=0,sticky="w",pady=(8,0))
        self.batch=tk.StringVar(value="20"); ttk.Entry(f,textvariable=self.batch,width=10).grid(row=3,column=1,sticky="w",padx=8,pady=(8,0))
        self.skip_ru=tk.BooleanVar(value=True); self.skip_chk=ttk.Checkbutton(f,variable=self.skip_ru); self.skip_chk.grid(row=4,column=1,sticky="w",pady=(8,0))
        f.columnconfigure(1,weight=1)

        bar=ttk.Frame(p); bar.pack(fill="x",pady=8)
        self.translate_btn=ttk.Button(bar,command=self.start); self.translate_btn.pack(side="left")
        self.save_btn=ttk.Button(bar,command=self.save_as,state="disabled"); self.save_btn.pack(side="left",padx=8)
        self.stop_btn=ttk.Button(bar,command=self.request_stop,state="disabled"); self.stop_btn.pack(side="left")

        self.status=tk.StringVar(); ttk.Label(p,textvariable=self.status).pack(anchor="w")
        self.progress=ttk.Progressbar(p,mode="determinate"); self.progress.pack(fill="x",pady=(6,8))
        self.log=tk.Text(p,height=18,wrap="word"); self.log.pack(fill="both",expand=True); self.log.configure(state="disabled")

    def apply_language(self):
        self.root.title(self.tr("title"))
        self.title_lbl.configure(text=self.tr("title")); self.subtitle_lbl.configure(text=self.tr("subtitle"))
        self.file_frame.configure(text=self.tr("file")); self.choose_btn.configure(text=self.tr("choose"))
        self.settings_frame.configure(text=self.tr("settings"))
        for k in self.labels: self.labels[k].configure(text=self.tr(k))
        self.lang_lbl.configure(text=self.tr("lang"))
        self.skip_chk.configure(text=self.tr("skip"))
        self.translate_btn.configure(text=self.tr("translate")); self.save_btn.configure(text=self.tr("save"))
        self.stop_btn.configure(text=self.tr("stop"))
        if not self.running and self.data is None: self.status.set(self.tr("ready"))
        elif self.data is not None and not self.running:
            self.status.set(self.tr("loaded",len(self.flat)))

    def change_language(self, _=None):
        self.lang_code="en" if self.lang_combo.get()=="English" else "ru"
        self.apply_language()

    def logmsg(self,s):
        self.root.after(0,lambda:self._append_log(s))
    def _append_log(self,s):
        self.log.configure(state="normal"); self.log.insert("end",s+"\n"); self.log.see("end"); self.log.configure(state="disabled")

    def choose_src(self):
        path=filedialog.askopenfilename(filetypes=[("JSON files","*.json"),("All files","*.*")])
        if not path:return
        try:
            with open(path,"r",encoding="utf-8") as fh:self.data=json.load(fh)
            self.src=path; self.srcvar.set(path); self.out=""; self.ckpt=path+".ru.checkpoint.json"
            self.flat=[]; self.flatten(self.data,())
            self.status.set(self.tr("loaded",len(self.flat)))
            self.logmsg(self.tr("opened",path)); self.logmsg(self.tr("count",len(self.flat)))
            if os.path.exists(self.ckpt): self.logmsg(self.tr("found"))
        except Exception as e: messagebox.showerror(self.tr("jsonerr"),str(e))

    def flatten(self,obj,path):
        if isinstance(obj,dict):
            for k,v in obj.items(): self.flatten(v,path+(k,))
        elif isinstance(obj,list):
            for i,v in enumerate(obj): self.flatten(v,path+(i,))
        elif isinstance(obj,str): self.flat.append((path,obj))

    def setv(self,path,val):
        x=self.data
        for k in path[:-1]: x=x[k]
        x[path[-1]]=val

    def load_checkpoint(self):
        if not os.path.exists(self.ckpt): return set()
        try:
            with open(self.ckpt,"r",encoding="utf-8") as f:c=json.load(f)
            for item in c.get("translations",[]):
                try:self.setv(tuple(item["path"]),item["value"])
                except Exception:pass
            return {tuple(item["path"]) for item in c.get("translations",[])}
        except Exception as e:
            self.logmsg("Checkpoint error: "+str(e)); return set()

    def checkpoint(self,done):
        payload={"source":self.src,"model":self.model.get(),"translations":[]}
        for path,_ in self.flat:
            if path in done: payload["translations"].append({"path":list(path),"value":self.get(path)})
        tmp=self.ckpt+".tmp"
        with open(tmp,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False)
        os.replace(tmp,self.ckpt)

    def get(self,path):
        x=self.data
        for k in path:x=x[k]
        return x

    def should_skip(self,s):
        if self.settings_snapshot.get("skip_ru", self.skip_ru.get()) and re.search(r"[А-Яа-яЁё]",s): return True
        if SEX_RE.search(s): return True
        return False

    def protect(self,s):
        toks=[]
        def repl(m): toks.append(m.group(0)); return f"⟦T{len(toks)-1}⟧"
        return TOKEN_RE.sub(repl,s),toks

    def restore(self,s,toks):
        for i,t in enumerate(toks): s=s.replace(f"⟦T{i}⟧",t)
        return s

    def api(self,text):
        safe,toks=self.protect(text)
        prompt=self.tr("translate_prompt")+"\n\n"+safe
        body=json.dumps({"model":self.settings_snapshot.get("model",self.model.get().strip()),"messages":[
            {"role":"system","content":"You are a professional video-game localization translator."},
            {"role":"user","content":prompt}],"temperature":0.2},ensure_ascii=False).encode()
        req=Request(self.settings_snapshot.get("url",self.url.get()).rstrip("/")+"/chat/completions",data=body,headers={"Content-Type":"application/json","Authorization":"Bearer "+self.settings_snapshot.get("api_key",self.key.get().strip())})
        with urlopen(req,timeout=90) as r:raw=r.read()
        obj=json.loads(raw.decode("utf-8")); out=obj["choices"][0]["message"]["content"].strip()
        if any(t not in out for t in toks): raise ValueError(self.tr("placeholder"))
        return self.restore(out,toks)

    def start(self):
        if self.running:return
        if not self.src or self.data is None: messagebox.showwarning(self.tr("no_file"),self.tr("choose_first")); return
        if not self.key.get().strip(): messagebox.showwarning(self.tr("no_key"),self.tr("enter_key")); return
        try:b=max(1,int(self.batch.get()))
        except: messagebox.showwarning(self.tr("batch_err"),self.tr("batch_num")); return
        self.running=True; self.stop=False
        self.settings_snapshot={"api_key":self.key.get().strip(),"model":self.model.get().strip(),"url":self.url.get().strip(),"skip_ru":bool(self.skip_ru.get())}
        self.translate_btn.configure(state="disabled"); self.stop_btn.configure(state="normal"); self.save_btn.configure(state="disabled")
        threading.Thread(target=self.worker,args=(b,),daemon=True).start()

    def worker(self,batch):
        done=self.load_checkpoint(); todo=[]
        for p,s in self.flat:
            if p in done:continue
            if self.should_skip(s):done.add(p);continue
            todo.append((p,s))
        total=len(self.flat); start_done=len(done)
        self.root.after(0,lambda:self.progress.configure(maximum=total,value=start_done))
        self.logmsg(self.tr("resume",start_done,total,len(todo)))
        for i in range(0,len(todo),batch):
            chunk=todo[i:i+batch]
            for p,s in chunk:
                if self.stop:break
                success=False; last=""
                for attempt in range(1,5):
                    try:
                        tr=self.api(s); self.setv(p,tr); done.add(p); success=True; break
                    except (HTTPError,URLError,TimeoutError,ValueError,KeyError) as e:
                        last=str(e); time.sleep(min(2**attempt,10))
                if not success:self.logmsg(self.tr("rowerr",p,last))
                self.root.after(0,lambda d=len(done): (self.progress.configure(value=d),self.status.set(self.tr("processed",d,total))))
            self.checkpoint(done); self.autosave()
            if self.stop:break
        self.root.after(0,self.finish)

    def autosave(self):
        snap=self.src+".ru-progress.json"; tmp=snap+".tmp"
        with open(tmp,"w",encoding="utf-8") as f:json.dump(self.data,f,ensure_ascii=False,indent=2)
        os.replace(tmp,snap)

    def finish(self):
        self.running=False; self.translate_btn.configure(state="normal"); self.stop_btn.configure(state="disabled"); self.save_btn.configure(state="normal")
        self.status.set(self.tr("stopped") if self.stop else self.tr("done"))
        self.logmsg(self.tr("progress_saved"))

    def request_stop(self):
        self.stop=True; self.status.set(self.tr("stopping"))

    def save_as(self):
        if self.data is None:return
        default="Hakubox-Translate-ru-RU.json" if self.lang_code=="ru" else "Hakubox-Translate-ru-RU.json"
        path=filedialog.asksaveasfilename(defaultextension=".json",initialfile=default,filetypes=[("JSON files","*.json")])
        if not path:return
        try:
            with open(path,"w",encoding="utf-8") as f:json.dump(self.data,f,ensure_ascii=False,indent=2)
            self.out=path; self.status.set(self.tr("saved",path)); self.logmsg(self.tr("final_saved",path))
            messagebox.showinfo(self.tr("done_title"),self.tr("saved_msg"))
        except Exception as e:messagebox.showerror(self.tr("save_err"),str(e))

if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()
