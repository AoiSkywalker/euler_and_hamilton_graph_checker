import itertools
import math

def solve_delivery_problem(matrix):
    """
    Tìm một chu trình Hamilton và đường đi ngắn nhất (TSP).
    Thuật toán: Sinh hoán vị (Brute-force)
    Độ phức tạp: O(N!)
    """
    n = len(matrix)
    if n == 0:
        return None, None, 0

    # Các đỉnh cần giao hàng (trừ điểm xuất phát là đỉnh 0)
    vertices = list(range(1, n))

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
