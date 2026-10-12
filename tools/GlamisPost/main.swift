// Glamis Post: one window to prepare a posting day and publish it.
// Build with tools/build-app.sh (puts "Glamis Post.app" on the Desktop).

import AppKit
import SwiftUI
import UniformTypeIdentifiers

// MARK: - Schedule (keep in sync with CLAUDE.md and tools/nudge.py)

let feedWeekdays: Set<Int> = [3, 5, 7]  // Calendar weekday: Sun=1 … Sat=7 → Tue, Thu, Sat
let ramps: [(String, String, String)] = [
    ("Halloween", "2026-10-24", "2026-11-01"),
    ("Thanksgiving", "2026-11-19", "2026-11-29"),
    ("New Year's", "2026-12-26", "2027-01-03"),
    ("Presidents' Day", "2027-02-06", "2027-02-15"),
]
let maxVideoBytes: Int64 = 95_000_000

let dayFormatter: DateFormatter = {
    let f = DateFormatter()
    f.calendar = Calendar(identifier: .gregorian)
    f.locale = Locale(identifier: "en_US_POSIX")
    f.timeZone = .current
    f.dateFormat = "yyyy-MM-dd"
    return f
}()

func dayString(_ d: Date) -> String { dayFormatter.string(from: d) }

func rampName(_ d: Date) -> String? {
    let s = dayString(d)
    return ramps.first { s >= $0.1 && s <= $0.2 }?.0
}

func postsDescription(_ d: Date) -> String {
    let wd = Calendar.current.component(.weekday, from: d)
    var parts = ["Video Story", "Download Story", "Reel"]
    if feedWeekdays.contains(wd) || rampName(d) != nil { parts.append("Feed post") }
    var text = parts.joined(separator: " · ")
    if let r = rampName(d) { text += "  (\(r) ramp-up)" }
    return text
}

var repoURL: URL {
    let path = Bundle.main.object(forInfoDictionaryKey: "GlamisRepoPath") as? String
        ?? (NSHomeDirectory() + "/Developer/Glamis_social")
    return URL(fileURLWithPath: path)
}

// MARK: - Git

@discardableResult
func git(_ args: [String]) -> (ok: Bool, output: String) {
    let p = Process()
    p.executableURL = URL(fileURLWithPath: "/usr/bin/git")
    p.arguments = ["-C", repoURL.path] + args
    let pipe = Pipe()
    p.standardOutput = pipe
    p.standardError = pipe
    do { try p.run() } catch { return (false, error.localizedDescription) }
    let data = pipe.fileHandleForReading.readDataToEndOfFile()
    p.waitUntilExit()
    return (p.terminationStatus == 0, String(data: data, encoding: .utf8) ?? "")
}

// MARK: - File drop zone

struct DropZone: View {
    let title: String
    let symbol: String
    let types: [UTType]
    let isImage: Bool
    @Binding var url: URL?

    var body: some View {
        VStack(spacing: 8) {
            if let url {
                if isImage, let img = NSImage(contentsOf: url) {
                    Image(nsImage: img).resizable().scaledToFit().frame(maxHeight: 150)
                } else {
                    Image(systemName: "film").font(.system(size: 40)).foregroundColor(.secondary)
                }
                Text(url.lastPathComponent).font(.caption).lineLimit(1).truncationMode(.middle)
            } else {
                Image(systemName: symbol).font(.system(size: 34)).foregroundColor(.secondary)
                Text(title).font(.headline)
                Text("Drop here or click").font(.caption).foregroundColor(.secondary)
            }
        }
        .padding(12)
        .frame(maxWidth: .infinity, minHeight: 190)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(style: StrokeStyle(lineWidth: 2, dash: [6]))
                .foregroundColor(Color.secondary.opacity(0.5))
        )
        .contentShape(Rectangle())
        .onTapGesture { choose() }
        .onDrop(of: [UTType.fileURL], isTargeted: nil) { providers in
            guard let provider = providers.first else { return false }
            provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, _ in
                var dropped: URL?
                if let data = item as? Data { dropped = URL(dataRepresentation: data, relativeTo: nil) }
                else if let u = item as? URL { dropped = u }
                if let dropped { DispatchQueue.main.async { self.url = dropped } }
            }
            return true
        }
    }

    func choose() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = types
        panel.allowsMultipleSelection = false
        if panel.runModal() == .OK { url = panel.url }
    }
}

// MARK: - Main window

final class PostModel: ObservableObject {
    @Published var date = Calendar.current.date(byAdding: .day, value: 1, to: Date()) ?? Date()
    @Published var video: URL?
    @Published var screenshot: URL?
    @Published var feature = ""
    @Published var whatItDoes = ""
    @Published var keyFacts = ""
    @Published var busy = false
    @Published var message = ""
    @Published var success = false

    var canPublish: Bool {
        video != nil && screenshot != nil
            && !feature.trimmingCharacters(in: .whitespaces).isEmpty
            && !whatItDoes.trimmingCharacters(in: .whitespaces).isEmpty
            && !busy
    }

    var existingNote: String? {
        let f = repoURL.appendingPathComponent(dayString(date)).appendingPathComponent("directions.md")
        guard let text = try? String(contentsOf: f, encoding: .utf8) else { return nil }
        return text.contains("status: ready") ? "This day is already published. Mark Ready replaces it." : nil
    }

    func oneLine(_ s: String) -> String {
        s.replacingOccurrences(of: "\n", with: " ").trimmingCharacters(in: .whitespaces)
    }

