from __future__ import annotations
import math, time
from collections import deque
from turtle import heading

# PyQt6 core + GUI classes
from PyQt6.QtCore import Qt, QPointF, QRectF, QPoint, QLine, QLineF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF, QShortcut, QKeySequence, QBrush
import math
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox


# All the widgets used are built here (except the map and synthetic vision)


def format_val(val):    # this function is to fix Nan errors related to controller input, 
                        # it was a last minute fix before the showcase, i dont know if its necessary still

    #Returns an integer string or '--' if value is NaN.
    try:
        if math.isnan(val):
            return "--"
        return str(int(val))
    except (ValueError, TypeError):
        return "--"

class AttitudeBackground(QWidget):   # AttitudeBackground, AttitudeOverlay, and Attitude indicator used to be all one widget, 
                                     # But they were separated to make the synthetic vision work (even though its a little bit useless right now)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.roll = 0.0
        self.pitch = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_state(self, roll, pitch):
        self.roll, self.pitch = roll, pitch
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        
        p.translate(cx, cy)
        p.rotate(-self.roll)
        
        pitch_px_per_deg = h / 80
        y = self.pitch * pitch_px_per_deg
        
        # Draw Sky and Ground
        p.fillRect(QRectF(-w*2, -h*2 + y, w*4, h*2), QColor(118, 161, 207)) 
        p.fillRect(QRectF(-w*2, y, w*4, h*2), QColor(153, 90, 42))
        
        # Horizon Line
        p.setPen(QPen(Qt.GlobalColor.white, 3))
        p.drawLine(QPointF(-w*2, y), QPointF(w*2, y))

class AttitudeOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.roll = 0.0
        self.pitch = 0.0
        self.u_fps = 0.0
        self.v_fps = 0.0
        self.w_fps = 0.0
        self.fd_enabled = False
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.altitude_ft = 0.0
        self.selected_altitude_ft = 1000.0
        self.heading_deg = 0.0
        self.selected_heading_deg = 90.0

    def set_state(self, roll, pitch):
        self.roll, self.pitch = roll, pitch
        self.update()
    
    def set_velocity(self, u, v, w):
        self.u_fps = float(u)
        self.v_fps = float(v)
        self.w_fps = float(w)
        self.update()

    def set_altitude(self, altitude_ft):
        self.altitude_ft = float(altitude_ft)
        self.update()

    def set_heading(self, heading_deg):
        self.heading_deg = float(heading_deg) % 360.0
        self.update()
    def set_selected_targets(self, heading_deg, altitude_ft):
        self.selected_heading_deg = float(heading_deg) % 360.0
        self.selected_altitude_ft = float(altitude_ft)
        self.update()
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        pitch_px_per_deg = h / 80.0
        radius = h / 2

        # ROTATING ELEMENTS (Pitch Ladder & Roll Triangle)
        p.save()
        p.translate(cx, cy)
        p.rotate(-self.roll)
        y_offset = self.pitch * pitch_px_per_deg
        
        # Rolling Triangle (Top of the rotating ball)
        p.setBrush(QBrush(Qt.GlobalColor.white))
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        # Positioned relative to the arc
        movingtris = (QPointF(0, -radius * 0.8), 
                      QPointF(8, -radius * 0.8 + 20), 
                      QPointF(-8, -radius * 0.8 + 20))
        p.drawPolygon(QPolygonF(movingtris))

        # Pitch Ladder
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.setFont(QFont("Consolas", 14))
        for deg in range(-20, 21, 10):  # from -20 to 20 degrees
            yy = y_offset - deg * pitch_px_per_deg
            # Main degree line
            p.drawLine(QPointF(-70, yy), QPointF(70, yy))

            # 5-degree intermediate dashes
            if deg < 20:
                p.drawLine(QPointF(-35, yy - (pitch_px_per_deg * 5)), 
                           QPointF(35, yy - (pitch_px_per_deg * 5)))
            
            # Draw numbers on right and left of all lines except horizon line
            if deg != 0:
                p.drawText(QRectF(-105, yy - 12, 30, 20), Qt.AlignmentFlag.AlignRight, f"{abs(deg)}")
                p.drawText(QRectF(75, yy - 12, 30, 20), Qt.AlignmentFlag.AlignLeft, f"{abs(deg)}")
        p.restore()

    # FIXED ELEMENTS (Roll Scale & Aircraft Symbol)  
        # Roll Indicator arc and dashes
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        for ang in range(-45, 46, 15):
            a = math.radians(ang)
            # Lines pointing inward from the edge
            x1 = cx + math.sin(a) * radius * 0.8
            y1 = cy - math.cos(a) * radius * 0.8
            x2 = cx + math.sin(a) * radius * 0.85
            y2 = cy - math.cos(a) * radius * 0.85
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Static Top Triangle (0-degree roll reference)
        p.setBrush(QBrush(Qt.GlobalColor.white))
        static_tris = (QPointF(cx, cy - radius * 0.8), 
                       QPointF(cx + 8, cy - radius * 0.8 - 20), 
                       QPointF(cx - 8, cy - radius * 0.8 - 20))
        p.drawPolygon(QPolygonF(static_tris))

        # Connecting arc for roll scale
        p.setBrush(Qt.BrushStyle.NoBrush)
        arcrect = QRectF(cx - radius*0.8, cy - radius*0.8, radius*0.8 * 2, radius*0.8 * 2)
        p.drawArc(arcrect, 45 * 16, 90 * 16)

    # Yellow shape
        yellow_pen = QPen(QColor(241, 194, 50), 7)
        p.setPen(yellow_pen)
        p.setBrush(QColor(241, 194, 50))
        
        # Horizontal "Wings"
        p.drawLine(QPointF(cx - 190, cy), QPointF(cx - 100, cy))
        p.drawLine(QPointF(cx + 190, cy), QPointF(cx + 100, cy))
        
        # Center Reference Polygon
        thickness = 7
        points = [
            QPoint(int(cx), int(cy + thickness/2)), 
            QPoint(int(cx - 60), int(cy + 30)), 
            QPoint(int(cx), int(cy + 10)), 
            QPoint(int(cx + 60), int(cy + 30))
        ]
        p.drawPolygon(QPolygonF([QPointF(pt) for pt in points]))
        # ACRON: Project body velocity onto the pitch ladder to position the FPV.
        u = self.u_fps
        v = self.v_fps
        down = self.w_fps

        # The F/D remains available when there is no usable forward FPV.
        velocity_valid = all(math.isfinite(value) for value in (u, v, down))
        if not velocity_valid or u < 1.0:
            fd_drawn = self._draw_flight_director(p, cx, cy)
            status = (
                "FPV: LOW FORWARD SPEED" if velocity_valid
                else "FPV: INVALID VELOCITY"
            )
            if fd_drawn:
                status += "\nF/D REF: AIRCRAFT"
            p.setPen(QPen(Qt.GlobalColor.white, 1))
            p.setFont(QFont("Consolas", 10))
            p.drawText(
                QRectF(cx - 190, cy + 95, 380, 48),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                status
            )
            return

        # Direction of motion relative to the aircraft
        horizontal_angle = math.degrees(math.atan2(v, u))
        vertical_angle = math.degrees(
            math.atan2(-down, math.hypot(u, v))
        )

        # Match the existing pitch ladder's angular scale
        pixels_per_degree = h / 80.0

        raw_x = cx + horizontal_angle * pixels_per_degree
        raw_y = cy - vertical_angle * pixels_per_degree

        # Keep the marker away from the tapes and lower compass
        fpv_x = max(w * 0.22, min(w * 0.78, raw_x))
        fpv_y = max(h * 0.08, min(h * 0.66, raw_y))

        # Clearly identify a direction beyond the display limits
        if fpv_x != raw_x or fpv_y != raw_y:
            p.setPen(QPen(Qt.GlobalColor.white, 1))
            p.setFont(QFont("Consolas", 9))
            p.drawText(
                QRectF(fpv_x - 90, fpv_y + 25, 180, 20),
                Qt.AlignmentFlag.AlignCenter,
                "FPV OFF SCALE"
            )

        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)

        # Center circle
        p.drawEllipse(QPointF(fpv_x, fpv_y), 10, 10)

        # Left wing
        p.drawLine(
            QPointF(fpv_x - 28, fpv_y),
            QPointF(fpv_x - 10, fpv_y)
        )

        # Right wing
        p.drawLine(
            QPointF(fpv_x + 10, fpv_y),
            QPointF(fpv_x + 28, fpv_y)
        )

        # Top stem
        p.drawLine(
            QPointF(fpv_x, fpv_y - 10),
            QPointF(fpv_x, fpv_y - 22)
        )
        self._draw_flight_director(p, fpv_x, fpv_y)

    def _draw_flight_director(self, p, reference_x, reference_y):
        """Draw against the FPV, or the aircraft reference if FPV is unavailable."""
        if not self.fd_enabled:
            return False
        if not all(math.isfinite(value) for value in (
            self.altitude_ft, self.selected_altitude_ft,
            self.heading_deg, self.selected_heading_deg
        )):
            return False

        w, h = self.width(), self.height()
        # ACRON: Use altitude error for the vertical cue and heading error for the lateral cue.
        altitude_error = (
            self.selected_altitude_ft - self.altitude_ft
        )

        # Starting display sensitivity: 100 ft = 10 pixels
        vertical_offset = altitude_error * 0.1

        # Limit separation from the FPV
        vertical_offset = max(-60.0, min(60.0, vertical_offset))

        # Shortest turn to the selected heading
        heading_error = (
            self.selected_heading_deg - self.heading_deg + 180.0
        ) % 360.0 - 180.0

        # Starting sensitivity: 1 degree = 2 pixels
        horizontal_offset = heading_error * 2.0
        horizontal_offset = max(
            -60.0, min(60.0, horizontal_offset)
        )

        fd_x = reference_x + horizontal_offset
        fd_x = max(24.0, min(w - 24.0, fd_x))
        fd_y = reference_y - vertical_offset

        # Keep the brackets inside the widget
        fd_y = max(24.0, min(h - 24.0, fd_y))

        p.setPen(QPen(QColor(255, 0, 255), 3))
        p.setBrush(Qt.BrushStyle.NoBrush)

        for sx, sy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            corner_x = fd_x + sx * 18
            corner_y = fd_y + sy * 18

            p.drawLine(
                QPointF(corner_x, corner_y),
                QPointF(corner_x - sx * 9, corner_y)
            )
            p.drawLine(
                QPointF(corner_x, corner_y),
                QPointF(corner_x, corner_y - sy * 9)
            )
        return True

class AttitudeIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg = AttitudeBackground(self)
        self.overlay = AttitudeOverlay(self)

    def resizeEvent(self, event):
        self.bg.setGeometry(0, 0, self.width(), self.height())
        self.overlay.setGeometry(0, 0, self.width(), self.height())

    def set_state(self, roll, pitch):
        self.bg.set_state(roll, pitch)
        self.overlay.set_state(roll, pitch)

    def set_velocity(self, u, v, w):
        self.overlay.set_velocity(u, v, w)

class ModeControlPanel(QWidget):
    """On-screen controls using the same target changes as the physical MCP."""
    # ACRON: Panel buttons send target steps, sync requests, and the F/D toggle.
    target_step_requested = pyqtSignal(str, int)
    sync_requested = pyqtSignal(str)
    fd_toggle_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QPushButton {background:#16191e; color:white; border:1px solid #666;"
            "border-radius:3px; padding:4px; min-width:24px;}"
            "QPushButton:checked {background:#401040; border-color:magenta;}"
            "QPushButton:disabled {color:#666;}"
        )
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(12)
        self.value_labels = {}
        self.sync_buttons = {}
        self.step_buttons = {}
        for key, title in [("speed_kt", "SPD / KT"),
                           ("heading_deg", "HDG / DEG"),
                           ("altitude_ft", "ALT / FT")]:
            group = QVBoxLayout()
            group.setSpacing(2)
            label = QLabel(title)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            group.addWidget(label)
            value = QLabel()
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value.setStyleSheet("color:magenta; font: bold 16px 'Consolas';")
            self.value_labels[key] = value
            group.addWidget(value)
            buttons = QHBoxLayout()
            minus, sync, plus = QPushButton("-"), QPushButton("Sync"), QPushButton("+")
            minus.clicked.connect(
                lambda checked=False, k=key: self.target_step_requested.emit(k, -1)
            )
            plus.clicked.connect(
                lambda checked=False, k=key: self.target_step_requested.emit(k, 1)
            )
            sync.clicked.connect(
                lambda checked=False, k=key: self.sync_requested.emit(k)
            )
            sync.setEnabled(False)
            self.sync_buttons[key] = sync
            self.step_buttons[key] = (minus, plus)
            for button in (minus, sync, plus):
                buttons.addWidget(button)
            group.addLayout(buttons)
            row.addLayout(group)
        self.fd_button = QPushButton("F/D")
        self.fd_button.setCheckable(True)
        self.fd_button.clicked.connect(lambda checked=False: self.fd_toggle_requested.emit())
        row.addWidget(self.fd_button)
        row.addStretch()

    def set_targets(self, targets):
        self.value_labels["speed_kt"].setText(f'{targets["speed_kt"]:.0f}')
        self.value_labels["heading_deg"].setText(f'{int(round(targets["heading_deg"])) % 360:03d}')
        self.value_labels["altitude_ft"].setText(f'{int(round(targets["altitude_ft"])):05d}')
        self.fd_button.setChecked(bool(targets["fd_enabled"]))

    def set_sync_available(self, key, available):
        self.sync_buttons[key].setEnabled(available)

