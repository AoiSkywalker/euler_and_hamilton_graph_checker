import itertools
import math

def solve_hamilton_brute(matrix):
    """
    Tìm chu trình Hamilton lớn nhất (số đỉnh nhiều nhất) trong bất kỳ đồ thị con nào.
    Trả về: (shortest_path, min_cost, hamilton_cycle)
    """
    if len(matrix) == 0:
        return None, 0, None

    best_cycle = None
    best_cost = float('inf')
    max_nodes = 0

    def find_cycles(current_node, start_node, visited, path, current_cost, target_size):
        nonlocal best_cycle, best_cost, max_nodes
        
        if len(path) == target_size:
            # Check if we can return to start_node
            if matrix[current_node][start_node] < float('inf') and (matrix[current_node][start_node] > 0 or current_node == start_node):
                cycle = path + [start_node]
                total_cost = current_cost + matrix[current_node][start_node]
                
                # We found a cycle of target_size
                if target_size > max_nodes:
                    max_nodes = target_size
                    best_cycle = cycle
                    best_cost = total_cost
                elif target_size == max_nodes:
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_cycle = cycle
                return True
            return False

        found = False
        for nxt in range(len(matrix)):
            if not visited[nxt] and matrix[current_node][nxt] < float('inf') and (matrix[current_node][nxt] > 0 or current_node == nxt):
                visited[nxt] = True
                if find_cycles(nxt, start_node, visited, path + [nxt], current_cost + matrix[current_node][nxt], target_size):
                    found = True
                    # Nếu đã tìm thấy một chu trình kích thước này, ta có thể dừng (hoặc tiếp tục để tìm cái rẻ nhất)
                    # Ở đây ta tiếp tục để tìm min_cost cho TSP
                visited[nxt] = False
        return found

    # Thử từ kích thước lớn nhất về 3
    for size in range(len(matrix), 2, -1):
        for start in range(len(matrix)):
            v = [False] * len(matrix)
            v[start] = True
            if find_cycles(start, start, v, [start], 0, size):
                # Vì ta đi từ size lớn nhất xuống, nếu tìm thấy bất kỳ cái nào ở size này, 
                # đó chính là thành phần/đồ thị con lớn nhất thoả mãn.
                return best_cycle, best_cost, best_cycle

    return None, 0, None
