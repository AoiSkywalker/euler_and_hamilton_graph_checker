import sys
import math
import random
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QListWidget, QListWidgetItem, 
                             QSlider, QLineEdit, QStackedWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QGraphicsDropShadowEffect, QGroupBox, QRadioButton, QInputDialog)
from PyQt5.QtCore import Qt, QPointF, QTimer, pyqtSignal, QRectF, QSize
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QPainterPath

from controllers.euler import euler_check, fleury, sub_euler_check
from controllers.hamilton import solve_delivery_problem, solve_hamilton_brute

# --- THEME COLORS ---
THEME = {
    "sidebar": "#0f172a",       # xanh đen 
    "white": "#ffffff",         # trắng 
    "indigo": "#4f46e5",        # chàm
    "indigo_hover": "#4338ca",  # chàm đậm
    "border": "#e2e8f0",        # trắng xanh 
    "text_main": "#1e293b",     # đen 
    "text_muted": "#64748b",    # xám tro
    "success": "#10b981",       # xanh lục
    "error": "#ef4444",         # đỏ cam
    "path": "#facc15",          # hồng
    "accent": "#f43f5e",        # đỏ hồng
    "grid": "#f1f5f9"           # trắng 
}

# Luồng tương tác người dùng
class GraphCanvas(QWidget):
    nodeSelected = pyqtSignal(int)          # Tín hiệu chọn node 
    edgeSelected = pyqtSignal(dict)         # Tín hiệu chọn cạnh
    graphChanged = pyqtSignal()             # Tín hiệu đồ thị đã bị thay đổi 
    
    def __init__(self, parent=None):
        super().__init__(parent)        
        self.nodes = []                     # Danh sách node 
        self.edges = []                     # Danh sách cạnh 
        self.path = []                      # Danh sách đường đi 
        self.sim_step = -1                  # Bước mô phỏng hiện tại. Mặc định -1 chưa có mô phỏng 
        self.dragging_node = None           # Node người dùng đang kéo 
        self.edge_start_node = None         # Node người dùng đang chọn để chuẩn bị tạo cạnh mới 
        self.is_directed = False            # Flag đồ thị có hướng / vô hướng. Mặc định vô hướng 
        self.is_weighted = True             # Flag đồ thị có trọng số / không trọng số. Mặc định có trọng số 
        self.setMouseTracking(True)         # Theo dõi chuột liên tục (cấu hình PyQt)

    # Chức năng cập nhật đồ thị
    def set_data(self, nodes, edges, path, sim_step, is_directed, is_weighted):
        self.nodes = nodes
        self.edges = edges
        self.path = path
        self.sim_step = sim_step
        self.is_directed = is_directed
        self.is_weighted = is_weighted
        self.update()

    def paintEvent(self, event):                            # Ghi đè hàm paintEvent của PyQt
        """Vẽ toàn bộ đồ thị lên màn hình """
        painter = QPainter(self)                            # Khởi tạo painter 
        painter.setRenderHint(QPainter.Antialiasing)        # chống răng cưa 
        
        # Background & Shadow
        rect = self.rect().adjusted(20, 20, -20, -20)       # Thụt lề vào trong 20px từ cả 4 phía
        painter.setBrush(QColor(THEME["white"]))            # painter đổ màu trắng 
        painter.setPen(QPen(QColor(THEME["border"]), 2))    # painter viền màu border, độ dày 2px 
        painter.drawRoundedRect(rect, 25, 25)               # Bo góc 
        
        # Grid
        painter.setPen(QPen(QColor(THEME["grid"]), 1))      # painter viền màu grid, độ dày 1px 
        step = 40                                           # khoảng cách giữa các grid là 40px, cách border 10px
        for x in range(int(rect.left()) + step, int(rect.right()), step):
            painter.drawLine(x, int(rect.top() + 10), x, int(rect.bottom() - 10))
        for y in range(int(rect.top()) + step, int(rect.bottom()), step):
            painter.drawLine(int(rect.left() + 10), y, int(rect.right() - 10), y)

        # Edges
        for edge in self.edges:
            u_node = self.nodes[edge["source"]]             # Node nguồn 
            v_node = self.nodes[edge["target"]]             # Node đích 
            u = QPointF(u_node["pos"][0], u_node["pos"][1]) # Tạo toạ độ node nguồn 
            v = QPointF(v_node["pos"][0], v_node["pos"][1]) # Tạo toạ độ node đích 
            self.draw_edge(painter, u, v, edge)             # Vẽ cạnh giữa node nguồn và node đích 

        # Highlight Path
        if self.path and self.sim_step >= 0:                        # Nếu có đường đi và tiến trình mô phỏng sẵn sàng  
            for i in range(min(self.sim_step, len(self.path)-1)):   # Chỉ vẽ đến bước mô phỏng hiện tại 
                u_node = self.nodes[self.path[i]]                   # Node trước 
                v_node = self.nodes[self.path[i+1]]                 # Node sau 
                u = QPointF(u_node["pos"][0], u_node["pos"][1])     # Tạo toạ độ node trước 
                v = QPointF(v_node["pos"][0], v_node["pos"][1])     # Tạo toạ độ node sau 
                
                painter.setPen(QPen(QColor(254, 240, 138), 12))     # painter viền màu vàng chanh, độ dày 12px 
                painter.drawLine(u, v)                              # vẽ cạnh giữa 2 node trước và sau (phần highlight)
                painter.setPen(QPen(QColor(THEME["path"]), 6))      # painter viền màu path, độ dày 6px 
                painter.drawLine(u, v)                              # Vẽ cạnh giữa 2 node trước và sau (vẽ đè)

        # Nodes
        for node in self.nodes:                                                         # Duyệt vét cạn để vẽ từng node 
            current_node = QPointF(node["pos"][0], node["pos"][1])                      # Toạ độ node hiện tại 
            is_curr = self.sim_step >= 0 and node["id"] == self.path[self.sim_step]     # Flag kiểm tra node hiện tại có đang trong quá trình mô phỏng 
            is_path = self.sim_step >= 0 and node["id"] in self.path[:self.sim_step]    # Flag kiểm tra node hiện tại có đang thuộc đường đi đang mô phỏng 
            
            # Viền node hiện tại : nếu is_curr thì màu accent : nếu is_path tnì màu indigo : nếu ko thì màu xám đen 
            outer_color = QColor(THEME["accent"]) if is_curr else (QColor(THEME["indigo"]) if is_path else QColor(51, 65, 85)) 
            # Ruột node hiện tại : nếu is_cur hoặc is_path thì giống viền node đó : nếu ko thì màu trắng 
            inner_color = QColor(THEME["white"]) if not (is_curr or is_path) else outer_color 
            
            painter.setPen(QPen(outer_color, 2))                      # painter viền màu outer_color, độ dày 2px 
            painter.setBrush(QBrush(inner_color))                     # painter đổ màu inner_color
            painter.drawEllipse(current_node, 21, 21)                 # vẽ hình tròn bán kính 21px 
            
            # label : nếu is_curr hoặc is_path thì màu trắng : nếu không thì màu text-main
            # font Arial bold 11px, align chính giữa khung vuông ảo cạnh 42, nội dung tên node A B C...
            painter.setPen(QColor(THEME["white"]) if (is_curr or is_path) else QColor(THEME["text_main"]))
            painter.setFont(QFont("Arial", 11, QFont.Bold))                                         
            painter.drawText(QRectF(current_node.x()-21, current_node.y()-21, 42, 42), Qt.AlignCenter, node["label"])

        # Hiệu ứng kéo-thả node 
        if self.edge_start_node:                                            # Nếu chọn và kéo node 
            painter.setPen(QPen(QColor(THEME["accent"]), 2, Qt.DashLine))   # painter viền màu accent, độ dày 2px, đứt nét 
            mouse_pos = self.mapFromGlobal(self.cursor().pos())             # chuyển toạ độ con trỏ hiện tại từ hệ quy chiếu toàn cục (màn hình máy tính) sang hệ quy chiếu cục bộ (GraphCanvas)
            painter.drawLine(QPointF(self.edge_start_node["pos"][0], self.edge_start_node["pos"][1]), mouse_pos) # Vẽ cạnh từ node tới chuột 

    def draw_edge(self, painter, u, v, edge):
        """Vẽ cạnh edge bằng painter giữa 2 nodes u và v"""
        edge_color = QColor(203, 213, 225)                          # Màu cạnh 
        edge_width = 2                                              # Độ dày cạnh 2px 
        painter.setPen(QPen(edge_color, edge_width))                # painter màu edge_color, dày edge_width 
        painter.drawLine(u, v)                                      # Vẽ cạnh giữa 2 node u và v 
        
        if self.is_directed:                                        # Nếu đồ thị có hướng thì vẽ mũi tên chỉ hướng 
            angle = math.atan2(v.y() - u.y(), v.x() - u.x())        # Tính góc [-π;π] rad 
            node_radius = 21                                        # Bán kính node 21px 
            end_point = QPointF(v.x() - node_radius * math.cos(angle), v.y() - node_radius * math.sin(angle)) # Toạ độ ngọn của vector 

            arrow_size = 12                                         # Độ dài cánh mũi tên 12px, cánh trên và cánh dưới tạo góc π/6 so với vector ban đầu
            p1 = end_point - QPointF(arrow_size * math.cos(angle - math.pi/6), arrow_size * math.sin(angle - math.pi/6)) 
            p2 = end_point - QPointF(arrow_size * math.cos(angle + math.pi/6), arrow_size * math.sin(angle + math.pi/6))
            
            painter.setBrush(QColor(edge_color))                    # painter đổ màu edge_color 
            painter.setPen(Qt.NoPen)                                # painter không viền 
            painter.drawPolygon(QPolygonF([end_point, p1, p2]))     # Nối 3 toạ độ của tam giác và tô màu
            
        if self.is_weighted:                                        # Nếu đồ thị có trọng số thì hiển thị trọng số 
            mid = (u + v) / 2                                       # Toạ độ trung điểm giữa 2 nodes u và v 
            dx = v.x() - u.x()                                      # delta x 
            dy = v.y() - u.y()                                      # delta y 
            length = math.sqrt(dx*dx + dy*dy) or 1                  # Độ dài cạnh u và v. Nếu 2 node trùng (cạnh 0) thì trả về 1 (tránh ctheo dòng tiếp theo)
            nx, ny = -dy/length, dx/length                          # Vector pháp tuyến đơn vị
            side = 1 if edge["target"] % 2 == 0 else -1             # Hướng dịch toạ độ trung điểm : lên (1) nếu node đích chẵn : xuống (-1) nếu node đích lẻ 
            mid += QPointF(nx * 22 * side, ny * 22 * side)          # Dịch toạ độ trung điểm theo đường trung trực 22px
            
            label_rect = QRectF(mid.x() - 20, mid.y() - 14, 40, 28) # Tạo khung hình chữ nhật, tâm toạ độ trung điểm đã dịch, dài 40px rộng 28px cho trọng số 
            painter.setPen(QPen(edge_color, 1))                     # painter viền edge_color, độ dày 1px 
            painter.setBrush(QColor(255, 255, 255, 220))            # painter đổ màu trắng trong suốt nhẹ 
            painter.drawRoundedRect(label_rect, 8, 8)               # Vẽ hình chữ nhật bo góc 
            
            painter.setPen(QColor(THEME["text_main"]))              # painter viền text_main 
            painter.setFont(QFont("Arial", 10))                 # font Arial 10px 
            painter.drawText(label_rect, Qt.AlignCenter, str(edge["weight"]))   # Hiển thị trọng số, align chính giữa
           
    def mousePressEvent(self, event):                                   # Ghi đè hàm thư viện của PyQt
        """Sự kiện click chuột -> lưu trữ node hoặc cập nhật cạnh"""
        pos = event.pos()                                               # Lấy toạ độ click chuột trên hệ quy chiếu GraphCanvas 
        if event.button() == Qt.LeftButton:                             # Nếu click chuột trái -> chức năng di chuyển, tạo sửa cạnh 
            for node in self.nodes:                                     # Vét cạn 
                dist = math.sqrt((node["pos"][0] - pos.x())**2 + (node["pos"][1] - pos.y())**2)
                if dist < 21:                   # Nếu click vào node (độ dài node so với vị trí click bé hơn 21)
                    self.dragging_node = node   # ghi nhớ node cho hàm mouseMoveEvent       -> di chuyển node
                    self.edge_start_node = node # ghi nhớ node cho hàm mouseReleaseEnode    -> tạo cạnh mới 
                    return

            if self.is_weighted:                                        # Nếu đồ thị có trọng số 
                for edge in self.edges:                                 # Vét cạn các node 
                    u_node = self.nodes[edge["source"]]                 # node nguồn 
                    v_node = self.nodes[edge["target"]]                 # node đích  
                    u = QPointF(u_node["pos"][0], u_node["pos"][1])     # Toạ độ node nguồn  
                    v = QPointF(v_node["pos"][0], v_node["pos"][1])     # Toạ độ node đích  
                    mid = (u + v) / 2                                   # Toạ độ trung điểm giữa 2 node nguồn và đích 
                    dx = v.x() - u.x()                                  # delta x
                    dy = v.y() - u.y()                                  # delta y 
                    length = math.sqrt(dx*dx + dy*dy) or 1              # Độ dài giữa 2 node 
                    nx, ny = -dy/length, dx/length                      # Vector pháp tuyến đơn vị 
                    side = 1 if edge["target"] % 2 == 0 else -1         # Hướng dịch toạ độ trung điểm : lên (1) nếu node đích chẵn : xuống (-1) nếu node đích lẻ 
                    mid += QPointF(nx * 22 * side, ny * 22 * side)      # Dịch toạ độ trung điểm theo đường trung trực 22px
                    label_rect = QRectF(mid.x() - 20, mid.y() - 14, 40, 28) # Tạo khung hình chữ nhật, tâm toạ độ trung điểm đã dịch, dài 40px rộng 28px cho trọng số 
                    if label_rect.contains(pos.x(), pos.y()):               # Nếu click trong khung hình chữ nhật 
                        new_w, ok = QInputDialog.getInt(self, "Sửa trọng số", "Nhập trọng số mới:", edge["weight"], 1, 1000)
                        if ok:                                          # Prompt sửa trọng số giới hạn trong đoạn [1,1000]
                            edge["weight"] = new_w                      # Cập nhật trọng số 
                            self.graphChanged.emit()                    # Gửi tín hiệu đồ thị đã thay đổi 
                            self.update()                               # Cập nhật ứng dụng 
                        return

        elif event.button() == Qt.RightButton:                          # Nếu click chuột phải -> chức năng : xoá cạnh 
            for i, edge in enumerate(self.edges):                       # Duyệt danh sách cạnh 
                p1 = self.nodes[edge["source"]]["pos"]                  # Toạ độ node nguồn 
                p2 = self.nodes[edge["target"]]["pos"]                  # Toạ độ node đích 
                mid = QPointF((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)         # Trung điểm giữa 2 node 
                if math.sqrt((mid.x() - pos.x())**2 + (mid.y() - pos.y())**2) < 30: # Nếu click gần trung điểm (khoảng cách trung điểm đến vị trí click bén hơn 30)
                    self.edges.pop(i)                                   # Xoá cạnh 
                    self.graphChanged.emit()                            # Gửi tín hiệu đồ thị đã thay đổi 
                    self.update()                                       # Cập nhật ứng dụng
                    break

    def mouseMoveEvent(self, event):                                    # Ghi đè hàm mouseMoveEvent của PyQt 
        """Sự kiện di chuột -> di chuyển node """
        if self.dragging_node:                                          # Nếu có node đang di chuyển thì cập nhật toạ độ theo toạ độ chuột
            self.dragging_node["pos"] = [event.pos().x(), event.pos().y()]
            self.update()

    def mouseReleaseEvent(self, event):                                 # Ghi đè hàm mousReleaseEvent của PyQt 
        """Sự kiện thả chuột -> Tạo cạnh mới"""
        if self.edge_start_node:
            pos = event.pos()
            # Vét cạn kiểm tra từng node (chừa node hiện tại vừa thả chuột)
            for node in self.nodes:
                if node == self.edge_start_node: continue 
                # Kiểm tra khoảng cách giữa 2 node có gần sát nhau (30px) ?
                if (math.sqrt((node["pos"][0] - pos.x())**2 + (node["pos"][1] - pos.y())**2)) < 30:
                    # Kiểm tra nếu đã tồn tại cạnh (liên thông)
                    exists = False
                    for e in self.edges:
                        if e["source"] == self.edge_start_node["id"] and e["target"] == node["id"]:
                            exists = True; break
                    if not exists:
                        # Chưa có cạnh -> Tạo cạnh với độ dài ngẫu nhiên từ 10 đến 50
                        self.edges.append({"source": self.edge_start_node["id"], "target": node["id"], "weight": random.randint(10, 50)})
                        self.graphChanged.emit()
                    break
        self.dragging_node = None       # Huỷ node đang kéo 
        self.edge_start_node = None     # Huỷ 
        self.update()

# Luồng màn hình giới thiệu
class IntroScreen(QWidget):
    startRequested = pyqtSignal()           # Chức năng nút Start 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #080818; color: white;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Tiêu đề lớn - Retro Glow/Shadow Effect 
        title = QLabel("LÝ THUYẾT ĐỒ THỊ")
        title.setStyleSheet("""
            font-family: Arial; 
            font-size: 85px; 
            color: #ffffff; 
            letter-spacing: 5px;
            background: transparent;
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)           # Độ nhòe của bóng
        shadow.setColor(QColor("#4f46e5")) # Màu Indigo làm Glow
        shadow.setOffset(0, 0)             # Đổ bóng ngay tại tâm để tạo hiệu ứng phát sáng (Glow)
        title.setGraphicsEffect(shadow)
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # Tiêu đề nhỏ
        sub = QLabel("Chu trình Euler, chu trình Hamilton và bài toán người đưa thư")
        sub.setStyleSheet("color: #fac415; font-size: 20px; font-weight: bold; margin-bottom: 40px;")
        layout.addWidget(sub, alignment=Qt.AlignCenter)
        
        # Thông tin sinh viên
        members_label = QLabel("Sinh viên thực hiện")
        members_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(members_label, alignment=Qt.AlignCenter)
        
        grid = QHBoxLayout()
        col1 = QVBoxLayout(); col2 = QVBoxLayout()
        all_members = ["Phan Đức Tài", "Phan Gia Khang", "Phan Quốc An", "Thái Hoàng Huy", "Tôn Thất Thiên Bảo", "Trần Danh Dũng", "Trần Đình Nhật", "Trần Đình Toàn", "Trần Đình Huy Văn", "Trần Đức Trí"]
        for i, m in enumerate(all_members):
            l = QLabel(m)
            l.setStyleSheet("color: white; font-size: 15px; background: transparent; border: none;")
            if i < 5: col1.addWidget(l, alignment=Qt.AlignCenter)
            else: col2.addWidget(l, alignment=Qt.AlignCenter)
        grid.addLayout(col1); grid.addLayout(col2)
        layout.addLayout(grid)
        
        btn = QPushButton("BẮT ĐẦU")                    # Giao diện nút Start
        btn.setFixedSize(220, 65)                       # Kích thước nút Start
        btn.setStyleSheet(f"background-color: {THEME['indigo']}; color: white; font-weight: bold; font-size: 18px; border-radius: 20px; margin-top: 40px;")
        btn.clicked.connect(self.startRequested.emit)   # Click vào để thực hiện chức năng nút Start 
        layout.addWidget(btn, alignment=Qt.AlignCenter) # Thêm nút Start vào bố cục cha 
        
        footer = QLabel("© 2026 - Trường Đại học Bách khoa - Đại học Quốc gia Thành phố Hồ Chí Minh")
        footer.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 12px; margin-top: 50px;")
        layout.addWidget(footer, alignment=Qt.AlignCenter)
        
class AppWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Background trắng 
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setStyleSheet(f"""
            AppWidget {{
                background-color: {THEME['white']};
            }}
        """)

        # State - Các trạng thái của ứng dụng ban đầu 
        self.algorithm = "EULER FULL GRAPH"         # Thuật toán hiện tại để giải đồ thị. Mặc định là tìm chu trình Euler 
        self.is_directed = False                    # Flag đồ thị vô hướng / có hướng 
        self.is_weighted = True                     # Flag đồ thị có trọng số / không trọng số
        self.node_count = 6                         # Số node của đồ thị. Mặc định là 6 nodes 
        self.nodes = []                             # Danh sách node 
        self.edges = []                             # Danh sách cạnh 
        self.path = []                              # Danh sách đường đi 
        self.sim_step = -1                          # Bước mô phỏng hiện tại 
        self.is_playing = False                     # Flag quá trình mô phỏng đang chạy / đang dừng 
        self.sim_speed = 5                          # Tốc độ mô phỏng. Mặc định là 5x
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.play_step)
        self.init_ui()
        
        # Tạo sinh đồ thị
        self.init_graph()
        # Nhận tín hiệu đồ thị thay đổi để reset mô phỏng 
        self.canvas.graphChanged.connect(self.reset_simulation_state)

    def init_ui(self):
        layout = QHBoxLayout(self)                          # Bố cục cha 
        layout.setContentsMargins(0, 0, 0, 0)               # Tràn viền màn hình 
        layout.setSpacing(0)                                # Không tạo khe hở giữa các bố cục con 
        
        # Tiêu đề ứng dụng
        brand = QLabel("Hameur", styleSheet="color: white; font-size: 28px; font-weight: bold;")

        # Sidebar bên trái ứng dụng 
        sidebar = QFrame()                                  # Tạo khung sidebar 
        sidebar.setFixedWidth(300)                          # Chiều rộng sidebar 300px 
        sidebar.setStyleSheet(f"background-color: {THEME['sidebar']};")
        sidebar_layout = QVBoxLayout(sidebar)               # Tạo bố cục sidebar (layout sidebar)
        sidebar_layout.setContentsMargins(20, 40, 20, 20)   # Khoảng trống (margin) bao quanh
        sidebar_layout.addWidget(brand)                     # Thêm Tiêu đề ứng dụng vào layout sidebar 
        sidebar_layout.addSpacing(40)                       # Thêm khoảng trống 40px
        
        # Option các thuật toán 
        sidebar_layout.addWidget(QLabel("THUẬT TOÁN", styleSheet=f"color: {THEME['text_muted']}; font-size: 12px; font-weight: bold;"))
        self.algo_btns = {}
        for id, name in [("EULER FULL GRAPH", "Euler Cycle (Full Graph)"), ("HAMILTON FULL GRAPH", "Hamilton Cycle (Full Graph)"), ("EULER SUBGRAPH", "Euler Cycle (Subgraph)"), ("HAMILTON SUBGRAPH", "Hamilton Cycle (Subgraph)"),  ("TSP", "Traveling Salesman Problem")]:
            algo_option = QPushButton(name)                 # Tạo biến tạm các nút bấm chọn thuật toán
            algo_option.setCheckable(True)                  # Tô màu nút bấm đang chọn 
            algo_option.setStyleSheet("""
                QPushButton {
                    color: white; text-align: left; padding: 12px; 
                    border-radius: 10px; border: none; font-weight: bold; 
                } 
                QPushButton:hover { background: #334155; } 
                QPushButton:checked { background: #4f46e5; }
            """)                                            
            algo_option.clicked.connect(lambda checked, a=id: self.set_algo(a)) # Chỉ được chọn nút bấm, khi chọn thì các nút bấm khác unchecked  
            self.algo_btns[id] = algo_option                                # Lưu trữ các nút bấm
            sidebar_layout.addWidget(self.algo_btns[id])                    # Thêm các nút bấm vào layout sidebar
        self.algo_btns["EULER FULL GRAPH"].setChecked(True)                 # Mặc định mới vào chọn thuật toán tìm chu trình Euler 
        
        # Option đồ thị có hướng / vô hướng 
        sidebar_layout.addSpacing(30)                                       # Thêm khoảng trống 30px 
        sidebar_layout.addWidget(QLabel("CÀI ĐẶT", styleSheet=f"color: {THEME['text_muted']}; font-size: 12px; font-weight: bold;"))
        sidebar_layout.addSpacing(10)
        self.check_dir = QRadioButton("Đồ thị có hướng")                    # Checkbox đồ thị có hướng ? 
        self.check_dir.setStyleSheet(f"color: {THEME['white']};")
        self.check_dir.setAutoExclusive(False)                              # Giá trị độc lập (ko liên quan các checkbox khác)
        self.check_dir.toggled.connect(self.set_directed)                   # Click để set đồ thị có hướng / vô hướng 
        sidebar_layout.addWidget(self.check_dir)                            # Thêm checkbox vào layout sidebar 
        sidebar_layout.addSpacing(10)
        self.check_weight = QRadioButton("Đồ thị có trọng số")              # Checkbox đồ thị có trọng số ?
        self.check_weight.setChecked(True)                                  # Giá trị mặc định True (đồ thị có trọng số)
        self.check_weight.setStyleSheet("color: white;")
        self.check_weight.setAutoExclusive(False)                           # Giá trị độc lập (ko liên quan các checkbox khác)
        self.check_weight.toggled.connect(self.set_weighted)                # Click để set đồ thị có trọng số / không trọng số
        sidebar_layout.addWidget(self.check_weight)
        sidebar_layout.addSpacing(20)
        
        # Option tuỳ chỉnh số node 
        sidebar_layout.addWidget(QLabel("SỐ LƯỢNG NÚT", styleSheet=f"color: {THEME['text_muted']}; font-size: 12px; font-weight: bold;"))
        self.nodes_number_input = QLineEdit("6")                            # Mặc định ban đầu 6 nodes
        self.nodes_number_input.setStyleSheet(f"background: {THEME['text_main']}; color: {THEME['white']}; padding: 8px; border-radius: 8px;")
        self.nodes_number_input.returnPressed.connect(self.update_nodes)    # Ô nhập liệu 
        sidebar_layout.addWidget(self.nodes_number_input)                   # Thêm ô tuỳ chỉnh này vào layout sidebar 
        
        # Option tạo sinh đồ thị
        regen = QPushButton("RE-GENERATE")                  # Nút RE-GENERATE 
        regen.setStyleSheet(f"background: {THEME['indigo']}; color: {THEME['white']}; font-weight: bold; padding: 12px; border-radius: 10px; margin-top: 40px;")
        regen.clicked.connect(self.init_graph)              # Click để tạo sinh đồ thị 
        sidebar_layout.addWidget(regen)                     # Thêm nút bấm vào layout sidebar 
        
        sidebar_layout.addStretch()                         # Chỉnh cho cân đối các nút trong layout sidebar
        layout.addWidget(sidebar)                           # Thêm layout sidebar vào layout chính 
        
        # Màn hình chính ứng dụng
        content = QVBoxLayout()                             # Layout ứng dụng chính 
        header = QFrame()                                   # Layout header 
        header.setFixedHeight(70)                           # Chỉnh header 70px 
        header.setStyleSheet(f"background: {THEME['white']}; border-bottom: 2px solid #e2e8f0;")                
        self.heading_mode = QLabel("Mode: Euler Cycle")     # Mode thuật toán hiện tại. Mặc định là Euler 
        self.heading_mode.setStyleSheet("font-size: 18px; font-weight: bold;"); 
        QHBoxLayout(header).addWidget(self.heading_mode)    # Thêm dòng mode thuật toán vào header 
        content.addWidget(header)                           # Thêm header vào layout ứng dụng chính 
        
        mid = QHBoxLayout()                                 # Layout nội dung chính 
        self.canvas = GraphCanvas()                         # Canvas vẽ đồ thị 
        mid.addWidget(self.canvas, 2)                       # Thêm canvas vào layout nội dung, tỉ lệ co dãn 2
        
        # Bảng biểu bên phải ứng dụng 
        self.table = QTableWidget(0, 0)                     # Layout bảng biểu
        self.table.setFixedWidth(400)                       # Chiều rộng bảng 400px
        self.table.setStyleSheet(f"background: {THEME['white']}; border-left: 2px solid #e2e8f0; font-family: Arial;")
        self.table.setHorizontalHeaderLabels(["Bước", "Đỉnh"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        mid.addWidget(self.table)                           # Thêm bảng biểu vào Layout nội dung chính, tỉ lệ co dãn 1 
        
        content.addLayout(mid)                              # Thêm Layout nội dung chính vào Layout ứng dụng chính
        
        # Thanh mô phỏng bên dưới ứng dụng
        player_panel = QFrame()                             # Khung player panel 
        player_panel.setFixedHeight(150)                    # Chiều cao player panel 150px
        player_panel.setStyleSheet(f"background: {THEME['sidebar']}; margin: 15px; border-radius: 15px;")
        player_layout = QHBoxLayout(player_panel)           # Layout player 
        player_layout.setContentsMargins(30, 0, 30, 0)      # Tạo khoảng xung quanh (margin) layout player 
        player_layout.setSpacing(25)                        

        control_layout = QHBoxLayout()                      # Layout control (3 nút tiến, lùi, chạy mổ phỏng)
        control_layout.setSpacing(10)                       

        self.btn_back = QPushButton("◀")                    # Nút lùi 
        self.btn_back.setFixedSize(40, 40)                  # Kích thước nút 
        self.btn_back.setStyleSheet("color: white; font-size: 18px; border: none;")
        self.btn_back.clicked.connect(self.step_back)       # Bấm nút để lùi 
        control_layout.addWidget(self.btn_back)             # Thêm nút lùi vào layout control 

        self.player_button = QPushButton("▶")               # Nút chạy 
        self.player_button.setFixedSize(50, 50)             # Kích thước nút 
        self.player_button.setStyleSheet("color: white; font-size: 24px; border: none;")
        self.player_button.clicked.connect(self.toggle_play)# Bấm nút để chạy hoặc dừng 
        control_layout.addWidget(self.player_button)        # Thêm nút chạy vào layout control 

        self.btn_next = QPushButton("▶▶")                   # Nút tiến 
        self.btn_next.setFixedSize(40, 40)                  # Kích thước nút 
        self.btn_next.setStyleSheet("color: white; font-size: 18px; border: none;")
        self.btn_next.clicked.connect(self.step_next)       # Bấm nút để tiến 
        control_layout.addWidget(self.btn_next)             # Thêm nút tiến vào layout control 

        player_layout.addLayout(control_layout)             # Thêm layout control vào layout player 
        
        # Thanh tốc độ
        speed_slider_layout = QVBoxLayout()                 # Layout thanh tốc độ 
        speed_slider_layout.setSpacing(8)
        speed_slider_layout.addStretch(1)

        # Layout hàng ngang chứa chữ "TỐC ĐỘ" và Số "5x"
        label_layout = QHBoxLayout()
        
        speed_label = QLabel("TỐC ĐỘ")                      # Tiêu đề cho layout thanh tốc độ 
        speed_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-left: 5px; padding: 5px 0px;")
        label_layout.addWidget(speed_label)                 # Thêm tiêu đề vào layout thanh tốc độ 

        self.speed_value_label = QLabel("5x")               # Số hiển thị tốc độ 
        self.speed_value_label.setStyleSheet(f"color: #bc61b7; font-size: 18px; font-weight: bold; margin-left: 10px; padding: 5px 0px;") # Hạ bớt cỡ chữ xuống 18px cho bằng với chữ TỐC ĐỘ nhìn sẽ đẹp hơn
        label_layout.addWidget(self.speed_value_label)      # Thêm số hiển thị tốc độ vào layout thanh tốc độ 

        label_layout.addStretch(1)  
        speed_slider_layout.addLayout(label_layout)

        # Thanh trượt
        speed_slider = QSlider(Qt.Horizontal)               # Thanh trượt tốc độ      
        speed_slider.setRange(1, 15)                        # Giới hạn tuỳ chỉnh tốc độ trong đoạn [1;15]
        speed_slider.setValue(5)                            # Mặc định tốc độ ban đầu là 5
        
        speed_slider.valueChanged.connect(self.set_speed)   # Trượt là thay đổi giá trị tốc độ mô phỏng 
        
        speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #3a3f54;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #bc61b7;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: none;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        """)

        speed_slider_layout.addWidget(speed_slider)         # Thêm thanh trượt tốc độ vào layout thanh tốc độ
        speed_slider_layout.addStretch(1)                   

        player_layout.addLayout(speed_slider_layout, 10)    # Thêm layout thanh tốc độ vào layout player 
        player_layout.setAlignment(speed_slider_layout, Qt.AlignVCenter) 
        
        # Số bước thực hiện 
        self.step_counter = QLabel("Bước: 0/0")             # Số bước thực hiện 
        self.step_counter.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-left: 50px; margin-right: 10px;")
        player_layout.addWidget(self.step_counter, 0, alignment=Qt.AlignVCenter)
        content.addWidget(player_panel)                     # Thêm khung player panel vào ứng dụng chính 
        
        # Logs kết quả mô phỏng 
        self.logs = QListWidget()                           # Logs kết quả mô phỏng 
        self.logs.setFixedHeight(120)                       # Chiều cao 120px 
        self.logs.setStyleSheet(f"background: #0f172a; color: white; margin: 0 15px 15px 15px; border-radius: 10px; padding: 10px;")
        content.addWidget(self.logs)                        # Thêm logs vào nội dung chính 
        
        layout.addLayout(content)                           # Thêm ứng dụng chính vào bố cục cha  
    
    def add_log(self, description, color="#94a3b8"):
        """Ghi nhật kí vào logs"""
        item = QListWidgetItem(f"[{time.strftime('%H:%M:%S')}] {description}") # Định dạng hiển thị nội dung là "<giờ>:<phút>:<giây>  <nội dung cần hiển thị>"
        item.setForeground(QColor(color))           # Màu của nội dung. Mặc định là #94a3b8
        self.logs.addItem(item)                     # Thêm nội dung vào logs 
        self.logs.scrollToBottom()                  # Luôn theo logs cuối cùng 

    def clear_log(self):
        """Xoá sạch lịch sử logs"""
        self.logs.clear()
        self.add_log("Hệ thống khởi động thành công.", THEME["success"])

    # CÁC HÀM TỐC ĐỘ MÔ PHỎNG 
    def set_speed(self, val):
        """Điều chỉnh tốc độ mô phỏng"""
        self.speed_value_label.setText(f"{val}x")
        self.sim_speed = val
        if self.is_playing: self.timer.setInterval(self.get_interval())

    def step_next(self):
        """Tiến một bước thực thi trong mô phỏng thuật toán"""
        if not self.path: self.solve()
        if (self.path) and (self.sim_step < len(self.path) - 1):
            self.step_counter.setText(f"BƯỚC: {self.sim_step + 1}/{len(self.path)}")
            self.is_playing = False
            self.player_button.setText("▶")
            self.timer.stop()
            self.sim_step += 1
            self.update_ui()

    def step_back(self):
        """Lùi một bước thực thi trong mô phỏng thuật toán"""
        if (self.path) and (self.sim_step > 0):
            self.step_counter.setText(f"BƯỚC: {self.sim_step - 1}/{len(self.path)}")
            self.is_playing = False
            self.player_button.setText("▶")
            self.timer.stop()
            self.sim_step -= 1
            self.update_ui()

    def get_interval(self):
        """Thời gian nghỉ để quy định tốc độ nhanh chậm của mô phỏng"""
        return int(2000 / max(1, self.sim_speed))

    def toggle_play(self):
        """Nút điều khiển chạy / dừng"""
        if not self.path: self.solve()
        has_content = len(self.path) > 0
        if has_content:
            limit = len(self.path)
            if (not self.is_playing) and (self.sim_step >= limit - 1):
                self.sim_step = -1
            self.is_playing = not self.is_playing
            self.player_button.setText("⏸" if self.is_playing else "▶")
            if self.is_playing: self.timer.start(self.get_interval())
            else: self.timer.stop()

    def play_step(self):
        """Mô phỏng chạy đến khi kết thúc"""
        if (self.sim_step < len(self.path) - 1):
            self.sim_step += 1
            self.update_ui()
        else: 
            self.is_playing = False
            self.timer.stop()
            self.player_button.setText("▶")

    # CÁC HÀM KHỞI TẠO CẬP NHẬT KẾT QUẢ MÔ PHỎNG 
    def init_graph(self):
        """Tạo sinh đồ thị"""
        self.nodes = [{
            "id": i, 
            "label": chr(65+i), 
            "pos": [random.randint(100, 500), random.randint(100, 400)]
        } for i in range(self.node_count)]  # Tạo các node toạ độ ngẫu nhiên với số lượng node_count 
        self.edges = []                     # Danh sách cạnh rỗng 
        self.path = []                      # Danh sách đường đi rỗng 
        self.sim_step = -1                  # Reset bước về chưa thực hiện giải thuật 
        self.is_playing = False             # Dừng mô phỏng 
        self.player_button.setText("▶")     # Đổi nút playback
        self.update_adj()                   # Cập nhật ma trận để gán giá trị cạnh 
        self.canvas.set_data(self.nodes, self.edges, self.path, -1, self.is_directed, self.is_weighted)   # Vẽ đồ thị 
        self.table.setRowCount(0)           # Xóa toàn bộ số hàng của bảng tiến trình
        self.table.setColumnCount(0)        # Xóa toàn bộ số cột của bảng tiến trình
        self.clear_log()                    # Reset log 

    def update_adj(self):
        """Cập nhật ma trận kề từ danh sách cạnh"""
        # Tạo ma trận vuông chiều node_count có giá trị inf 
        self.matrix = [[float('inf')]*self.node_count for i in range(self.node_count)]
        # Đường chéo chính của ma trận là 0
        for i in range(self.node_count): self.matrix[i][i] = 0
        # Cập nhật giá trị cho ma trận 
        if not self.edges:                              # Nếu đồ thị chưa có cạnh (danh sách cạnh không tồn tại) thì sinh ngẫu nhiên 
            for i in range(self.node_count):            # Xét ma trận tam giác trên 
                for j in range(i+1, self.node_count):   # bỏ qua đường chéo chính 
                    if random.random() < 0.4:           # Edge[i][j] có xác suất 40% để nhận giá trị (Xác suất để tạo cạnh giữa 2 node bất kì là 40%)
                        weight = random.randint(1, 20) if self.is_weighted else 1       # Độ dài cạnh sinh ngẫu nhiên từ 1 đến 20     
                        self.edges.append({"source": i, "target": j, "weight": weight}) # Gián giá trị cạnh vào danh sách cạnh 
                        self.matrix[i][j] = weight      # Gán giá trị cạnh vào ma trận kề 
                        if not self.is_directed:        # Nếu vô hướng thì giá trị lấy đối xứng qua đường chéo chính
                            self.matrix[j][i] = weight
        else:                                           # Nếu đồ thị đã có các cạnh thì gán cạnh đó 
            for edge in self.edges:                        # Duyệt danh sách cạnh 
                self.matrix[edge['source']][edge['target']] = edge['weight'] if self.is_weighted else 1  # Gán trị cạnh vào ma trận kề 
                if not self.is_directed: self.matrix[edge['target']][edge['source']] = edge['weight']    # Nếu vô hướng thì giá trị lấy đối xứng qua đường chéo chính 

    def update_nodes(self): 
        """Cập nhật số lượng nodes của đồ thị"""
         # Mặc định 6 nodes ban đầu hoặc người dùng nhập không hợp lệ, giới hạn nodes trong đoạn [3;10]
        try: 
            self.node_count = int(self.nodes_number_input.text()) if (3 <= int(self.nodes_number_input.text()) <= 10) else 6
        except: self.node_count = 6
        self.reset_simulation_state()
        self.init_graph()

    def update_ui(self):
        """Cập nhật trạng thái của đồ thị theo bước mô phỏng"""
        self.step_counter.setText(f"BƯỚC: {self.sim_step + 1}/{len(self.path)}")    # Cập nhật số bước mô phỏng 
        self.canvas.set_data(self.nodes, self.edges, self.path, self.sim_step, self.is_directed, self.is_weighted) # Cập nhật dữ liệu đồ thị 
        for row in range(self.table.rowCount()):                                    # Duyệt từng hàng và từng cột 
            for col in range(2):
                item = self.table.item(row, col)                                    # Xét từng ô
                if item:
                    if row == self.sim_step:                                        # Highlight hàng hiện tại 
                        item.setBackground(QColor(THEME["indigo"]))
                        item.setForeground(QColor("white"))
                    else:                                                           # Màu mặc định của các hàng 
                        item.setBackground(QColor("white"))
                        item.setForeground(QColor(THEME["text_main"]))
        self.table.scrollToItem(self.table.item(max(0, self.sim_step), 0))          # Tự động cuộn bảng xuống dưới cùng 

    def set_directed(self, directed): self.is_directed = directed; self.reset_simulation_state()
    
    def set_weighted(self, weighted): 
        self.is_weighted = weighted; self.reset_simulation_state()
        if "TSP" in self.algo_btns:
            if self.is_weighted: self.algo_btns["TSP"].show() # Nếc có trọng số -> Hiển thị nút TSP
            else:                                             # Nếu không có trọng số -> Ẩn nút TEuler
                self.algo_btns["TSP"].hide()                  # Nếu đang chọn TSP mà uncheck thì mặc định về Euler
                if self.algorithm == "TSP":
                    self.set_algo("EULER FULL GRAPH")

    def setup_path_table(self):
        """Tạo kết quả mô phỏng bằng bảng biểu"""
        self.table.setColumnCount(2)
        self.table.setRowCount(len(self.path))
        self.table.setHorizontalHeaderLabels(["Bước", "Đỉnh"])
        for i, nid in enumerate(self.path):
            self.table.setItem(i, 0, QTableWidgetItem(str(i)))
            self.table.setItem(i, 1, QTableWidgetItem(self.nodes[nid]["label"]))

    def reset_simulation_state(self):
        """Reset kết quả cũ và dừng mô phỏng mỗi khi đồ thị thay đổi"""
        self.path = []
        self.sim_step = -1
        self.is_playing = False
        self.timer.stop()
        
        # Cập nhật lại trạng thái nút Play về nút ▶
        if hasattr(self, 'player_button'):
            self.player_button.setText("▶")
            
        # Xóa sạch bảng kết quả bên phải
        if hasattr(self, 'table'):
            self.table.setRowCount(0)
            
        # Ghi log thông báo và vẽ lại màn hình đồ thị mới 
        self.clear_log()
        self.update_ui()

    # HÀM GIẢI THUẬT 
    def solve(self):
        """Hàm chọn thuật toán để giải đồ thị"""
        try:
            self.update_adj()
            if self.algorithm == "EULER FULL GRAPH":
                try:
                    # Tạo ma trận 0 1 với 0: ko có cạnh và 1: có cạnh 
                    matrix_01 = [[1 if self.matrix[i][j] < float('inf') and i != j else 0 for j in range(self.node_count)] for i in range(self.node_count)]
                    is_euler, msg = euler_check(matrix_01, self.is_directed)
                    if is_euler: 
                        any_cycle = fleury(matrix_01, self.is_directed)
                        cycle_str = " -> ".join([self.nodes[nid]["label"] for nid in any_cycle])
                        self.add_log(f"Một chu trình Euler bất kỳ: {cycle_str}")
                        self.path = any_cycle
                        self.setup_path_table()
                    else: 
                        self.path = []
                        self.add_log(f"Không tìm thấy chu trình Euler nào trong đồ thị này, {msg}", THEME["error"])
                except Exception as e: self.add_log(str(e), THEME["error"])
            elif self.algorithm == "HAMILTON FULL GRAPH":
                any_cycle, shortest_path, min_cost  = solve_delivery_problem(self.matrix)
                if (any_cycle):
                    # Format output cho dễ nhìn: 0 -> 1 -> 2 -> 3 -> 0
                    cycle_str = " -> ".join([self.nodes[nid]["label"] for nid in any_cycle])
                    self.add_log(f"Một chu trình Hamilton bất kỳ: {cycle_str}")
                    self.path = any_cycle
                    self.setup_path_table()
                else:
                    self.path = []
                    self.add_log("Không tìm thấy chu trình Hamilton nào trong đồ thị này.", THEME["error"])
            elif self.algorithm == "EULER SUBGRAPH":
                    try:
                        # Tạo ma trận 0 1 với 0: ko có cạnh và 1: có cạnh 
                        matrix_01 = [[1 if self.matrix[i][j] < float('inf') and i != j else 0 for j in range(self.node_count)] for i in range(self.node_count)]
                        is_euler, sub_start = sub_euler_check(matrix_01, self.is_directed)
                        if is_euler and sub_start is None: is_euler = False
                        if is_euler:
                            matrix_copy = [row[:] for row in matrix_01]
                            any_cycle = fleury(matrix_copy, self.is_directed, start=sub_start)
                            cycle_str = " -> ".join([self.nodes[nid]["label"] for nid in any_cycle])
                            self.add_log(f"Một chu trình Euler (Subgraph) bất kỳ: {cycle_str}")
                            self.path = any_cycle
                            self.setup_path_table()
                        else: 
                            self.path = []
                            self.add_log(f"Không tìm thấy chu trình Euler.", THEME["error"])
                    except Exception as e: self.add_log(str(e), THEME["error"])
            elif self.algorithm == "HAMILTON SUBGRAPH":
                any_cycle, shortest_path, min_cost = solve_hamilton_brute(self.matrix)
                if (any_cycle):
                    # Format output cho dễ nhìn: 0 -> 1 -> 2 -> 3 -> 0
                    cycle_str = " -> ".join([self.nodes[nid]["label"] for nid in any_cycle])
                    self.add_log(f"Một chu trình Hamilton bất kỳ: {cycle_str}")
                    self.path = any_cycle
                    self.setup_path_table()
                else:
                    self.path = []
                    self.add_log("Không tìm thấy chu trình Hamilton nào trong đồ thị này.", THEME["error"])
            elif self.algorithm == "TSP":
                any_cycle, shortest_path, min_cost = solve_delivery_problem(self.matrix)
                if shortest_path and min_cost != float('inf'):
                    shortest_str = " -> ".join([self.nodes[nid]["label"] for nid in shortest_path])
                    self.add_log(f"Đường đi giao hàng ngắn nhất (TSP): {shortest_str}", THEME["success"])
                    self.add_log(f"   Tổng chi phí (khoảng cách): {min_cost}", THEME["success"])
                    
                    self.path = shortest_path
                    self.setup_path_table()
                else:
                    self.path = []
                    self.add_log("Không tìm thấy giải pháp cho bài toán TSP (Đồ thị không liên thông hoàn toàn).", THEME["error"])
        except Exception as e: self.add_log(str(e), THEME["error"])

    def set_algo(self, a): 
        """Chọn thuật toán để giải đồ thị"""
        self.reset_simulation_state()
        self.algorithm = a
        self.heading_mode.setText(f"Mode: {a}")
        for k, b in self.algo_btns.items(): b.setChecked(k == a)
    
# Luồng khởi tạo màn hình
class MainWindow(QMainWindow):
    # CÁC HÀM ỨNG DỤNG CHÍNH 
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bài tập lớn Đại số tuyến tính - Lý thuyết đồ thị")     # Tiêu đề cửa sổ 
        self.resize(1240, 850)                                                      # Kích thước cửa sổ
        
        # Stack dùng chuyển đổi 2 màn hình "INTRO" và "APP WIDGET"
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"""
            QStackedWidget {{ 
                background-color: #080818; 
                color: {THEME['white']}
            }}
        """)
        self.setCentralWidget(self.stack)
        
        # Màn hình "INTRO"
        self.intro = IntroScreen()                  # Stack 0 cho IntroScreen 
        self.intro.setObjectName("IntroScreen")
        self.stack.addWidget(self.intro)            # Thêm IntroScreen vào Stack
        
        # Màn hình "APP WIDGET" (ứng dụng chính)
        self.app = AppWidget()                      # Stack 1 cho AppWidget 
        self.app.setObjectName("AppWidget")
        self.app.setStyleSheet(f"background-color: {THEME['white']};")
        self.stack.addWidget(self.app)              # Thêm AppWidget vào Stack 

        # Chức năng nút Start là chuyển đổi sang stack 1 và clear log 
        self.intro.startRequested.connect(lambda: (self.stack.setCurrentIndex(1), self.app.clear_log()))  
        
if __name__ == "__main__":
    qapp = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(qapp.exec_())
