import mysql.connector
import hashlib
from config import MYSQL_CONFIG
import jieba
import numpy as np
from predict import predict_label, TfidfVectorizer

def init_db():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    try:
        # 先删除旧表（如果存在的话）
        cursor.execute("DROP TABLE IF EXISTS emails")
        cursor.execute("DROP TABLE IF EXISTS users")
        print("旧表删除成功")

        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("用户表创建成功")

        # 创建邮件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT NOT NULL,
                receiver_id INT NOT NULL,
                subject VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                is_spam BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            )
        """)
        print("邮件表创建成功")

        # 添加测试账户
        test_accounts = [
            {
                'email': 'test1@example.com',
                'password': '123456',
                'is_admin': False
            },
            {
                'email': 'admin@example.com',
                'password': 'admin123',
                'is_admin': True
            },
            {
                'email': 'spammer@example.com',
                'password': '123456',
                'is_admin': False
            }
        ]

        # 存储用户ID映射
        user_ids = {}

        for account in test_accounts:
            # 检查账户是否已存在
            cursor.execute("SELECT id FROM users WHERE email = %s", (account['email'],))
            existing_user = cursor.fetchone()
            
            if not existing_user:
                # 密码加密
                hashed_password = hashlib.md5(account['password'].encode()).hexdigest()
                
                # 插入用户
                cursor.execute("""
                    INSERT INTO users (email, password, is_admin)
                    VALUES (%s, %s, %s)
                """, (account['email'], hashed_password, account['is_admin']))
                user_ids[account['email']] = cursor.lastrowid
                print(f"创建用户成功: {account['email']}")
            else:
                user_ids[account['email']] = existing_user[0]

        # 添加测试邮件
        test_emails = [
            # 正常邮件
            {
                'from': 'admin@example.com',
                'to': 'test1@example.com',
                'subject': '项目进展报告',
                'content': '您好，\n\n这是本周的项目进展报告，请查收。\n\n主要完成了以下工作：\n1. 完成了用户界面设计\n2. 实现了基本功能\n3. 修复了已知bug\n\n请回复确认收到。\n\n谢谢！'
            },
            {
                'from': 'admin@example.com',
                'to': 'test1@example.com',
                'subject': '会议通知',
                'content': '各位同事：\n\n定于明天下午2点在会议室召开项目总结会议，请准时参加。\n\n会议议程：\n1. 项目进展汇报\n2. 问题讨论\n3. 下一步计划\n\n请做好准备。'
            },
            # 垃圾邮件
            {
                'from': 'spammer@example.com',
                'to': 'test1@example.com',
                'subject': '恭喜您中奖了！！！',
                'content': '尊敬的用户：\n\n恭喜您获得了100万大奖！！！\n点击链接立即领取：www.example.com/scam\n错过不再有，快快行动！\n\n请在24小时内领取，否则奖金将作废！'
            },
            {
                'from': 'spammer@example.com',
                'to': 'test1@example.com',
                'subject': '最新优惠活动，仅此一天！',
                'content': '震撼优惠！！\n\n限时特价，全场1折起！\n名牌包包、手表、化妆品应有尽有！\n先到先得，错过就没了！\n\n赶快点击：www.example.com/fake-shop\n\n今天下单还送iPhone 15！'
            },
            {
                'from': 'spammer@example.com',
                'to': 'test1@example.com',
                'subject': '紧急通知：您的账户异常',
                'content': '【紧急】您的账户出现异常！\n\n我们检测到您的账户有异常登录。\n为了您的账户安全，请立即点击以下链接验证身份：\nwww.example.com/verify\n\n若不处理，账户将在24小时内冻结！'
            }
        ]

        # 插入测试邮件
        for email in test_emails:
            # 使用朴素贝叶斯模型预测是否为垃圾邮件
            is_spam = predict_label(email['content']) == '垃圾邮件'
            
            cursor.execute("""
                INSERT INTO emails (sender_id, receiver_id, subject, content, is_spam)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_ids[email['from']],
                user_ids[email['to']],
                email['subject'],
                email['content'],
                is_spam
            ))
            print(f"创建邮件成功: {email['subject']} {'(垃圾邮件)' if is_spam else '(正常邮件)'}")

        conn.commit()
        print("\n数据库初始化成功！")
        print("\n测试账户信息：")
        print("普通用户 - Email: test1@example.com, 密码: 123456")
        print("管理员 - Email: admin@example.com, 密码: admin123")

    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    init_db() 