# ==================== GENERIC TAPE (SPEED / ALTITUDE) ====================
class TapeWidget(QWidget):
    HEADER_HEIGHT = 28

    def __init__(self, label: str, fmt: str, color=QColor(255, 255, 255), parent=None):
        super().__init__(parent)
        self.label = label
        self.value = 0.0
        self.selected_value = None
        self.fmt = fmt
        self.color = color
        self.setMinimumSize(70, 280)

    def set_value(self, value):
        self.value = float(value)
        self.update()

    def set_selected_value(self, value):
        value = float(value)
        if not math.isfinite(value):
            return
        self.selected_value = value
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        magenta = QColor(255, 0, 255)
        is_speed = self.label == "TAS"

        # Selected value sits above the scrolling tape.
        p.setPen(magenta)
        p.setFont(QFont("Consolas", 13, QFont.Weight.Bold))
        selected_text = "---"
        if self.selected_value is not None:
            selected_text = (f"{self.selected_value:.0f}" if is_speed else
                             f"{int(round(self.selected_value)):05d}")
        p.drawText(QRectF(0, 0, self.width(), self.HEADER_HEIGHT),
                   Qt.AlignmentFlag.AlignCenter, selected_text)

        R = QRectF(self.rect()).adjusted(6, self.HEADER_HEIGHT + 6, -6, -6)
        cy = R.center().y()
        p.fillRect(R, QColor(0, 0, 0, 100))
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        p.drawRect(R)
        p.save()
        p.setClipRect(R)

        value_valid = math.isfinite(self.value)
        value = self.value if value_valid else 0.0
        spacing, scale = (10, 4.0) if is_speed else (100, 0.4)
        half_span = R.height() / (2 * scale)
        first = math.floor((value - half_span) / spacing) * spacing
        last = math.ceil((value + half_span) / spacing) * spacing
        if is_speed:
            first = max(0, first)
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.setFont(QFont("Consolas", 12))
        for tick in range(int(first), int(last) + spacing, spacing):
            y = cy + (value - tick) * scale
            if is_speed:
                p.drawLine(QPointF(R.right() - 2, y), QPointF(R.right() - 18, y))
                text = QRectF(R.left() + 2, y - 9, R.width() - 24, 18)
                alignment = Qt.AlignmentFlag.AlignRight
            else:
                p.drawLine(QPointF(R.left() + 2, y), QPointF(R.left() + 18, y))
                text = QRectF(R.left() + 20, y - 9, R.width() - 22, 18)
                alignment = Qt.AlignmentFlag.AlignLeft
            p.drawText(text, alignment | Qt.AlignmentFlag.AlignVCenter, str(tick))

        # Current value retains the white pointer box.
        if is_speed:
            points = [(R.right()-6, cy), (R.right()-12, cy+6),
                      (R.right()-12, cy+14), (R.left(), cy+14),
                      (R.left(), cy-14), (R.right()-12, cy-14),
                      (R.right()-12, cy-6)]
        else:
            points = [(R.left()+6, cy), (R.left()+12, cy+6),
                      (R.left()+12, cy+14), (R.right(), cy+14),
                      (R.right(), cy-14), (R.left()+12, cy-14),
                      (R.left()+12, cy-6)]
        pointer = QPolygonF([QPointF(x, y) for x, y in points])
        p.setBrush(Qt.GlobalColor.black)
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        p.drawPolygon(pointer)
        p.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        current_text = self.fmt.format(value) if value_valid else "--"
        p.drawText(pointer.boundingRect(), Qt.AlignmentFlag.AlignCenter, current_text)

        label_rect = QRectF(R.left(), R.bottom() - 20, R.width(), 20)
        p.fillRect(label_rect, Qt.GlobalColor.black)
        p.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        p.drawRect(label_rect)
        p.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.label)

        # ACRON: Mark selected speed or altitude on the tape; point to off-scale targets.
        if self.selected_value is not None and value_valid:
            raw_y = cy + (value - self.selected_value) * scale
            top, bottom = R.top() + 10, label_rect.top() - 10
            y = max(top, min(bottom, raw_y))
            x = R.right() - 8 if is_speed else R.left() + 8
            if raw_y < top or raw_y > bottom:
                base_y = y + 8 if raw_y < top else y - 8
                points = [(x, y), (x-6, base_y), (x+6, base_y)]
            elif is_speed:
                points = [(R.right()-1, y), (R.right()-12, y-7), (R.right()-12, y+7)]
            else:
                points = [(R.left()+1, y), (R.left()+12, y-7), (R.left()+12, y+7)]
            p.setPen(QPen(magenta, 2))
            p.setBrush(magenta)
            p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in points]))
        p.restore()


# ====================== VERTICAL RATE =========================

