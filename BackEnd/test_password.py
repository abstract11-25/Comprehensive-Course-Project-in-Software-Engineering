"""
密码验证测试脚本
用于诊断密码加密和验证问题
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from auth import get_password_hash, verify_password

def test_password_hashing():
    """测试密码哈希和验证"""
    print("=" * 50)
    print("密码哈希和验证测试")
    print("=" * 50)
    
    test_password = "test123456"
    print(f"\n1. 测试密码: {test_password}")
    
    # 生成哈希
    print("\n2. 生成密码哈希...")
    hashed = get_password_hash(test_password)
    print(f"   哈希值: {hashed}")
    print(f"   哈希长度: {len(hashed)}")
    print(f"   哈希前缀: {hashed[:10]}...")
    
    # 验证密码
    print("\n3. 验证密码...")
    result = verify_password(test_password, hashed)
    print(f"   验证结果: {result}")
    
    if result:
        print("   ✅ 密码验证成功")
    else:
        print("   ❌ 密码验证失败")
    
    # 测试错误密码
    print("\n4. 测试错误密码...")
    wrong_password = "wrongpassword"
    result = verify_password(wrong_password, hashed)
    print(f"   错误密码验证结果: {result}")
    
    if not result:
        print("   ✅ 错误密码正确被拒绝")
    else:
        print("   ❌ 错误密码验证通过（这是错误的！）")
    
    # 测试多次哈希是否一致
    print("\n5. 测试多次哈希的一致性...")
    hashed1 = get_password_hash(test_password)
    hashed2 = get_password_hash(test_password)
    print(f"   第一次哈希: {hashed1[:20]}...")
    print(f"   第二次哈希: {hashed2[:20]}...")
    print(f"   哈希是否相同: {hashed1 == hashed2}")
    print("   (注意: bcrypt 每次生成的哈希都不同，这是正常的)")
    
    # 验证两次哈希都能验证同一个密码
    verify1 = verify_password(test_password, hashed1)
    verify2 = verify_password(test_password, hashed2)
    print(f"   第一次哈希验证: {verify1}")
    print(f"   第二次哈希验证: {verify2}")
    
    if verify1 and verify2:
        print("   ✅ 两次哈希都能正确验证密码")
    else:
        print("   ❌ 哈希验证失败")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    try:
        test_password_hashing()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

