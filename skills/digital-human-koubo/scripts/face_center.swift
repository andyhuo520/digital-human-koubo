import Foundation
import Vision
import AppKit
// swift face_center.swift frame.png → 打印脸中心（1920×1080 像素坐标，原点左上）
let img = NSImage(contentsOfFile: CommandLine.arguments[1])!
let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil)!
let req = VNDetectFaceRectanglesRequest()
try! VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
if let f = req.results?.first {
  let b = f.boundingBox; let W = Double(cg.width), H = Double(cg.height)
  print(String(format: "%.0f %.0f", (b.midX) * W * 1920 / W, (1 - b.midY) * H * 1080 / H))
}