class RateWidget(QWidget):   # a little broken when its maxed out, maybe change the size in main_window.py to fix the clipping
    def __init__(self, parent = None):
        super().__init__(parent)
        self.value = 0.0

    def set_value(self, v: float):
        self.value = float(v) * 60
        self.update()  # Triggers paintEvent()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        R = self.rect()#.adjusted(8, 8, -8, -8)

        # Transparent background
        p.setBrush(QColor(0, 0, 0, 100))   # translucent gray

        # Limit of vertical speed
        limit = 2500

        # p.drawRect(R)
        cx = R.center().x()
        cy = R.center().y()
        rightoffset = 20

        # Box outline
        ratepoints = [QPointF(R.left(), R.top()),QPointF(R.right() - rightoffset, R.top()),QPointF(R.right() - rightoffset, cy - (30-rightoffset)),QPointF(R.left(), cy),QPointF(R.right() - rightoffset, cy + (30-rightoffset)),QPointF(R.right() - rightoffset, R.bottom()),QPointF(R.left(), R.bottom()),]
        ratepoly = QPolygonF(ratepoints)
        p.drawPolygon(ratepoly)

        # Ticks and tick numbers
        for percent in range(0, 100, 10):
            if percent == 50:
                continue  # don't draw middle tick
            y = int(percent/100 * R.height())
            p.drawLine(R.left(), y, R.left() + 5, y)

        ticks = [10, 30, 70, 90]
            # mapping from tick to label
        labels = {10: "2", 30: "1", 70: "1", 90: "2",}  # 1000 ft/m, 2000ft/m

        # draw 2, 1, 1, 2 at correct locations
        p.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        for percent in ticks:
            y = percent / 100 * R.height()
            p.drawText(
                QRectF(R.right() - 29, y - 7, 18, 14),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                labels[percent]
            )
                

        # Pointer
        heightoffset = -self.value * R.height() / 2 / limit
        p.setBrush(Qt.GlobalColor.black)
        ratepointerpoints = [QPointF(cx + 19, cy - (30-rightoffset) + heightoffset), QPointF(R.right() - rightoffset, cy - (30-rightoffset) + heightoffset),QPointF(R.left(), cy + heightoffset),QPointF(R.right() - rightoffset, cy + (30-rightoffset) + heightoffset), QPointF(cx + 19, cy + (30-rightoffset) + heightoffset)]
        ratepointer = QPolygonF(ratepointerpoints)
        p.drawPolygon(ratepointer)

        # Exact vertical rate in pointer
        text_rect = ratepointer.boundingRect().translated(-2,3)
        p.setPen(Qt.GlobalColor.white)
        p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))

        if math.isnan(self.value): # Nan Prtecion
            heightoffset = 0
        else:
            heightoffset = -self.value * R.height() / 2 / limit

        display_text = format_val(self.value)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignRight, display_text)

# ==================== COMPASS ====================
class CompassWidget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.heading = 0.0
        self.selected_heading = None
        self.setMinimumSize(180, 180)

    def set_heading(self, deg: float):
        self.heading = float(deg) % 360.0
        self.update()

    def set_selected_heading(self, deg):
        deg = float(deg)
        if math.isfinite(deg):
            self.selected_heading = deg % 360.0
            self.update()

    def paintEvent(self, e):
        # Draw compass circle and labels
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        R = self.rect().adjusted(8, 8, -8, -36)
        cx, cy = R.center().x(), R.center().y()
        r = min(R.width(), R.height()) * 0.42

        # Transparent background + circle
        p.setBrush(QColor(0, 0, 0, 100))   # translucent gray
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Heading ticks
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        radius = r
        for ang in range(0, 360, 30):
            a = math.radians(ang - self.heading)
            x1 = cx + math.sin(a) * radius * 0.93
            y1 = cy - math.cos(a) * radius * 0.93
            x2 = cx + math.sin(a) * radius
            y2 = cy - math.cos(a) * radius 
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        p.setBrush(Qt.GlobalColor.white)
        p.setPen(QPen(Qt.GlobalColor.white, 1))        

        # Draw N, E, S, W
        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        for i, direction in enumerate(["N","E","S","W"]):
            ang = math.radians(i*90.0 - self.heading)
            x = cx + math.sin(ang) * (r - 14)
            y = cy - math.cos(ang) * (r - 14)
            p.drawText(QRectF(x-10, y-10, 20, 20),
                       Qt.AlignmentFlag.AlignCenter, direction)

    # Numeric heading display
        p.setFont(QFont("Consolas", 12))

        # Box rectangle
        box_rect = QRectF(cx - 20, R.top() - 5, 40, 20)

        # Semi-transparent fill (black with alpha)
        p.setBrush(QColor(0, 0, 0))   
        p.setPen(QPen(QColor(255, 255, 255, 220), 1.5))  # white border

        # Draw the transparent box
        p.drawRect(box_rect)

        # Draw heading text centered inside
        p.setPen(QColor(255, 255, 255))  # solid white text

        if math.isnan(self.heading): # nan protection
            display_heading = 0
        else:
            display_heading = int(round(self.heading))

        p.drawText(
            box_rect,
            Qt.AlignmentFlag.AlignCenter,
            f"{display_heading}"
        )

        # ACRON: Draw the selected heading relative to the current compass heading.
        if self.selected_heading is not None and math.isfinite(self.heading):
            angle = self.selected_heading - self.heading
            def ring_point(deg, radius):
                a = math.radians(deg)
                return QPointF(cx + math.sin(a) * radius,
                               cy - math.cos(a) * radius)
            p.setPen(QPen(QColor(255, 0, 255), 2))
            p.setBrush(QColor(255, 0, 255))
            p.drawPolygon(QPolygonF([
                ring_point(angle, r * 0.80),
                ring_point(angle - 6, r * 1.04),
                ring_point(angle + 6, r * 1.04)
            ]))
            p.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            selected = int(round(self.selected_heading)) % 360
            p.drawText(QRectF(0, self.height() - 27, self.width(), 24),
                       Qt.AlignmentFlag.AlignCenter, f"HDG {selected:03d}")


