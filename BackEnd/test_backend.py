"""
测试后端服务是否正常运行
"""
import requests
import sys

def test_backend():
    """测试后端服务"""
    base_url = "http://127.0.0.1:8000"
    
    print("测试后端服务连接...")
    print(f"后端地址: {base_url}")
    print()
    
    # 测试根路径
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"[OK] 根路径响应: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 无法连接到后端服务: {e}")
        print("请确保后端服务已启动（运行 start.bat 或 BackEnd/main.py）")
        return False
    
    # 测试注册接口
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"[OK] API 文档可访问: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] API 文档不可访问: {e}")
    
    # 测试注册接口（不发送数据，只测试连接）
    try:
        response = requests.post(
            f"{base_url}/api/auth/register",
            json={"username": "test", "email": "test@test.com", "password": "test123", "role": "user"},
            timeout=5
        )
        # 400 或 201 都表示服务正常（400 可能是因为用户名已存在）
        if response.status_code in [200, 201, 400]:
            print(f"[OK] 注册接口可访问: {response.status_code}")
            if response.status_code == 400:
                print(f"   响应: {response.json().get('detail', '')}")
        else:
            print(f"[WARNING] 注册接口返回异常状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 注册接口无法访问: {e}")
        return False
    
    print()
    print("后端服务测试完成！")
    return True

if __name__ == "__main__":
    success = test_backend()
    sys.exit(0 if success else 1)

