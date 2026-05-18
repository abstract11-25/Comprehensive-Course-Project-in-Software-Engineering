"""
测试登录功能
"""
import requests
import json

# 测试登录接口
def test_login():
    base_url = "http://127.0.0.1:8000"
    
    print("=" * 60)
    print("登录功能测试")
    print("=" * 60)
    
    # 1. 测试后端服务是否运行
    print("\n[1] 检查后端服务...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✓ 后端服务正常运行")
        else:
            print(f"✗ 后端服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到后端服务 (http://127.0.0.1:8000)")
        print("  请确保后端服务已启动:")
        print("  cd BackEnd")
        print("  .venv\\Scripts\\activate")
        print("  uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"✗ 连接错误: {e}")
        return False
    
    # 2. 测试登录接口
    print("\n[2] 测试登录接口...")
    login_url = f"{base_url}/api/auth/login"
    
    # 使用测试账号（如果存在）
    test_username = input("\n请输入用户名（或按Enter跳过）: ").strip()
    if not test_username:
        print("跳过登录测试")
        return True
    
    test_password = input("请输入密码: ").strip()
    
    try:
        # 使用FormData格式（OAuth2PasswordRequestForm要求）
        form_data = {
            'username': test_username,
            'password': test_password
        }
        
        response = requests.post(login_url, data=form_data, timeout=10)
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ 登录成功!")
            print(f"  Token: {data.get('access_token', '')[:50]}...")
            print(f"  用户信息: {json.dumps(data.get('user', {}), indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"✗ 登录失败")
            print(f"  响应内容: {response.text}")
            try:
                error_data = response.json()
                print(f"  错误详情: {error_data.get('detail', '未知错误')}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

if __name__ == "__main__":
    test_login()

