from collections import deque

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

def solve_euler_check(matrix, is_directed, start_node=None):
    # Nếu không có start_node được chỉ định, tìm node đầu tiên có cạnh
    if start_node is None:
        for i in range(len(matrix)):
            if any(matrix[i][j] > 0 or matrix[j][i] > 0 for j in range(len(matrix))):
                start_node = i
                break
    
    if start_node is None:
        return False, "Đồ thị không có cạnh"

    # Kiểm tra tính liên thông của thành phần chứa start_node
    visited = [False] * len(matrix)
    q = deque([start_node])
    visited[start_node] = True
    while q:
        x = q.popleft()
        for y in range(len(matrix)):
            if (matrix[x][y] > 0 or matrix[y][x] > 0) and not visited[y]:
                visited[y] = True
                q.append(y)
    
    # Kiểm tra xem có cạnh nào nằm ngoài thành phần liên thông này không
    for i in range(len(matrix)):
        for j in range(len(matrix)):
            if matrix[i][j] > 0:
                if not visited[i] or not visited[j]:
                    # Có cạnh ở thành phần khác, nhưng ta chỉ xét thành phần chứa start_node
                    pass 

    # Kiểm tra bậc trong thành phần liên thông chứa start_node
    nodes_in_comp = [i for i, v in enumerate(visited) if v]
    
    if not is_directed:
        for i in nodes_in_comp:
            bac = sum(matrix[i])
            if bac % 2 != 0:
                return False, f"Thành phần chứa {chr(65+i)} không thoả Euler (bậc lẻ)"
    else:
        for i in nodes_in_comp:
            ra = sum(matrix[i][j] for j in range(len(matrix)))
            vao = sum(matrix[j][i] for j in range(len(matrix)))
            if vao != ra:
                return False, f"Thành phần chứa {chr(65+i)} không thoả Euler (vao != ra)"
    
    return True, "Thành phần liên thông có chu trình Euler"

def la_cau(matrix, u, v, is_directed):
    # Thử tạm thời xóa cạnh
    matrix[u][v] -= 1
    if not is_directed:
        matrix[v][u] -= 1

    visited = [False] * len(matrix)
    q = deque([u])
    visited[u] = True
    while q:
        x = q.popleft()
        for y in range(len(matrix)):
            if matrix[x][y] > 0 and not visited[y]:
                visited[y] = True
                q.append(y)

    # Hoàn trả lại cạnh
    matrix[u][v] += 1
    if not is_directed:
        matrix[v][u] += 1

    return not visited[v]

def solve_fleury(matrix, is_directed):
    """
    Tìm chu trình Euler NGẮN NHẤT (ít cạnh nhất) có thể trong đồ thị con.
    """
    best_path = []
    min_len = float('inf')
    
    def backtrack(curr, path, matrix):
        nonlocal best_path, min_len
        
        # Nếu đã tạo thành vòng khép kín và có ít nhất 3 cạnh (độ dài mảng > 3: ví dụ A-B-C-A)
        if len(path) > 3 and curr == path[0]:
            if len(path) < min_len:
                min_len = len(path)
                best_path = path[:]
            return # Đã đóng vòng rồi thì dừng nhánh này lại, không đi lan man nữa
            
        # Cắt tỉa (Pruning): Nếu đường đi đang xét đã dài bằng min_len hiện tại thì bỏ qua luôn
        if len(path) >= min_len:
            return
            
        # Duyệt các cạnh kề
        for nxt in range(len(matrix)):
            if matrix[curr][nxt] > 0:
                # Thử đi qua cạnh này
                matrix[curr][nxt] -= 1
                if not is_directed:
                    matrix[nxt][curr] -= 1
                
                path.append(nxt)
                backtrack(nxt, path, matrix)
                path.pop()
                
                # Hoàn trả cạnh
                matrix[curr][nxt] += 1
                if not is_directed:
                    matrix[nxt][curr] += 1

    # Thử bắt đầu từ mọi node
    for start_node in range(len(matrix)):
        mtk = [row[:] for row in matrix]
        backtrack(start_node, [start_node], mtk)

    if not best_path:
        return [], []
    
    # Tạo notes tương ứng
    notes = ["Bắt đầu"]
    mtk = [row[:] for row in matrix]
    for i in range(len(best_path) - 1):
        u, v = best_path[i], best_path[i+1]
        is_bridge = la_cau(mtk, u, v, is_directed) 
        notes.append("Cầu" if is_bridge else "Không phải cầu")
        mtk[u][v] -= 1
        if not is_directed:
            mtk[v][u] -= 1
    
    return best_path, notes
