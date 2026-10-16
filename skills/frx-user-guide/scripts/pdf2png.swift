// swift pdf2png.swift <in.pdf> <out_dir> [scale]  -> out_dir/p01.png, p02.png ...  (macOS PDFKit, no deps)
import PDFKit
import AppKit
let args = CommandLine.arguments
guard args.count >= 3, let doc = PDFDocument(url: URL(fileURLWithPath: args[1])) else {
  print("usage: swift pdf2png.swift in.pdf out_dir [scale]"); exit(1)
}
let scale: CGFloat = args.count > 3 ? CGFloat(Double(args[3]) ?? 1.6) : 1.6
print("pages", doc.pageCount)
for i in 0..<doc.pageCount {
  let page = doc.page(at: i)!
  let r = page.bounds(for: .mediaBox)
  let img = NSImage(size: NSSize(width: r.width * scale, height: r.height * scale))
  img.lockFocus()
  NSColor.white.set(); NSRect(x: 0, y: 0, width: r.width * scale, height: r.height * scale).fill()
  let ctx = NSGraphicsContext.current!.cgContext
  ctx.scaleBy(x: scale, y: scale)
  page.draw(with: .mediaBox, to: ctx)
  img.unlockFocus()
  let rep = NSBitmapImageRep(data: img.tiffRepresentation!)!
  try! rep.representation(using: .png, properties: [:])!
    .write(to: URL(fileURLWithPath: String(format: "%@/p%02d.png", args[2], i + 1)))
}
