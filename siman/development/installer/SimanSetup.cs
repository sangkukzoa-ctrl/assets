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
using System.Web.Script.Serialization;
using System.Net;
using System.Net.Sockets;
using System.Windows.Forms;
using System.Windows.Automation;
using Microsoft.Win32;

namespace SimanSetup
{
    internal static class Program
    {
        public const string AppVersion = "1.5.8";
        public const string InstallerRevision = "5";
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
                    if (args[0] == "--update") {
                        InstallCore();
                        BrowserUpdateResult applied = ApplyBrowserUpdates();
                        return applied.Failed == 0 ? 0 : 5;
                    }
                    if (args[0] == "--apply-browser") { return ApplyBrowserUpdates().Failed == 0 ? 0 : 5; }
                    if (args[0] == "--scan-browser") { return DiscoverBrowserExtensions().Count > 0 ? 0 : 6; }
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

        // Stable installation root. Never touch Chrome/Edge profiles or extension storage.
        // All archives remain keyed to the extension ID because the unpacked path stays put.
        private const string ManagedListName = ".siman-managed-files.txt";

        private static string Child(string root, string relative)
        {
            string full = Path.GetFullPath(Path.Combine(root, relative.Replace('/', Path.DirectorySeparatorChar)));
            string prefix = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            if (!full.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("설치 경로 밖 파일 접근이 차단됐습니다.");
            return full;
        }

        private static string[] Files(string dir)
        {
            var items = new List<string>();
            foreach (string file in Directory.GetFiles(dir, "*", SearchOption.AllDirectories))
            {
                string relative = file.Substring(dir.TrimEnd(Path.DirectorySeparatorChar).Length + 1)
                    .Replace(Path.DirectorySeparatorChar, '/');
                if (!String.Equals(relative, ManagedListName, StringComparison.OrdinalIgnoreCase))
                    items.Add(relative);
            }
            items.Sort(StringComparer.Ordinal);
            return items.ToArray();
        }

        private static void CopyDirectory(string source, string destination)
        {
            Directory.CreateDirectory(destination);
            foreach (string item in Files(source))
            {
                string to = Child(destination, item);
                Directory.CreateDirectory(Path.GetDirectoryName(to));
                File.Copy(Child(source, item), to, true);
            }
            string managed = Path.Combine(source, ManagedListName);
            if (File.Exists(managed))
                File.Copy(managed, Path.Combine(destination, ManagedListName), true);
        }

        private static HashSet<string> ReadManagedFiles(string dir)
        {
            var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            string file = Path.Combine(dir, ManagedListName);
            if (!File.Exists(file)) return names; // v1.5.6 and earlier used whole-folder swaps.
            foreach (string name in File.ReadAllLines(file, Encoding.UTF8))
            {
                if (String.IsNullOrWhiteSpace(name)) continue;
                Child(dir, name); // Reject unsafe old manifests before deleting any file.
                names.Add(name.Trim().Replace('\\', '/'));
            }
            return names;
        }

        public static string InstalledVersion()
        {
            try
            {
                string manifest = Path.Combine(Target, "manifest.json");
                if (!File.Exists(manifest)) return "";
                Match match = Regex.Match(File.ReadAllText(manifest, Encoding.UTF8),
                    "\\\"version\\\"\\s*:\\s*\\\"([^\\\"]+)\\\"");
                return match.Success ? match.Groups[1].Value : "";
            }
            catch { return ""; }
        }

        public static string InstallCore()
        {
            VerifyPayload();
            Directory.CreateDirectory(Root);
            string stage = Path.Combine(Root, ".siman-stage-" + Guid.NewGuid().ToString("N"));
            string backup = Path.Combine(Root, ".siman-rollback-" + Guid.NewGuid().ToString("N"));
            bool existing = Directory.Exists(Target);
            bool backupReady = false;
            bool changed = false;
            string before = InstalledVersion();
            try
            {
                Directory.CreateDirectory(stage);
                using (Stream s = OpenPayload())
                using (ZipArchive za = new ZipArchive(s, ZipArchiveMode.Read))
                {
                    foreach (ZipArchiveEntry entry in za.Entries)
                    {
                        if (String.IsNullOrEmpty(entry.Name)) continue;
                        string path = Child(stage, entry.FullName);
                        Directory.CreateDirectory(Path.GetDirectoryName(path));
                        using (Stream input = entry.Open())
                        using (FileStream output = new FileStream(path, FileMode.CreateNew, FileAccess.Write))
                            input.CopyTo(output);
                    }
                }
                if (!File.Exists(Path.Combine(stage, "manifest.json")) ||
                    !File.Exists(Path.Combine(stage, "search.html")) ||
                    !File.Exists(Path.Combine(stage, "store.js")))
                    throw new InvalidDataException("확장프로그램 구성 파일이 일부 누락됐습니다.");

                string[] incoming = Files(stage);
                HashSet<string> incomingSet = new HashSet<string>(incoming, StringComparer.OrdinalIgnoreCase);
                if (existing)
                {
                    // Back up every existing app-directory file for an on-disk rollback.
                    // Do not delete the folder/re-register the browser extension.
                    CopyDirectory(Target, backup);
                    backupReady = true;
                    HashSet<string> managedBefore = ReadManagedFiles(Target);
                    changed = true;
                    CopyDirectory(stage, Target);
                    // Delete only files managed by a previous Siman installer.
                    // Preserve unrecognized files, personal notes, and user assets.
                    foreach (string oldFile in managedBefore)
                    {
                        if (incomingSet.Contains(oldFile)) continue;
                        string stale = Child(Target, oldFile);
                        if (File.Exists(stale)) File.Delete(stale);
                    }
                }
                else
                {
                    changed = true;
                    Directory.Move(stage, Target);
                }
                File.WriteAllLines(Path.Combine(Target, ManagedListName), incoming, Encoding.UTF8);
                string written = File.ReadAllText(Path.Combine(Target, "manifest.json"), Encoding.UTF8);
                if (!Regex.IsMatch(written, "\\\"version\\\"\\s*:\\s*\\\"" + Regex.Escape(AppVersion) + "\\\""))
                    throw new InvalidDataException("설치 후 버전 확인에 실패했습니다.");
                if (!File.Exists(Path.Combine(Target, "search.js")) ||
                    !File.Exists(Path.Combine(Target, "core.js")))
                    throw new InvalidDataException("설치 후 필수 파일 확인에 실패했습니다.");
                Log("SUCCESS: " + (existing ? "In-place update" : "New install") +
                    " (" + (String.IsNullOrEmpty(before) ? "none" : before) + " -> " + AppVersion + ")" +
                    " · browser profiles and archived data untouched · " + Target);
                return Target;
            }
            catch (Exception e)
            {
                Log("INSTALL FAILURE: " + e.ToString());
                if (changed)
                {
                    try
                    {
                        if (existing && backupReady)
                        {
                            if (Directory.Exists(Target)) Directory.Delete(Target, true);
                            Directory.Move(backup, Target);
                            backupReady = false;
                            Log("ROLLBACK: old app files restored");
                        }
                        else if (!existing && Directory.Exists(Target))
                        {
                            Directory.Delete(Target, true);
                            Log("ROLLBACK: incomplete new install removed");
                        }
                    }
                    catch (Exception rollbackError) { Log("ROLLBACK ERROR: " + rollbackError.ToString()); }
                }
                throw;
            }
            finally
            {
                try { if (Directory.Exists(stage)) Directory.Delete(stage, true); } catch { }
                if (backupReady)
                    try { if (Directory.Exists(backup)) Directory.Delete(backup, true); } catch { }
            }
        }

        internal sealed class ExtensionProfile
        {
            internal string Browser;
            internal string ProfileName;
            internal string UserDataDir;
            internal string Id;
        }

        internal sealed class BrowserUpdateResult
        {
            internal int Found;
            internal int Launched;
            internal int Confirmed;
            internal int DraftTabs;
            internal int RefreshedTabs;
            internal int Failed;
            internal string Details = "";
        }

        private static Dictionary<string, object> Obj(object value)
        {
            return value as Dictionary<string, object>;
        }

        private static object At(Dictionary<string, object> node, string key)
        {
            object found;
            return node != null && node.TryGetValue(key, out found) ? found : null;
        }

        // Chrome stores each unpacked extension's original source directory and
        // stable extension ID in its read-only Preferences snapshot. We inspect only
        // known Chrome/Edge profiles and match the EXACT Siman installation path.
        // Never edit Preferences, Secure Preferences, Extension State or the archive.
        internal static List<ExtensionProfile> DiscoverBrowserExtensions()
        {
            var found = new List<ExtensionProfile>();
            string local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string[] binaries = { "chrome", "msedge" };
            string[] dataDirs = {
                Path.Combine(local, @"Google\Chrome\User Data"),
                Path.Combine(local, @"Microsoft\Edge\User Data")
            };
            string expected = Path.GetFullPath(Target).TrimEnd(Path.DirectorySeparatorChar);
            for (int b = 0; b < binaries.Length; b++)
            {
                if (!Directory.Exists(dataDirs[b])) continue;
                string[] dirs;
                try { dirs = Directory.GetDirectories(dataDirs[b]); }
                catch { continue; }
                foreach (string dir in dirs)
                {
                    string name = Path.GetFileName(dir);
                    if (name != "Default" && !Regex.IsMatch(name, @"^Profile [0-9]+$")) continue;
                    var seenIds = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                    // Modern Chrome/Edge place unpacked extensions in Secure Preferences.
                    // Older browser builds used Preferences; inspect both files read-only.
                    foreach (string prefName in new[] { "Secure Preferences", "Preferences" })
                    {
                    string prefs = Path.Combine(dir, prefName);
                    if (!File.Exists(prefs)) continue;
                    try
                    {
                        string json = "";
                        for (int attempt = 0; attempt < 3; attempt++)
                        {
                            try { json = File.ReadAllText(prefs, Encoding.UTF8); break; }
                            catch (IOException) { Thread.Sleep(100); }
                        }
                        if (json.Length < 10 || json.Length > 64 * 1024 * 1024) continue;
                        var parser = new JavaScriptSerializer {
                            MaxJsonLength = 64 * 1024 * 1024, RecursionLimit = 220
                        };
                        var root = Obj(parser.DeserializeObject(json));
                        var extensions = Obj(At(root, "extensions"));
                        var settings = Obj(At(extensions, "settings"));
                        if (settings == null) continue;
                        foreach (var item in settings)
                        {
                            if (!Regex.IsMatch(item.Key, "^[a-p]{32}$")) continue;
                            var ext = Obj(item.Value);
                            string raw = At(ext, "path") as string;
                            if (String.IsNullOrWhiteSpace(raw)) continue;
                            string path = Path.GetFullPath(
                                Path.IsPathRooted(raw) ? raw : Path.Combine(dir, raw))
                                .TrimEnd(Path.DirectorySeparatorChar);
                            if (!String.Equals(path, expected, StringComparison.OrdinalIgnoreCase)) continue;
                            if (!seenIds.Add(item.Key)) continue;
                            found.Add(new ExtensionProfile {
                                Browser = binaries[b], ProfileName = name, UserDataDir = dataDirs[b], Id = item.Key
                            });
                            Log("BROWSER FOUND: " + binaries[b] + "/" + name +
                                " extension ID ending " + item.Key.Substring(28));
                        }
                    }
                    catch (Exception e)
                    {
                        Log("BROWSER READ NOTE: " + binaries[b] + "/" + name + "/" + prefName + " " + e.GetType().Name);
                    }
                    }
                }
            }
            return found;
        }

        private static string QueryValue(string request, string name)
        {
            Match match = Regex.Match(request, "(?:[?&])" + Regex.Escape(name) + "=([^&\\s]+)");
            return match.Success ? Uri.UnescapeDataString(match.Groups[1].Value) : "";
        }

        // A single-use 128-bit token is sent to the extension-owned page and returned
        // by the updated extension background worker to this loopback-only listener.
        // This proves the new extension context ran, not just that a browser tab opened.
        public static BrowserUpdateResult ApplyBrowserUpdates()
        {
            var result = new BrowserUpdateResult();
            List<ExtensionProfile> installed = DiscoverBrowserExtensions();
            result.Found = installed.Count;
            if (installed.Count == 0)
            {
                result.Details = "브라우저에 등록된 심안을 아직 찾지 못했습니다.";
                return result;
            }
            var pending = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            TcpListener listener = null;
            try
            {
                listener = new TcpListener(IPAddress.Loopback, 0);
                listener.Start();
                int port = ((IPEndPoint)listener.LocalEndpoint).Port;
                foreach (ExtensionProfile profile in installed)
                {
                    string exe = FindBrowser(profile.Browser);
                    if (String.IsNullOrEmpty(exe))
                    {
                        result.Failed++;
                        Log("BROWSER REFRESH: executable missing: " + profile.Browser);
                        continue;
                    }
                    string token = Guid.NewGuid().ToString("N");
                    string url = "chrome-extension://" + profile.Id +
                        "/search.html?siman_auto_apply=1&version=" + AppVersion +
                        "&port=" + port + "&token=" + token;
                    // No user interaction, forced browser restarts, debug ports, key
                    // shortcuts, profile writes or extension re-registration.
                    string args = "--user-data-dir=\"" + profile.UserDataDir +
                        "\" --profile-directory=\"" + profile.ProfileName +
                        "\" --new-window \"" + url + "\"";
                    try
                    {
                        pending[token] = profile.Browser + "/" + profile.ProfileName;
                        Log("BROWSER LAUNCH: " + profile.Browser + "/" + profile.ProfileName +
                            " exe=" + exe + " extension ending=" + profile.Id.Substring(28));
                        Process.Start(new ProcessStartInfo(exe, args) { UseShellExecute = true });
                        // Chromium can silently ignore extension:// on the command line.
                        // Address-bar delivery is a safe foreground-only fallback.
                        bool addressSent = NavigateExistingBrowser(profile.Browser, url);
                        Log("BROWSER UPDATE: direct foreground address dispatch " + (addressSent ? "sent" : "not available"));
                        result.Launched++;
                    }
                    catch (Exception e)
                    {
                        pending.Remove(token);
                        result.Failed++;
                        Log("BROWSER LAUNCH ERROR: " + profile.Browser + "/" + profile.ProfileName + " " + e.Message);
                    }
                }
                var watch = Stopwatch.StartNew();
                while (pending.Count > 0 && watch.ElapsedMilliseconds < 14000)
                {
                    if (!listener.Pending()) { Thread.Sleep(80); continue; }
                    using (TcpClient client = listener.AcceptTcpClient())
                    {
                        client.ReceiveTimeout = 1200;
                        client.SendTimeout = 1200;
                        string first = "";
                        try
                        {
                            using (StreamReader input = new StreamReader(client.GetStream(), Encoding.ASCII, false, 1024, true))
                                first = input.ReadLine() ?? "";
                            string token = QueryValue(first, "token");
                            string version = QueryValue(first, "v");
                            if (first.StartsWith("GET /complete?", StringComparison.Ordinal) &&
                                version == AppVersion && pending.ContainsKey(token))
                            {
                                result.Confirmed++;
                                int refreshed; int drafts;
                                if (Int32.TryParse(QueryValue(first, "refreshed"), out refreshed))
                                    result.RefreshedTabs += refreshed;
                                if (Int32.TryParse(QueryValue(first, "drafts"), out drafts))
                                    result.DraftTabs += drafts;
                                Log("BROWSER RELOADED: " + pending[token] +
                                    " / app " + version + " / tabs " + QueryValue(first, "refreshed") +
                                    " / preserved drafts " + QueryValue(first, "drafts"));
                                pending.Remove(token);
                            }
                            byte[] bytes = Encoding.UTF8.GetBytes("<!doctype html><meta charset=utf-8><title>Siman updated</title>OK");
                            byte[] header = Encoding.ASCII.GetBytes(
                                "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n" +
                                "Content-Length: " + bytes.Length + "\r\nConnection: close\r\n\r\n");
                            client.GetStream().Write(header, 0, header.Length);
                            client.GetStream().Write(bytes, 0, bytes.Length);
                        }
                        catch (Exception e) { Log("BROWSER ACK NOTE: " + e.GetType().Name); }
                    }
                }
            }
            catch (Exception e)
            {
                Log("BROWSER AUTO RELOAD ERROR: " + e.ToString());
                result.Failed++;
            }
            finally { if (listener != null) listener.Stop(); }
            result.Failed += pending.Count;
            result.Details = result.Confirmed + "/" + result.Found +
                "개 브라우저 프로필 새 코드 적용 확인 · AI 탭 자동 갱신 " +
                result.RefreshedTabs + "개 · 작성 중인 입력 보호 " + result.DraftTabs + "개";
            Log("BROWSER AUTO RELOAD: " + result.Details + " · failed " + result.Failed);
            return result;
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

        // External Chrome process command lines deliberately reject some chrome-extension:
        // navigations. Use the address bar of a confirmed Chrome/Edge foreground window
        // only, never inject keys into another application. This is a one-off bootstrap
        // for older Siman releases that had no built-in self-update watcher.
        private static bool NavigateExistingBrowser(string browser, string uri)
        {
            if (!Environment.UserInteractive) return false;
            try
            {
                bool ready = false;
                for (int pass = 0; pass < 16; pass++)
                {
                    if (IsBrowserForeground(browser)) { ready = true; break; }
                    foreach (Process process in Process.GetProcessesByName(browser))
                    {
                        try
                        {
                            if (process.MainWindowHandle == IntPtr.Zero) continue;
                            SetForegroundWindow(process.MainWindowHandle);
                            Thread.Sleep(110);
                            if (IsBrowserForeground(browser)) { ready = true; break; }
                        }
                        catch { }
                    }
                    if (ready) break;
                    Thread.Sleep(130);
                }
                if (!ready)
                {
                    Log("BROWSER UPDATE: foreground browser window unavailable; no keyboard injection");
                    return false;
                }
                // Prefer the actual UI Automation address-bar control over synthetic
                // Ctrl+V. This avoids relying on clipboard timing in a running browser.
                try
                {
                    AutomationElement window = AutomationElement.FromHandle(GetForegroundWindow());
                    AutomationElementCollection edits = window.FindAll(
                        TreeScope.Descendants,
                        new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Edit));
                    for (int i = 0; i < edits.Count; i++)
                    {
                        AutomationElement edit = edits[i];
                        string name = (edit.Current.Name ?? "").ToLowerInvariant();
                        if (!(name.Contains("address") || name.Contains("주소") ||
                            name.Contains("url") || name.Contains("search or enter") ||
                            name.Contains("search google or type"))) continue;
                        object raw;
                        if (!edit.TryGetCurrentPattern(ValuePattern.Pattern, out raw)) continue;
                        ValuePattern pattern = (ValuePattern)raw;
                        if (pattern.Current.IsReadOnly) continue;
                        edit.SetFocus();
                        pattern.SetValue(uri);
                        Thread.Sleep(140);
                        if (!IsBrowserForeground(browser)) return false;
                        SendKeys.SendWait("{ENTER}");
                        Log("BROWSER UPDATE: extension URL dispatched using Chrome/Edge UI Automation address bar");
                        return true;
                    }
                    Log("BROWSER UPDATE: accessibility address bar not found, using keyboard fallback");
                }
                catch (Exception e)
                {
                    Log("BROWSER UPDATE: accessibility fallback " + e.GetType().Name);
                }
                // Preserve clipboard when it contains text; avoid replacing personal data.
                string original = null;
                try { if (Clipboard.ContainsText()) original = Clipboard.GetText(); }
                catch { }
                try
                {
                    Clipboard.SetText(uri);
                    SendKeys.SendWait("^l");
                    Thread.Sleep(110);
                    if (!IsBrowserForeground(browser)) return false;
                    SendKeys.SendWait("^v");
                    Thread.Sleep(110);
                    if (!IsBrowserForeground(browser)) return false;
                    SendKeys.SendWait("{ENTER}");
                    Thread.Sleep(350);
                    Log("BROWSER UPDATE: extension address navigation sent via verified " + browser + " foreground window");
                    return true;
                }
                finally
                {
                    try
                    {
                        if (original != null) Clipboard.SetText(original);
                        else Clipboard.Clear();
                    }
                    catch { }
                }
            }
            catch (Exception e)
            {
                Log("BROWSER UPDATE: foreground navigation unavailable (" + e.GetType().Name + ")");
                return false;
            }
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
        readonly bool wasInstalledAtStart;
        int y = 0;

        public SetupForm()
        {
            wasInstalledAtStart = !String.IsNullOrEmpty(Program.InstalledVersion());
            Text = "심안(心眼) 자동 설치 · 업데이트";
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
            Title(p1, "01   기존 설치본 자동 감지", 16);
            Desc(p1, "설치 관리자를 실행하면 기존 설치 위치에 자동으로 덮어씁니다.\n브라우저 확장프로그램 삭제·재등록이나 원문 백업은 필요 없습니다.", 47, 53);
            Button old = Btn(p1, "기존 확장 관리 (필요할 때만)", 92, 292, false);
            old.Click += delegate { ChooseAndOpenManager(); };

            Panel p2 = Card(body, 150);
            Title(p2, "02   자동 설치 · 덮어쓰기", 16);
            Desc(p2, "기존 앱 폴더를 유지하면서 코드 파일만 최신 버전으로 교체합니다.\n실패하면 이전 코드로 복원하며, 브라우저에 저장된 기록은 건드리지 않습니다.", 47, 49);
            installBtn = Btn(p2, "다시 설치 / 복구", 100, 190, true);
            installBtn.Click += delegate { DoInstall(false); };
            status = new Label { Text = wasInstalledAtStart ? "기존 v" + Program.InstalledVersion() + " 감지 · 자동 업데이트 준비" : "최초 설치 자동 시작", ForeColor = secondary, Location = new Point(222, 109), AutoSize = false, Size = new Size(468, 28) };
            p2.Controls.Add(status);

            Panel p3 = Card(body, 173);
            Title(p3, "03   신규 설치일 때만 브라우저 등록", 16);
            Desc(p3, "이미 등록된 Chrome·Edge 확장프로그램은 그대로 사용하세요.\n최초 설치일 때만 개발자 모드 → 압축해제된 확장프로그램 로드.", 45, 53);
            chromeBtn = Btn(p3, "Chrome 등록하기", 99, 164, true);
            edgeBtn = Btn(p3, "Edge 등록하기", 99, 160, false); edgeBtn.Left = 184;
            chromeBtn.Click += delegate { Register("chrome", "chrome://extensions"); };
            edgeBtn.Click += delegate { Register("msedge", "edge://extensions"); };
            copyBtn = Btn(p3, "폴더 주소 복사", 99, 150, false); copyBtn.Left = 355; copyBtn.Click += delegate { CopyPath(); };
            explorerBtn = Btn(p3, "폴더 열기", 99, 142, false); explorerBtn.Left = 515; explorerBtn.Click += delegate { OpenFolder(); };
            pathText = new Label { Text = Program.Target, ForeColor = secondary, Location = new Point(16, 146), Size = new Size(684, 22), AutoEllipsis = true, Font = new Font("Consolas", 8F) };
            p3.Controls.Add(pathText);

            Label foot = new Label { Text = "파일 자동 덮어쓰기 후 기존 확장프로그램을 삭제하거나 재등록하지 마세요. 실행 중인 브라우저에는 확장 새로고침/재시작이 필요할 수 있습니다.", Location = new Point(11, y + 5), AutoSize = false, Size = new Size(696, 40), ForeColor = secondary, Font = new Font("Malgun Gothic", 8.5F) };
            body.Controls.Add(foot);
            ready = Directory.Exists(Program.Target) && File.Exists(Path.Combine(Program.Target, "manifest.json"));
            UpdateButtons();
            Shown += delegate { BeginInvoke(new Action(delegate { DoInstall(true); })); };
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
        // Double-clicking SimanSetup.exe performs the update automatically.
        // The manual button remains only for retry/repair after a failed installation.
        void DoInstall(bool automatic)
        {
            installBtn.Enabled = false;
            Cursor = Cursors.WaitCursor;
            status.Text = wasInstalledAtStart ? "기존 심안 덮어쓰는 중..." : "최초 설치 진행 중...";
            Application.DoEvents();
            try
            {
                string path = Program.InstallCore();
                ready = true;
                // Complete the upgrade in Chrome/Edge too: no manual extension reload.
                status.Text = "Chrome · Edge의 기존 심안에 새 코드 반영 중...";
                Application.DoEvents();
                Program.BrowserUpdateResult applied = Program.ApplyBrowserUpdates();
                if (applied.Found > 0)
                {
                    status.Text = applied.Failed == 0 ? "자동 업데이트 완료 ✓ · " + applied.Details :
                        "파일 설치 완료 · 브라우저 적용 일부 미확인 (" + applied.Confirmed + "/" + applied.Found + ")";
                    if (applied.Failed == 0 && automatic)
                    {
                        var completeTimer = new System.Windows.Forms.Timer();
                        completeTimer.Interval = 1800;
                        completeTimer.Tick += delegate {
                            completeTimer.Stop(); completeTimer.Dispose();
                            Close();
                        };
                        completeTimer.Start();
                    }
                }
                else status.Text = "파일 설치 완료 · 브라우저 최초 등록 안내";
                status.ForeColor = Color.FromArgb(25, 123, 74);
                if (applied.Found == 0)
                    status.Text = (wasInstalledAtStart ? "설치 파일 갱신 완료" : "최초 설치 완료") +
                        " ✓  (v" + Program.AppVersion + ")";
                pathText.Text = path;
                if (applied.Found == 0)
                {
                    MessageBox.Show(this,
                        "심안 파일 설치가 완료됐습니다.\n\n아래의 Chrome 또는 Edge 등록 버튼으로 최초 한 번만 연결하세요.\n이후 새 설치 관리자는 이 경로를 자동으로 덮어씁니다.",
                        "심안 - 최초 설치 완료", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                else if (applied.Failed > 0)
                {
                    MessageBox.Show(this,
                        "심안 코드 파일은 업데이트됐지만 일부 브라우저에서 새 코드 적용 확인을 받지 못했습니다.\n\n" +
                        applied.Details + "\n기존 확장프로그램은 삭제하지 않았습니다.\n\n진단 로그: " + Program.LogPath,
                        "심안 - 브라우저 자동 적용 점검", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
                else if (!automatic)
                {
                    MessageBox.Show(this,
                        "자동 덮어쓰기 및 브라우저 확장 새로고침 완료.\n" + applied.Details +
                        "\n\n기존 대화 원문과 검색 색인은 유지됩니다.",
                        "심안 - 전체 업데이트 완료", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
            catch (Exception e)
            {
                status.ForeColor = Color.FromArgb(177, 53, 65);
                status.Text = "업데이트 실패 · 이전 파일 복구 시도";
                MessageBox.Show(this,
                    "자동 설치에 실패해 기존 버전 복원을 시도했습니다.\n\n" +
                    e.Message + "\n\n진단 로그: " + Program.LogPath,
                    "심안 - 설치 실패", MessageBoxButtons.OK, MessageBoxIcon.Error);
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
            DialogResult answer = MessageBox.Show(this, "기존 심안을 삭제하거나 다시 등록하지 마세요.\n버전 반영이 필요할 때 기존 심안 카드의 새로고침을 사용하세요.\n\nChrome에서 관리 화면을 열까요? (아니오: Edge)", "기존 확장 관리", MessageBoxButtons.YesNoCancel, MessageBoxIcon.Warning);
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
            MessageBox.Show(this, "1. 방금 열린 브라우저에서 '개발자 모드'를 켭니다.\n\n2. '압축해제된 확장 프로그램을 로드'를 누릅니다.\n\n3. 폴더 선택 창의 주소 입력 칸에 Ctrl+V → Enter를 누릅니다.\n\n4. '폴더 선택'을 누릅니다.\n\n설치 경로는 클립보드에 이미 복사했습니다. 드래그 앤 드롭은 필요하지 않습니다.\n\n이미 등록되어 있다면 재등록할 필요가 없습니다. 관리 화면에서 기존 심안만 새로고침하세요.", "심안 - 브라우저 등록 방법", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
    }
}
