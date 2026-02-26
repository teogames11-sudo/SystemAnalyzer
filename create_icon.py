"""Generate icon.ico — lightning bolt on dark background."""
import struct
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import (
    QPixmap, QPainter, QPolygon, QColor, QBrush,
    QPen, QLinearGradient, QRadialGradient
)
from PyQt6.QtCore import QPoint, Qt, QByteArray, QBuffer, QIODeviceBase


def draw_lightning(size: int) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # ── Background circle ──────────────────────
    bg = QRadialGradient(size / 2, size * 0.45, size * 0.52)
    bg.setColorAt(0.0, QColor("#1e1a50"))
    bg.setColorAt(0.7, QColor("#0d0a28"))
    bg.setColorAt(1.0, QColor("#070514"))
    p.setBrush(QBrush(bg))
    p.setPen(Qt.PenStyle.NoPen)
    margin = max(2, size // 64)
    p.drawEllipse(margin, margin, size - margin * 2, size - margin * 2)

    # ── Outer glow ring ────────────────────────
    glow_pen = QPen(QColor(120, 80, 255, 60))
    glow_pen.setWidth(max(1, size // 32))
    p.setPen(glow_pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(margin, margin, size - margin * 2, size - margin * 2)

    # ── Lightning bolt polygon ─────────────────
    # Reference design on 256×256 canvas:
    #   top point    (152,  14)
    #   middle-left  ( 78, 148)
    #   inner notch  (124, 132)
    #   bottom tip   ( 66, 242)
    #   outer-right  (180, 108)
    #   inner-right  (134, 124)
    s = size / 256.0
    bolt = QPolygon([
        QPoint(int(152 * s), int(14  * s)),
        QPoint(int(78  * s), int(148 * s)),
        QPoint(int(124 * s), int(132 * s)),
        QPoint(int(66  * s), int(242 * s)),
        QPoint(int(180 * s), int(108 * s)),
        QPoint(int(134 * s), int(124 * s)),
    ])

    # Gold-white gradient from top to bottom
    bolt_grad = QLinearGradient(
        int(100 * s), int(14 * s),
        int(100 * s), int(242 * s)
    )
    bolt_grad.setColorAt(0.0, QColor("#ffffff"))
    bolt_grad.setColorAt(0.25, QColor("#ffe566"))
    bolt_grad.setColorAt(0.7,  QColor("#ffaa00"))
    bolt_grad.setColorAt(1.0,  QColor("#ff6600"))

    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(bolt_grad))
    p.drawPolygon(bolt)

    # ── Glow halo around bolt ──────────────────
    glow_width = max(3, int(8 * s))
    for alpha, width in [(30, glow_width * 3), (55, glow_width * 2), (90, glow_width)]:
        glow_p = QPen(QColor(255, 200, 0, alpha))
        glow_p.setWidth(width)
        glow_p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        glow_p.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(glow_p)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPolygon(bolt)

    # ── Bright highlight on upper-left edge ───
    hi = QPolygon([
        QPoint(int(152 * s), int(14  * s)),
        QPoint(int(100 * s), int(112 * s)),
        QPoint(int(118 * s), int(105 * s)),
        QPoint(int(148 * s), int(22  * s)),
    ])
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(255, 255, 255, 80)))
    p.drawPolygon(hi)

    p.end()
    return pix


def save_ico(pix: QPixmap, path: str):
    """Wrap a QPixmap as an ICO file (PNG payload)."""
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODeviceBase.OpenModeFlag.WriteOnly)
    pix.save(buf, "PNG")
    buf.close()
    png_data = bytes(ba)

    # ICO header (6 bytes) + one directory entry (16 bytes) + PNG
    header      = struct.pack("<HHH", 0, 1, 1)           # reserved, type=1, count=1
    data_offset = 6 + 16
    entry       = struct.pack("<BBBBHHII",
                              0, 0, 0, 0,                # w, h, colorCount, reserved
                              1, 32,                     # planes, bitCount
                              len(png_data), data_offset)
    with open(path, "wb") as f:
        f.write(header + entry + png_data)
    print(f"Saved: {path}  ({len(png_data) // 1024} KB PNG payload)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pixmap = draw_lightning(256)
    save_ico(pixmap, "icon.ico")
    # Also save a preview PNG
    pixmap.save("icon_preview.png", "PNG")
    print("Done. icon.ico and icon_preview.png created.")
    sys.exit(0)
