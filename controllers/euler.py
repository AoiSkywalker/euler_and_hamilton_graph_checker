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


def euler_check(matrix, vo_huong):
    if not kiem_tra_lien_thong(matrix):
        return False, "Đồ thị không liên thông (xét các đỉnh có cạnh)"

    if vo_huong:
        for i in range(len(matrix)):
            bac = sum(matrix[i])
            if bac % 2 != 0:
                return False, f"Đỉnh {chr(65+i)} có bậc lẻ ({bac})"
    else:
        for i in range(len(matrix)):
            ra = sum(matrix[i][j] for j in range(len(matrix)))
            vao = sum(matrix[j][i] for j in range(len(matrix)))
            if vao != ra:
                return False, f"Đỉnh {chr(65+i)} có bậc vào ({vao}) != bậc ra ({ra})"
    return True, "Đồ thị có chu trình Euler"

def la_cau(matrix, u, v, vo_huong):
    matrix[u][v] -= 1
    if vo_huong:
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
    if vo_huong:
        matrix[v][u] += 1

    return not visited[v]


def fleury(matrix, vo_huong, start=None):
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
            if not la_cau(matrix, cur, v, vo_huong):
                nxt = v
                break
            elif nxt == -1:
                nxt = v
        if nxt == -1: break
        matrix[cur][nxt] -= 1
        if vo_huong: matrix[nxt][cur] -= 1
        cur = nxt

    return path


def hierholzer(start, matrix):
    st = [start]
    ec = []

    while st:
        x = st[-1]
        tim_thay = False
        for i in range(len(matrix)):
            if matrix[x][i] > 0:
                matrix[x][i] -= 1
                matrix[i][x] -= 1
                st.append(i)
                tim_thay = True
                break
        if not tim_thay:
            st.pop()
            ec.append(x)

    return ec


def hierholzer_ad(start):

    st = [start]
    ec = []

    while st:
        x = st[-1]
        tim_thay = False
        for i in range(len(matrix)):
            if matrix[x][i] > 0:
                matrix[x][i] -= 1
                st.append(i)
                tim_thay = True
                break
        if not tim_thay:
            st.pop()
            ec.append(x)

    return ec