class VMap(QWidget): # This is unused and broken right now, supposed to be a vertial situation indicator
    def __init__(self):
        super().__init__()
        self.setMinimumSize(360, 160)

        self.pitch = 0.0          # degrees
        self.altitude = 0.0       # meters
        self.scale = 10          # meters per pixel? also altitude isnt in meters

    def set_state(self, pitch: float, altitude: float):
        self.pitch = float(pitch)
        self.altitude = float(altitude)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        R = self.rect()
        cx, cy = R.center().x(), R.center().y()

        # Background
        p.fillRect(R, QColor(20, 20, 20))
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.drawRect(R)

        # Vertical offset from altitude
        y_offset = -self.altitude / self.scale

        # Draw airplane
        p.save()
        p.translate(cx, cy + y_offset)
        p.rotate(-self.pitch)

        plane = QPolygonF([
            QPointF(0, 0),
            QPointF(0, -12),
            QPointF(22, 0)
        ])

        p.setBrush(QColor(0, 0, 0))
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.drawPolygon(plane)

        p.restore()

        # Grid logic
        grid_spacing_px = 500 / self.scale # pixels per box
        # # x_offset = (self.x / self.scale) % grid_spacing_px
        # y_offset = (self.altitude / self.scale) % grid_spacing_px

        pen = QPen(QColor(80, 80, 80), 1, Qt.PenStyle.DashLine)
        p.setPen(pen)

        # Draw a grid
        grid_range = int(R.width())
        lines = []
        # for x in range(-grid_range, grid_range, int(grid_spacing_px)):
        #     lines.append(QLineF(x - x_offset, -grid_range, x - x_offset, grid_range))
        for y in range(-grid_range, grid_range, int(grid_spacing_px)):
            lines.append(QLineF(-grid_range, y, grid_range, y))
        
        p.drawLines(lines)


class SemicircleIndicator(QWidget):     # Used for RPM
    def __init__(
        self,
        parent=None,
        value= 0,
        label="PROP1",
        unit="RPM",
        valuerange = (0, 1250), # Actual numbers
        greenrange = (9, 98), # Percent its reversed though sorry
        yellowrange = (5, 10), # percent its reversed though sorry
        redrange = (2,5) # percent its reversed though sorry
    ):
        super().__init__(parent)

        self.value = value
        self.valuepercent = (value - valuerange[0]) / (valuerange[1] - valuerange[0])
        self.label = label
        self.unit = unit
        self.valuerange = valuerange
        self.greenrange = greenrange
        self.yellowrange = yellowrange
        self.redrange = redrange

    def set_value(self, v: float):
        self.value = float(v)

        # clamp to range
        vmin, vmax = self.valuerange
        self.value = max(vmin, min(self.value, vmax))

        # recompute percent
        self.valuepercent = (self.value - vmin) / (vmax - vmin)

        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # bounding box
        R = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        #p.drawRect(R) # draw outline

        percentSize = 0.9

        # new R is Smaller bounding box
        R = QRectF(int((1-percentSize) * R.height() / 2), int((1-percentSize) * R.height() / 2), int(R.height() * 0.9), int(R.height() * 0.9))
        W = R.width()
        H = R.height()
        #p.drawRect(R) # draw outline

        # white arc
        pen = QPen(QColor(255, 255, 255), 2)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        start_deg = 15
        span_deg = 180 #180 - start_deg
        p.drawArc(R, int((start_deg)* 16 - 10), int(span_deg * 16) + 20)      

        cx, cy = R.center().x(), R.center().y()
        radius = int(R.width() / 2)
        offset = 0

        # green ring
        pen = QPen(QColor(115, 200, 70), 6)
        p.setPen(pen)

        gstartdeg = (span_deg * self.greenrange[0] / 100) + start_deg
        gspandeg = (span_deg * (self.greenrange[1] - self.greenrange[0]) / 100)
        p.drawArc(R.adjusted(5,5,-5,-5), int((gstartdeg)* 16 - 10), int(gspandeg * 16) + 20)

        # yellow ring
        pen = QPen(QColor(255, 255, 0), 6)
        p.setPen(pen)

        ystartdeg = (span_deg * self.yellowrange[0] / 100) + start_deg
        yspandeg = (span_deg * (self.yellowrange[1] - self.yellowrange[0]) / 100)

        p.drawArc(R.adjusted(5,5,-5,-5), int((ystartdeg)* 16 - 10), int(yspandeg * 16) + 20)

        # red ring
        pen = QPen(QColor(255, 0, 0), 6)
        p.setPen(pen)

        rstartdeg = (span_deg * self.redrange[0] / 100) + start_deg
        rspandeg = (span_deg * (self.redrange[1] - self.redrange[0]) / 100)

        p.drawArc(R.adjusted(5,5,-5,-5), int((rstartdeg)* 16 - 10), int(rspandeg * 16) + 20)


        # ticks
        tickmultiplier = 1   # 0 = 2 ticks, 1 = 5 ticks, 2 = 9 ticks, 3 = 17 ticks, 4 = 33 ticks, 
        ticknum = pow(2,tickmultiplier+1)+1

        pen = QPen(QColor(255, 255, 255), 2)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        step = span_deg / (ticknum - 1)

        # draw ticks
        for i in range(ticknum):
            ang = start_deg + i * step
            a = math.radians(ang)
            x1 = cx + math.cos(a) * radius * 1
            y1 = cy - math.sin(a) * radius * 1 + offset
            x2 = cx + math.cos(a) * radius * 0.85
            y2 = cy - math.sin(a) * radius * 0.85 + offset
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    # pointer
        p.setBrush(Qt.GlobalColor.white)
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        pt1 = QPointF(cx, cy - radius)
        pt2 = QPointF(cx + 6, cy -  radius + 15)
        pt3 = QPointF(cx - 6, cy -  radius + 15)
        #self.valuepercent
        
        if math.isnan(self.valuepercent): # nan Protection
            angle = start_deg - 90 
        else:
            angle = (span_deg * self.valuepercent) + start_deg - 90 - start_deg * 2

        theta = math.radians(angle)

        def rotate_point(x, y, cx, cy, theta): # rotate points (x,y) of pointer around center (cx,cy) given angle theta
            dx = x - cx
            dy = y - cy
            xr = cx + dx * math.cos(theta) - dy * math.sin(theta)
            yr = cy + dx * math.sin(theta) + dy * math.cos(theta)
            return QPointF(xr, yr)

        pt1adjusted = rotate_point(pt1.x(), pt1.y(), cx, cy, theta)
        pt2adjusted = rotate_point(pt2.x(), pt2.y(), cx, cy, theta)
        pt3adjusted = rotate_point(pt3.x(), pt3.y(), cx, cy, theta)

        # draw rotated pointer
        tris = (pt1adjusted, pt2adjusted, pt3adjusted)
        p.drawPolygon(tris)


    # number
        textbox = QRectF(R.width() * 0.85, int(R.height()/2)+5, float(R.width()*0.3), float(R.height()*0.15))
        if (self.value > (100 - self.redrange[1]-3)/100 * self.valuerange[1]): # if in red range, make text box red
            p.setPen(Qt.PenStyle.NoPen)                     
            p.setBrush(QColor(255, 0, 0)) # red             
            p.drawRect(textbox)
            p.setPen(QPen(QColor(255, 255, 255))) # white      
        else:
            p.setPen(QPen(QColor(115, 200, 70))) # green         

        p.setFont(QFont("Consolas", 12))
        p.drawText(textbox, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, format_val(self.value))

        # label (PROP # in this case)  
        p.setPen(QPen(Qt.GlobalColor.white))
        p.setFont(QFont("Consolas", 12))

        p.drawText(QRectF(5, int(R.height()*0.35), float(R.width()), float(R.height()*0.2)),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self.label)
                
        # unit (RPM in this case)
        p.setPen(QPen(Qt.GlobalColor.white))
        p.setFont(QFont("Consolas", 12))

        p.drawText(QRectF(5, int(R.height()*0.5), float(R.width()), float(R.height()*0.2)),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self.unit)


