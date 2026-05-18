import itertools
import math
from collections import deque

def solve_delivery_problem(matrix):
    """
    Tìm một chu trình Hamilton và đường đi ngắn nhất (TSP).
    Thuật toán: Sinh hoán vị (Brute-force)
    Độ phức tạp: O(N!)
    Trả về : (any_hamiltonian_cycle, shortest_path, min_cost)
    """
    if len(matrix) == 0: return None, None, 0

    # Các đỉnh cần giao hàng (trừ điểm xuất phát là đỉnh 0)
    vertices = list(range(1, len(matrix)))
    any_hamiltonian_cycle = None
    shortest_path = None
    min_cost = math.inf

    # Sinh tất cả các hoán vị của các điểm cần giao hàng
    for perm in itertools.permutations(vertices):
        # Tạo chu trình: Bắt đầu từ 0 -> đi qua các điểm -> quay về 0
        current_path = [0] + list(perm) + [0]
        current_cost = 0
        is_valid_cycle = True
        # Tính tổng chi phí cho chu trình hiện tại
        for i in range(len(current_path) - 1):
            u = current_path[i]
            v = current_path[i + 1]

            if matrix[u][v] == math.inf or matrix[u][v] == 0 and u != v:
                is_valid_cycle = False  # Không có đường đi
                break
            current_cost += matrix[u][v]
        # Nếu là một chu trình hợp lệ (chu trình Hamilton)
        if is_valid_cycle:
            # Lưu lại chu trình đầu tiên tìm thấy
            if any_hamiltonian_cycle is None:
                any_hamiltonian_cycle = current_path.copy()
            # Cập nhật đường đi ngắn nhất
            if current_cost < min_cost:
                min_cost = current_cost
                shortest_path = current_path.copy()
    return any_hamiltonian_cycle, shortest_path, min_cost

def solve_hamilton_brute(matrix):
    """
    Tìm chu trình Hamilton đi qua HẾT TẤT CẢ các đỉnh của một thành phần liên thông.
    Nếu cụm liên thông đó không đi hết các đỉnh, loại bỏ và tìm cụm khác.
    Trả về: (any_hamiltonian_cycle, shortest_path, min_cost)
    """
    n = len(matrix)
    if n == 0: return None, None, 0

    # Phân tách đồ thị thành các thành phần liên thông  
    visited_global = [False] * n
    components = [] # Lưu danh sách các cụm, mỗi cụm là một list chứa các ID đỉnh

    for start_node in range(n):
        # Nếu đỉnh chưa được duyệt và có ít nhất 1 cạnh nối
        has_edges = any(matrix[start_node][j] < float('inf') and start_node != j for j in range(n)) or \
                    any(matrix[j][start_node] < float('inf') and start_node != j for j in range(n))
        
        if not visited_global[start_node] and has_edges:
            comp_visited = [False] * n
            q = deque([start_node])
            comp_visited[start_node] = True
            
            while q:
                x = q.popleft()
                for y in range(n):
                    if (matrix[x][y] < float('inf') or matrix[y][x] < float('inf')) and x != y:
                        if not comp_visited[y]:
                            comp_visited[y] = True
                            q.append(y)
            
            # Đánh dấu vào mảng toàn cục để các vòng lặp sau không trùng cụm này nữa
            nodes_in_comp = []
            for i in range(n):
                if comp_visited[i]:
                    visited_global[i] = True
                    nodes_in_comp.append(i)
            
            # Chỉ xét các thành phần liên thông có từ 3 đỉnh trở lên (mới tạo thành chu trình)
            if len(nodes_in_comp) >= 3:
                components.append(nodes_in_comp)

    # Tìm chu trình Hamilton trong từng cụm
    best_cycle = None
    best_cost = float('inf')

    # Duyệt qua từng thành phần liên thông để tìm chu trình thỏa mãn
    for comp in components:
        k = len(comp) # Số đỉnh trong thành phần liên thông hiện tại
        
        # Tạo một ma trận kề thu nhỏ kích thước (k x k) dành riêng cho cụm này
        sub_matrix = [[float('inf')] * k for _ in range(k)]
        for i in range(k): sub_matrix[i][i] = 0
            
        # Ánh xạ trọng số từ ma trận gốc sang ma trận thu nhỏ
        for i in range(k):
            for j in range(k):
                if i != j:
                    orig_u = comp[i]
                    orig_v = comp[j]
                    sub_matrix[i][j] = matrix[orig_u][orig_v]

        # Kiểm tra điều kiện chu trình Hamilton
        any_ham, short_path, cost = solve_delivery_problem(sub_matrix)

        # Nếu tìm thấy chu trình Hamilton hợp lệ đi qua hết cụm
        if short_path and cost != math.inf:
            real_path = [comp[local_id] for local_id in short_path]
            return real_path, real_path, cost

    return None, None, 0

  