    func publish() {
        guard let video = video, let screenshot = screenshot else { return }
        let day = dayString(date)
        let featureText = oneLine(feature)
        let what = oneLine(whatItDoes)
        let facts = oneLine(keyFacts)
        busy = true
        success = false
        message = "Saving…"
        DispatchQueue.global(qos: .userInitiated).async {
            let result = ContentView.writeAndPush(day: day, video: video, screenshot: screenshot,
                                                  feature: featureText, what: what, facts: facts)
            DispatchQueue.main.async {
                self.busy = false
                self.success = result.ok
                self.message = result.message
            }
        }
    }
}

struct ContentView: View {
    @StateObject private var m = PostModel()

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack(alignment: .firstTextBaseline) {
                Text("Glamis Post").font(.largeTitle.bold())
                Spacer()
                DatePicker("", selection: $m.date, displayedComponents: .date)
                    .labelsHidden().datePickerStyle(.field)
            }
            VStack(alignment: .leading, spacing: 4) {
                Text(postsDescription(m.date)).font(.subheadline).foregroundColor(.secondary)
                if let note = m.existingNote {
                    Text(note).font(.caption).foregroundColor(.orange)
                }
            }

            HStack(spacing: 14) {
                DropZone(title: "Video", symbol: "video",
                         types: [.movie, .quickTimeMovie, .mpeg4Movie], isImage: false, url: $m.video)
                DropZone(title: "Screenshot", symbol: "photo",
                         types: [.image], isImage: true, url: $m.screenshot)
            }

            VStack(alignment: .leading, spacing: 10) {
                field("Feature", "Search and Nearby Places", $m.feature)
                field("What it does", "One sentence", $m.whatItDoes)
                field("Key facts (optional)", "Real facts only. Used word for word.", $m.keyFacts)
            }

            HStack {
                if m.busy { ProgressView().controlSize(.small) }
                Text(m.message)
                    .font(.callout)
                    .foregroundColor(m.success ? .green : .secondary)
                    .fixedSize(horizontal: false, vertical: true)
                Spacer()
                if m.success {
                    Button("Done") { NSApp.terminate(nil) }
                        .keyboardShortcut(.defaultAction)
                } else {
                    Button("Mark Ready") { m.publish() }
                        .keyboardShortcut(.defaultAction)
                        .disabled(!m.canPublish)
                }
            }
        }
        .padding(24)
        .frame(width: 600)
    }

    func field(_ label: String, _ prompt: String, _ text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label).font(.caption.weight(.semibold)).foregroundColor(.secondary)
            TextField(prompt, text: text).textFieldStyle(.roundedBorder)
        }
    }

    static func writeAndPush(day: String, video: URL, screenshot: URL,
                             feature: String, what: String, facts: String) -> (ok: Bool, message: String) {
        let fm = FileManager.default
        let folder = repoURL.appendingPathComponent(day)
        do {
            let size = (try fm.attributesOfItem(atPath: video.path)[.size] as? NSNumber)?.int64Value ?? 0
            if size > maxVideoBytes {
                return (false, "Video is \(size / 1_000_000) MB. Export it at 1080p (under 95 MB) and try again.")
            }
            try fm.createDirectory(at: folder, withIntermediateDirectories: true)

            // Replace any earlier video/screenshot for this day.
            for item in (try? fm.contentsOfDirectory(atPath: folder.path)) ?? []
            where item.hasPrefix("video.") || item.hasPrefix("screenshot.") {
                try? fm.removeItem(at: folder.appendingPathComponent(item))
            }

            let ext = video.pathExtension.isEmpty ? "mov" : video.pathExtension.lowercased()
            try fm.copyItem(at: video, to: folder.appendingPathComponent("video.\(ext)"))

            let shotDest = folder.appendingPathComponent("screenshot.png")
            if screenshot.pathExtension.lowercased() == "png" {
                try fm.copyItem(at: screenshot, to: shotDest)
            } else {
                guard let rep = NSImage(contentsOf: screenshot)?.representations.first as? NSBitmapImageRep
                        ?? NSImage(contentsOf: screenshot)?.tiffRepresentation.flatMap(NSBitmapImageRep.init(data:)),
                      let png = rep.representation(using: .png, properties: [:]) else {
                    return (false, "Could not read the screenshot. Use a PNG or JPG.")
                }
                try png.write(to: shotDest)
            }

            let directions = """
            status: ready

            feature: \(feature)
            what it does: \(what)
            key facts: \(facts)
            angle:
            headline:
            device:
            notes:

            # Written by the Glamis Post app. Answers go on the same line after the colon.
            # Lines starting with # are ignored.

            """
            try directions.write(to: folder.appendingPathComponent("directions.md"), atomically: true, encoding: .utf8)
        } catch {
            return (false, "Could not save files: \(error.localizedDescription)")
        }

        git(["add", day])
        let commit = git(["commit", "-q", "-m", "Ready: \(day) — \(feature)"])
        if !commit.ok && !commit.output.contains("nothing to commit") {
            return (false, "Saved, but the commit failed:\n\(commit.output.prefix(300))")
        }
        let pull = git(["pull", "-q", "--rebase", "--autostash"])
        if !pull.ok {
            return (false, "Saved, but pulling from GitHub failed:\n\(pull.output.prefix(300))")
        }
        let push = git(["push", "-q"])
        if !push.ok {
            return (false, "Saved, but pushing to GitHub failed:\n\(push.output.prefix(300))")
        }
        return (true, "Published \(day). The build runs at 7:45 PM the evening before.")
    }
}

@main
struct GlamisPostApp: App {
    var body: some Scene {
        WindowGroup("Glamis Post") {
            ContentView()
        }
        .windowResizability(.contentSize)
    }
}