class VerticalIndicator(QWidget): # Used for Power / Batter indicators
    def __init__(
        self,
        parent=None,
        value= 0,
        label="POWER",
        unit="KW",
        valuerange = (0, 2200), # Actual numbers
        greenrange = (2, 89), # Percent
        yellowrange = (90, 98), # Percent
        redrange = (179,180) # Percent  (I have crazy high number here just because I want no red range for power.)
    ):
        super().__init__(parent)

        self.value = value
        self.valuepercent = (value - valuerange[0]) / (valuerange[1] - valuerange[0])
        self.label = label
        self.unit = unit
        self.valuerange = valuerange
        self.greenrange = greenrange
        self.yellowrange = yellowrange
        self.redrange = redrange

    def set_value(self, v: float):
        self.value = float(v)

        # clamp to range
        vmin, vmax = self.valuerange
        self.value = max(vmin, min(self.value, vmax))

        # recompute percent
        self.valuepercent = (self.value - vmin) / (vmax - vmin)

        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # bounding box
        R = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        # p.drawRect(R) # show outline

        percentSize = 0.7

        dx = R.width() * (1 - percentSize) / 2
        dy = R.height() * (1 - percentSize) / 2

        # adjusted bounding box
        R = QRectF(
            R.x() + dx,
            R.y() + dy,
            R.width() * percentSize,
            R.height() * percentSize
        )

        right = R.x() + R.width()
        bottom = R.y() + R.height()
        left = R.x()
        top = R.y()

        # red line      draw first because otherwise the red text box doesnt align with the red line
        pen = QPen(QColor(255, 0, 0), 6)
        p.setPen(pen)

        p.drawLine(QLine(int(right-5), int(bottom - R.height() * self.redrange[0] / 100), int(right-5), int(bottom - R.height() * self.redrange[1] / 100)))

        # green line
        pen = QPen(QColor(115, 200, 70), 6)
        p.setPen(pen)

        p.drawLine(QLine(int(right-5), int(bottom - R.height() * self.greenrange[0] / 100), int(right-5), int(bottom - R.height() * self.greenrange[1] / 100)))

        # yellow line
        pen = QPen(QColor(255, 255, 0), 6)
        p.setPen(pen)
        p.drawLine(QLine(int(right-5), int(bottom - R.height() * self.yellowrange[0] / 100), int(right-5), int(bottom - R.height() * self.yellowrange[1] / 100)))

        # white outline
        pen = QPen(QColor(255, 255, 255), 3)
        pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        p.setPen(pen)

        outlinewidth = 40

        # thick white line outlines
        lines = [
            QLine(int(right - outlinewidth), int(top),
                int(right), int(top)),

            QLine(int(right), int(top),
                int(right), int(bottom)),

            QLine(int(right), int(bottom),
                int(right - outlinewidth), int(bottom))
        ]

        p.drawLines(lines)


    # pointer
        p.setBrush(Qt.GlobalColor.white)
        p.setPen(QPen(Qt.GlobalColor.white, 1))


        if math.isnan(self.valuepercent): # NAN protection
            pointer_y = bottom
        else:
            pointer_y = bottom - (R.height() * self.valuepercent) # convert percent into Y position

        # pointer size
        pointer_width = 15
        pointer_height = 12

        # position it slightly right of the bar
        px = right - 5

        pt1 = QPointF(px, pointer_y)  # tip
        pt2 = QPointF(px - pointer_width, pointer_y - pointer_height / 2)
        pt3 = QPointF(px - pointer_width, pointer_y + pointer_height / 2)

        tris = (pt1, pt2, pt3)
        p.drawPolygon(tris)

    # number
        textbox = QRectF(R.width() * 0.5, R.height() + 35, float(R.width() * 0.75), float(R.height()*0.12)) # below indicator

        if (self.redrange[0] <= self.valuepercent * 100 <= self.redrange[1]): # draw red if in red range, else green.
            p.setPen(Qt.PenStyle.NoPen)                     
            p.setBrush(QColor(255, 0, 0)) # red background             
            p.drawRect(textbox)
            p.setPen(QPen(QColor(255, 255, 255))) # white text    
        else:
            p.setPen(QPen(QColor(115, 200, 70))) # green       
        p.setFont(QFont("Consolas", 12))
        p.drawText(textbox, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, format_val(self.value))        
        
    # label (example: Power) positioned above indicator
        p.setPen(QPen(Qt.GlobalColor.white))
        p.setFont(QFont("Consolas", 10))

        p.drawText(QRectF(0, -7, float(R.width() + 20), float(R.height()*0.2)),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self.label)
                
    # unit (example: KW) positioned above indicator
        p.setPen(QPen(Qt.GlobalColor.white))
        p.setFont(QFont("Consolas", 8))

        p.drawText(QRectF(int(R.width() / 4), 5, float(R.width()), float(R.height()*0.2)),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self.unit)

