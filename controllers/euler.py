from collections import deque
import sys

def kiem_tra_lien_thong(matrix):
    start = -1
    for i in range(len(matrix)):
        for j in range(len(matrix)):
            if matrix[i][j]:
                start = i
                break
        if start != -1:
            break

    if start == -1:
        return True  

    visited = [False] * len(matrix)
    q = deque()
    q.append(start)
    visited[start] = True

    while q:
        x = q.popleft()
        for y in range(len(matrix)):
            if (matrix[x][y] or matrix[y][x]) and not visited[y]:
                visited[y] = True
                q.append(y)

    for i in range(len(matrix)):
        co_canh_i = any(matrix[i][j] or matrix[j][i] for j in range(len(matrix)))
        if co_canh_i and not visited[i]:
            return False
    return True

def euler_check(matrix, is_directed):
    if not kiem_tra_lien_thong(matrix):
        return False, "Đồ thị không liên thông (xét các đỉnh có cạnh)"

    if is_directed:
        for i in range(len(matrix)):
            ra = sum(matrix[i][j] for j in range(len(matrix)))
            vao = sum(matrix[j][i] for j in range(len(matrix)))
            if vao != ra:
                return False, f"Đỉnh {chr(65+i)} có bậc vào ({vao}) != bậc ra ({ra})"
    else:
        for i in range(len(matrix)):
            bac = sum(matrix[i])
            if bac % 2 != 0:
                return False, f"Đỉnh {chr(65+i)} có bậc lẻ ({bac})"
        
    return True, "Đồ thị có chu trình Euler"

def sub_euler_check(matrix, is_directed):
    n = len(matrix)
    visited_global = [False] * n  # Đánh dấu các đỉnh đã được xét qua các cụm
    
    # Duyệt qua từng đỉnh để tìm các thành phần liên thông khác nhau
    for start_node in range(n):
        # Nếu đỉnh chưa được duyệt và có ít nhất 1 cạnh nối
        if not visited_global[start_node] and any(matrix[start_node][j] > 0 or matrix[j][start_node] > 0 for j in range(n)):
            # 1. Tìm toàn bộ các đỉnh thuộc thành phần liên thông chứa start_node (Dùng BFS)
            comp_visited = [False] * n
            q = deque([start_node])
            comp_visited[start_node] = True
            
            while q:
                x = q.popleft()
                for y in range(n):
                    if (matrix[x][y] > 0 or matrix[y][x] > 0) and not comp_visited[y]:
                        comp_visited[y] = True
                        q.append(y)
            
            # Đánh dấu vào mảng toàn cục để các vòng lặp sau không trùng cụm này nữa
            for i in range(n):
                if comp_visited[i]:
                    visited_global[i] = True
            
            # Lấy danh sách các đỉnh trong thành phần liên thông này
            nodes_in_comp = [i for i, v in enumerate(comp_visited) if v]
            
            # 2. Kiểm tra điều kiện Euler cho riêng thành phần liên thông này
            is_valid_subgraph = True
            if not is_directed:
                for i in nodes_in_comp:
                    bac = sum(matrix[i])
                    if bac % 2 != 0:
                        is_valid_subgraph = False
                        break
            else:
                for i in nodes_in_comp:
                    ra = sum(matrix[i][j] for j in range(n))
                    vao = sum(matrix[j][i] for j in range(n))
                    if vao != ra:
                        is_valid_subgraph = False
                        break
            
            # Nếu thành phần liên thông này ok thì trả về True và đỉnh xuất phát
            if is_valid_subgraph:
                return True, start_node

    # Nếu đã duyệt qua tất cả các cụm mà không cụm nào đạt yêu cầu
    return False, None

def la_cau(matrix, u, v, is_directed):
    matrix[u][v] -= 1
    if not is_directed:
        matrix[v][u] -= 1

    visited = [False] * len(matrix)
    q = deque()
    q.append(u)
    visited[u] = True
    while q:
        x = q.popleft()
        for y in range(len(matrix)):
            if matrix[x][y] > 0 and not visited[y]:
                visited[y] = True
                q.append(y)

    matrix[u][v] += 1
    if not is_directed:
        matrix[v][u] += 1

    return not visited[v]

def fleury(matrix, is_directed, start=None):
    if start is None:
        start = 0 # Mặc định là 0 nếu đồ thị rỗng
        for i in range(len(matrix)):
            # Nếu đỉnh i có ít nhất 1 cạnh nối ra ngoài, chọn nó làm điểm xuất phát
            if any(matrix[i][j] > 0 for j in range(len(matrix))):
                start = i
                break
    
    cur = start
    path = []
    while True:
        path.append(cur)
        nxt = -1
        for v in range(len(matrix)):
            if matrix[cur][v] <= 0: continue
            if not la_cau(matrix, cur, v, is_directed):
                nxt = v
                break
            elif nxt == -1:
                nxt = v
        if nxt == -1: break
        matrix[cur][nxt] -= 1
        if not is_directed: matrix[nxt][cur] -= 1
        cur = nxt

    return path

