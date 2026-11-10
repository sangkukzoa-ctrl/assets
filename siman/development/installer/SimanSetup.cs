using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Forms;
using Microsoft.Win32;

namespace SimanSetup
{
    internal static class Program
    {
        public const string AppVersion = "1.5.6";
        public const string InstallerRevision = "3";
        public static readonly string Root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "2bornot", "Siman");
        public static readonly string Target = Path.Combine(Root, "app");
        public static readonly string LogPath = Path.Combine(Root, "setup.log");

        [STAThread]
        static int Main(string[] args)
        {
            if (args.Length > 0)
            {
                try
                {
                    if (args[0] == "--verify") { VerifyPayload(); return 0; }
                    if (args[0] == "--install") { InstallCore(); return 0; }
                    if (args[0] == "--show-path") { return Directory.Exists(Target) ? 0 : 3; }
                }
                catch (Exception e) { Log("CLI ERROR: " + e.ToString()); return 2; }
                return 4;
            }
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new SetupForm());
            return 0;
        }

        public static void Log(string line)
        {
            try
            {
                Directory.CreateDirectory(Root);
                File.AppendAllText(LogPath, DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + " | " + line + Environment.NewLine, Encoding.UTF8);
            }
            catch { }
        }

        static Stream OpenPayload()
        {
            Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream("siman.extension.payload");
            if (s == null) throw new IOException("설치 구성 파일을 찾지 못했습니다.");
            return s;
        }

        public static void VerifyPayload()
        {
            using (Stream s = OpenPayload())
            using (ZipArchive za = new ZipArchive(s, ZipArchiveMode.Read))
            {
                bool manifest = false;
                foreach (ZipArchiveEntry entry in za.Entries)
                {
                    if (entry.FullName == "manifest.json")
                    {
                        using (StreamReader r = new StreamReader(entry.Open(), Encoding.UTF8))
                        {
                            string text = r.ReadToEnd();
                            if (!Regex.IsMatch(text, "\\\"version\\\"\\s*:\\s*\\\"" + Regex.Escape(AppVersion) + "\\\""))
                                throw new InvalidDataException("확장프로그램 버전이 일치하지 않습니다.");
                            if (!Regex.IsMatch(text, "\\\"manifest_version\\\"\\s*:\\s*3"))
                                throw new InvalidDataException("Manifest V3 형식이 아닙니다.");
                            manifest = true;
                        }
                    }
                }
                if (!manifest) throw new InvalidDataException("manifest.json이 없습니다.");
            }
        }

        public static string InstallCore()
        {
            VerifyPayload();
            Directory.CreateDirectory(Root);
            string stage = Path.Combine(Root, ".siman-stage-" + Guid.NewGuid().ToString("N"));
            string old = Path.Combine(Root, ".siman-previous-" + Guid.NewGuid().ToString("N"));
            bool movedOld = false;
            bool movedNew = false;
            try
            {
                Directory.CreateDirectory(stage);
                using (Stream s = OpenPayload())
                using (ZipArchive za = new ZipArchive(s, ZipArchiveMode.Read))
                {
                    foreach (ZipArchiveEntry entry in za.Entries)
                    {
                        if (string.IsNullOrEmpty(entry.Name)) continue;
                        string path = Path.GetFullPath(Path.Combine(stage, entry.FullName.Replace('/', Path.DirectorySeparatorChar)));
                        string stageFull = Path.GetFullPath(stage) + Path.DirectorySeparatorChar;
                        if (!path.StartsWith(stageFull, StringComparison.OrdinalIgnoreCase))
                            throw new InvalidDataException("비정상 설치 파일 경로가 발견됐습니다.");
                        Directory.CreateDirectory(Path.GetDirectoryName(path));
                        using (Stream input = entry.Open())
                        using (FileStream output = new FileStream(path, FileMode.CreateNew, FileAccess.Write)) input.CopyTo(output);
                    }
                }
                if (!File.Exists(Path.Combine(stage, "manifest.json")) || !File.Exists(Path.Combine(stage, "search.html")) || !File.Exists(Path.Combine(stage, "store.js")))
                    throw new InvalidDataException("확장프로그램 구성 파일이 일부 누락됐습니다.");
                if (Directory.Exists(Target)) { Directory.Move(Target, old); movedOld = true; }
                Directory.Move(stage, Target); movedNew = true;
                string written = File.ReadAllText(Path.Combine(Target, "manifest.json"), Encoding.UTF8);
                if (!Regex.IsMatch(written, "\\\"version\\\"\\s*:\\s*\\\"" + Regex.Escape(AppVersion) + "\\\""))
                    throw new InvalidDataException("설치 후 버전 확인에 실패했습니다.");
                if (movedOld) try { Directory.Delete(old, true); } catch (Exception e) { Log("Old code clean-up note: " + e.Message); }
                Log("SUCCESS: Clean code installation (" + AppVersion + ") -> " + Target);
                return Target;
            }
            catch (Exception e)
            {
                Log("INSTALL FAILURE: " + e.ToString());
                if (movedOld)
                {
                    try
                    {
                        if (movedNew && Directory.Exists(Target)) Directory.Delete(Target, true);
                        if (!Directory.Exists(Target) && Directory.Exists(old)) Directory.Move(old, Target);
                        Log("Rollback completed");
                    }
                    catch (Exception rollbackError) { Log("ROLLBACK ERROR: " + rollbackError.ToString()); }
                }
                throw;
            }
            finally
            {
                try { if (Directory.Exists(stage)) Directory.Delete(stage, true); } catch { }
            }
        }

        // Opening a chrome:// page as an external process argument can be ignored by a running
        // Chrome profile. Open a real browser window and explicitly navigate its address bar,
        // but ONLY after confirming that the foreground window belongs to that browser.
        [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

        static bool IsBrowserForeground(string browser)
        {
            try
            {
                var hwnd = GetForegroundWindow();
                if (hwnd == IntPtr.Zero) return false;
                uint pid; GetWindowThreadProcessId(hwnd, out pid);
                if (pid == 0) return false;
                return String.Equals(Process.GetProcessById((int)pid).ProcessName, browser,
                    StringComparison.OrdinalIgnoreCase);
            }
            catch { return false; }
        }

        public static bool OpenBrowser(string browser, string uri)
        {
            string file = FindBrowser(browser);
            if (String.IsNullOrEmpty(file)) { Log("BROWSER: executable not found: " + browser); return false; }
            try
            {
                // Explicit window flag prevents Chrome from treating an unsupported external
                // internal URL as a generic browser startup request.
                Process.Start(new ProcessStartInfo(file, "--new-window \"" + uri + "\"") { UseShellExecute = true });
                for (int i = 0; i < 12 && !IsBrowserForeground(browser); i++) Thread.Sleep(180);
                if (!IsBrowserForeground(browser))
                {
                    // When Chrome opens in the background, move focus only to its own browser
                    // process. Never send keyboard shortcuts to a different user's app.
                    Process[] processes = Process.GetProcessesByName(browser);
                    for (int i = processes.Length - 1; i >= 0; i--)
                    {
                        if (processes[i].MainWindowHandle == IntPtr.Zero) continue;
                        SetForegroundWindow(processes[i].MainWindowHandle);
                        Thread.Sleep(160);
                        if (IsBrowserForeground(browser)) break;
                    }
                }
                if (!IsBrowserForeground(browser))
                {
                    Log("BROWSER: unable to focus " + browser + " address bar; manual navigation required");
                    // Give the user a useful fallback, not a false claim that the manager opened.
                    Clipboard.SetText(uri);
                    return false;
                }
                Clipboard.SetText(uri);
                SendKeys.SendWait("^l");
                Thread.Sleep(130);
                SendKeys.SendWait("^v");
                Thread.Sleep(130);
                SendKeys.SendWait("{ENTER}");
                Thread.Sleep(400);
                // The registration flow now needs the install folder on the clipboard again.
                Clipboard.SetText(Target);
                Log("BROWSER: address bar navigation sent to " + browser + " for extension manager");
                return true;
            }
            catch (Exception e)
            {
                Log("BROWSER ERROR: " + e.ToString());
                try { Clipboard.SetText(uri); } catch { }
                return false;
            }
        }

        static string FindBrowser(string name)
        {
            var paths = new List<string>();
            try
            {
                using (RegistryKey k = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\App Paths\" + name + ".exe"))
                    if (k != null && k.GetValue("") is string) paths.Add((string)k.GetValue(""));
                using (RegistryKey k = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\" + name + ".exe"))
                    if (k != null && k.GetValue("") is string) paths.Add((string)k.GetValue(""));
            }
            catch { }
            if (name == "chrome")
            {
                paths.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), @"Google\Chrome\Application\chrome.exe"));
                paths.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), @"Google\Chrome\Application\chrome.exe"));
                paths.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), @"Google\Chrome\Application\chrome.exe"));
            }
            else
            {
                paths.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), @"Microsoft\Edge\Application\msedge.exe"));
                paths.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), @"Microsoft\Edge\Application\msedge.exe"));
            }
            foreach (string p in paths) if (File.Exists(p)) return p;
            return null;
        }
    }

    internal class SetupForm : Form
    {
        readonly Color dark = Color.FromArgb(25, 36, 60);
        readonly Color secondary = Color.FromArgb(95, 106, 125);
        readonly Color blue = Color.FromArgb(39, 91, 207);
        readonly Color border = Color.FromArgb(218, 226, 237);
        readonly Label status;
        readonly Label pathText;
        readonly Button chromeBtn;
        readonly Button edgeBtn;
        readonly Button copyBtn;
        readonly Button explorerBtn;
        readonly Button installBtn;
        bool ready;
        int y = 0;

        public SetupForm()
        {
            Text = "심안(心眼) 설치 관리자";
            AutoScaleMode = AutoScaleMode.Dpi;
            ClientSize = new Size(760, 660);
            MinimumSize = new Size(740, 665);
            BackColor = Color.FromArgb(246, 248, 252);
            Font = new Font("Malgun Gothic", 9F);
            StartPosition = FormStartPosition.CenterScreen;
            MaximizeBox = false;

            Panel header = new Panel { BackColor = dark, Location = new Point(0, 0), Size = new Size(760, 125), Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right };
            Controls.Add(header);
            Label brand = new Label { Text = "心眼  SIMAN", ForeColor = Color.White, Font = new Font("Malgun Gothic", 22F, FontStyle.Bold), Location = new Point(26, 17), AutoSize = true };
            header.Controls.Add(brand);
            Label sub = new Label { Text = "AI 대화 통합 검색  ·  간편 설치 관리자", ForeColor = Color.FromArgb(204, 214, 232), Font = new Font("Malgun Gothic", 10F), Location = new Point(28, 67), AutoSize = true };
            header.Controls.Add(sub);
            Label version = new Label { Text = "확장프로그램 v" + Program.AppVersion + "  |  설치 관리자 R" + Program.InstallerRevision, ForeColor = Color.FromArgb(179, 192, 211), Location = new Point(28, 97), AutoSize = true };
            header.Controls.Add(version);

            Panel body = new Panel { Location = new Point(20, 140), Size = new Size(720, 510), Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom, AutoScroll = true, BackColor = Color.FromArgb(246, 248, 252) };
            Controls.Add(body);
            y = 0;

            Panel p1 = Card(body, 134);
            Title(p1, "01   기존 설치본 정리", 16);
            Desc(p1, "기존 심안을 사용했다면 먼저 심안에서 ‘전체 원문 백업 저장’을 누르세요.\n브라우저에서 확장프로그램을 삭제하면 로컬 검색 기록이 지워질 수 있습니다.", 47, 53);
            Button old = Btn(p1, "기존 확장프로그램 관리 화면", 92, 292, false);
            old.Click += delegate { ChooseAndOpenManager(); };

            Panel p2 = Card(body, 150);
            Title(p2, "02   새 버전 파일 설치", 16);
            Desc(p2, "기존 코드 파일을 재사용하지 않고 깨끗하게 교체합니다.\n설치에는 관리자 권한이나 CMD 실행이 필요하지 않습니다.", 47, 49);
            installBtn = Btn(p2, "설치 파일 준비하기", 100, 190, true);
            installBtn.Click += delegate { DoInstall(); };
            status = new Label { Text = Directory.Exists(Program.Target) ? "설치 폴더가 있습니다. 새 파일로 교체할 수 있습니다." : "설치 준비 전", ForeColor = secondary, Location = new Point(222, 109), AutoSize = false, Size = new Size(468, 28) };
            p2.Controls.Add(status);

            Panel p3 = Card(body, 173);
            Title(p3, "03   브라우저에 등록", 16);
            Desc(p3, "버튼을 누르면 등록 화면을 열고 설치 폴더 주소를 자동 복사합니다.\n개발자 모드 → 압축해제된 확장프로그램을 로드 → Ctrl+V → 폴더 선택", 45, 53);
            chromeBtn = Btn(p3, "Chrome 등록하기", 99, 164, true);
            edgeBtn = Btn(p3, "Edge 등록하기", 99, 160, false); edgeBtn.Left = 184;
            chromeBtn.Click += delegate { Register("chrome", "chrome://extensions"); };
            edgeBtn.Click += delegate { Register("msedge", "edge://extensions"); };
            copyBtn = Btn(p3, "폴더 주소 복사", 99, 150, false); copyBtn.Left = 355; copyBtn.Click += delegate { CopyPath(); };
            explorerBtn = Btn(p3, "폴더 열기", 99, 142, false); explorerBtn.Left = 515; explorerBtn.Click += delegate { OpenFolder(); };
            pathText = new Label { Text = Program.Target, ForeColor = secondary, Location = new Point(16, 146), Size = new Size(684, 22), AutoEllipsis = true, Font = new Font("Consolas", 8F) };
            p3.Controls.Add(pathText);

            Label foot = new Label { Text = "브라우저 보안 정책상 최초 등록은 사용자가 승인해야 합니다. 정식 웹스토어 게시 후에는 클릭 설치·자동 업데이트가 가능합니다.", Location = new Point(11, y + 5), AutoSize = false, Size = new Size(696, 40), ForeColor = secondary, Font = new Font("Malgun Gothic", 8.5F) };
            body.Controls.Add(foot);
            ready = Directory.Exists(Program.Target) && File.Exists(Path.Combine(Program.Target, "manifest.json"));
            UpdateButtons();
        }

        Panel Card(Panel body, int height)
        {
            Panel panel = new Panel { Location = new Point(0, y), Size = new Size(698, height), BackColor = Color.White, BorderStyle = BorderStyle.FixedSingle };
            body.Controls.Add(panel); y += height + 12; return panel;
        }
        void Title(Panel p, string s, int top)
        {
            p.Controls.Add(new Label { Text = s, AutoSize = true, Location = new Point(16, top), ForeColor = dark, Font = new Font("Malgun Gothic", 11F, FontStyle.Bold) });
        }
        void Desc(Panel p, string s, int top, int height)
        {
            p.Controls.Add(new Label { Text = s, Location = new Point(17, top), Size = new Size(661, height), ForeColor = secondary, Font = new Font("Malgun Gothic", 9F) });
        }
        Button Btn(Panel p, string title, int top, int width, bool primary)
        {
            Button b = new Button { Text = title, Location = new Point(16, top), Size = new Size(width, 33), FlatStyle = FlatStyle.Flat, BackColor = primary ? blue : Color.FromArgb(239, 243, 250), ForeColor = primary ? Color.White : dark, Cursor = Cursors.Hand, Font = new Font("Malgun Gothic", 9F, FontStyle.Bold) };
            b.FlatAppearance.BorderSize = 0; p.Controls.Add(b); return b;
        }
        void UpdateButtons()
        {
            chromeBtn.Enabled = ready; edgeBtn.Enabled = ready; copyBtn.Enabled = ready; explorerBtn.Enabled = ready;
        }
        void DoInstall()
        {
            installBtn.Enabled = false;
            Cursor = Cursors.WaitCursor;
            try
            {
                string path = Program.InstallCore(); ready = true;
                status.ForeColor = Color.FromArgb(25, 123, 74);
                status.Text = "설치 파일 준비 완료 ✓  (v" + Program.AppVersion + ")";
                pathText.Text = path;
                MessageBox.Show(this, "확장프로그램 파일 설치가 완료됐습니다.\n\n이제 아래 ‘Chrome 등록하기’ 또는 ‘Edge 등록하기’를 누르세요.", "심안 - 설치 파일 준비 완료", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception e)
            {
                status.ForeColor = Color.FromArgb(177, 53, 65);
                status.Text = "설치 파일 준비 실패";
                MessageBox.Show(this, "설치에 실패했습니다. 기존 파일 복원을 시도했습니다.\n\n" + e.Message + "\n\n진단 로그: " + Program.LogPath, "심안 - 설치 실패", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally { Cursor = Cursors.Default; installBtn.Enabled = true; UpdateButtons(); }
        }
        bool CopyPath()
        {
            try { Clipboard.SetText(Program.Target); return true; }
            catch (Exception e) { MessageBox.Show(this, "폴더 주소 복사에 실패했습니다: " + e.Message); return false; }
        }
        void OpenFolder()
        {
            try { Process.Start(new ProcessStartInfo("explorer.exe", "\"" + Program.Target + "\"") { UseShellExecute = true }); }
            catch (Exception e) { MessageBox.Show(this, e.Message); }
        }
        void ChooseAndOpenManager()
        {
            DialogResult answer = MessageBox.Show(this, "기존 확장프로그램을 삭제하기 전 반드시 심안에서 ‘전체 원문 백업 저장’을 실행하세요.\n\nChrome에서 관리 화면을 열까요? (아니오: Edge)", "기존 확장 관리", MessageBoxButtons.YesNoCancel, MessageBoxIcon.Warning);
            if (answer == DialogResult.Cancel) return;
            if (answer == DialogResult.Yes) { if (!Program.OpenBrowser("chrome", "chrome://extensions")) MessageBox.Show(this, "Chrome 확장 관리 화면으로 자동 이동하지 못했습니다. Chrome 주소창에 Ctrl+V 후 Enter를 누르세요."); }
            else if (!Program.OpenBrowser("msedge", "edge://extensions")) MessageBox.Show(this, "Edge 확장 관리 화면으로 자동 이동하지 못했습니다. Edge 주소창에 Ctrl+V 후 Enter를 누르세요.");
        }
        void Register(string browser, string address)
        {
            if (!ready) return;
            if (!CopyPath()) return;
            bool launched = Program.OpenBrowser(browser, address);
            if (!launched) { MessageBox.Show(this, "브라우저는 실행됐지만 확장프로그램 관리 페이지로 자동 이동하지 못했습니다.\n\n브라우저 주소창에 Ctrl+V → Enter를 눌러 관리 화면을 연 다음, 설치 관리자에서 ‘폴더 주소 복사’를 다시 눌러 주세요.", "심안 - 브라우저 등록", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
            MessageBox.Show(this, "1. 방금 열린 브라우저에서 '개발자 모드'를 켭니다.\n\n2. '압축해제된 확장 프로그램을 로드'를 누릅니다.\n\n3. 폴더 선택 창의 주소 입력 칸에 Ctrl+V → Enter를 누릅니다.\n\n4. '폴더 선택'을 누릅니다.\n\n설치 경로는 클립보드에 이미 복사했습니다. 드래그 앤 드롭은 필요하지 않습니다.\n\n기존 심안을 삭제했다면 심안에서 'ZIP / JSON 기록 가져오기'로 백업을 복원하세요.", "심안 - 브라우저 등록 방법", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
    }
}