class BasicText(QWidget):  # Used for range and endurance, its just text with a number next to it
    def __init__(
        self,
        parent=None,
        value= 0,
        label="RANGE NM",
        unit="NM",
    ):
        super().__init__(parent)

        self.value = value
        self.label = label
        self.unit = unit

    def set_value(self, v: float):
        self.value = float(v)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        R = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(Qt.GlobalColor.white, 1))
        p.drawRect(R)

        # Value on right
        textbox = QRectF(int(R.width() * 3/4), 0, int(R.width() * 1/4), int(R.height()))
        p.setPen(QPen(QColor(255, 255, 255)))           
        p.setPen(QPen(QColor(115, 200, 70)))            
        p.setFont(QFont("Consolas", 12))
        p.drawText(textbox, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, format_val(self.value))

        # Label on left
        p.setPen(QPen(Qt.GlobalColor.white))
        p.setFont(QFont("Consolas", 12))

        labelbox = QRectF(0, 0, int(R.width() * 3/4), int(R.height()))

        p.drawText(labelbox,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self.label) 


class PreflightChecklist(QWidget):  # its quite ugly and dumb right now, and covers range and endurance, so it could be changed a lot
    def __init__(self):
        super().__init__()


        layout = QVBoxLayout()
        self.setLayout(layout)

        items = [
            "Flux capacitor stable",
            "Door closed",
            "Battery charged",
            "Seatbelt fastened",
            "Check weather",
        ]

        self.checkboxes = []

        for text in items:
            cb = QCheckBox(text)
            cb.stateChanged.connect(self.check_all)
            layout.addWidget(cb)
            self.checkboxes.append(cb)

    # hide item if its checked 
    def check_all(self):   
        if all(cb.isChecked() for cb in self.checkboxes):
            self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        R = self.rect()
        p.fillRect(R, QColor(0, 0, 0))
        p.setPen(QPen(Qt.GlobalColor.white, 2))
        p.drawRect(R)

