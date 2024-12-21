// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 显示用户邮箱
    const userEmail = localStorage.getItem('userEmail');
    if (!userEmail) {
        window.location.href = 'index.html';
        return;
    }
    document.getElementById('userEmail').textContent = userEmail;

    // 初始化变量
    let currentFolder = 'inbox';
    let currentEmailId = null;

    // 导航切换
    document.querySelectorAll('.nav-links li').forEach(item => {
        item.addEventListener('click', function() {
            // 更新激活状态
            document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
            this.classList.add('active');

            // 更新当前文件夹
            currentFolder = this.getAttribute('data-folder');
            document.querySelector('.email-list-header h2').textContent = this.textContent.trim();

            // 加载邮件列表
            loadEmails(currentFolder);
        });
    });

    // 加载邮件列表
    async function loadEmails(folder = 'inbox') {
        try {
            // 根据文件夹类型选择不同的API端点
            let endpoint;
            switch (folder) {
                case 'sent':
                    endpoint = '/api/sent';
                    break;
                case 'spam':
                    endpoint = '/api/spam';
                    break;
                default:
                    endpoint = '/api/inbox';
            }

            const response = await fetch(endpoint, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = 'index.html';
                    return;
                }
                throw new Error('Failed to load emails');
            }

            const data = await response.json();
            const emailList = document.getElementById('emailList');
            emailList.innerHTML = '';

            if (data.emails.length === 0) {
                emailList.innerHTML = `<div class="no-emails">暂无${folder === 'spam' ? '垃圾' : ''}邮件</div>`;
                return;
            }

            data.emails.forEach(email => {
                const emailItem = document.createElement('div');
                emailItem.className = 'email-item';
                emailItem.dataset.emailId = email.id;
                
                // 根据文件夹类型显示不同的信息
                let contactInfo;
                if (folder === 'sent') {
                    contactInfo = `发送至：${email.receiver_email}`;
                } else {
                    contactInfo = `来自：${email.sender_email}`;
                    if (folder === 'spam') {
                        emailItem.classList.add('spam');
                    }
                }
                
                emailItem.innerHTML = `
                    <div class="email-header">
                        <span class="contact">${contactInfo}</span>
                        <span class="date">${formatDate(email.created_at)}</span>
                    </div>
                    <div class="subject">
                        ${folder === 'spam' ? '<i class="ri-spam-2-line"></i>' : ''}
                        ${email.subject}
                    </div>
                    <div class="preview">${email.content.substring(0, 100)}...</div>
                `;

                emailItem.addEventListener('click', () => loadEmailContent(email.id));
                emailList.appendChild(emailItem);
            });

            // 更新文件夹标题
            const folderTitle = document.querySelector('.email-list-header h2');
            switch (folder) {
                case 'sent':
                    folderTitle.textContent = '已发送';
                    break;
                case 'spam':
                    folderTitle.textContent = '垃圾邮件';
                    break;
                default:
                    folderTitle.textContent = '收件箱';
            }
            
            // 更新导航栏选中状态
            document.querySelectorAll('.nav-links li').forEach(li => {
                li.classList.toggle('active', li.dataset.folder === folder);
            });
            
            // 保存当前文件夹
            currentFolder = folder;
        } catch (error) {
            console.error('Error loading emails:', error);
            showNotification('加载邮件失败，请稍后重试', 'error');
        }
    }

    // 加载邮件内容
    async function loadEmailContent(emailId) {
        try {
            const response = await fetch(`/api/email/${emailId}`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = 'index.html';
                    return;
                }
                throw new Error('Failed to load email content');
            }
            
            const email = await response.json();
            displayEmailContent(email);
            
            // 更新选中状态
            document.querySelectorAll('.email-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector(`[data-email-id="${emailId}"]`)?.classList.add('active');
            
            currentEmailId = emailId;
        } catch (error) {
            console.error('Error loading email content:', error);
            showNotification('加载邮件内容失败，请稍后重试', 'error');
        }
    }

    // 显示邮件内容
    function displayEmailContent(email) {
        const content = document.getElementById('emailContent');
        const isSentEmail = email.sender_id === parseInt(localStorage.getItem('userId'));
        
        // 确定显示的联系人信息
        const contactInfo = isSentEmail ? 
            { label: '收件人：', email: email.receiver_email } :
            { label: '发件人：', email: email.sender_email };
        
        content.innerHTML = `
            <div class="email-content-header">
                <h1 class="subject">${email.subject}</h1>
                <div class="email-meta">
                    <div class="contact-info">
                        <span class="label">${contactInfo.label}</span>
                        <span class="email">${contactInfo.email}</span>
                    </div>
                    <div class="date">${formatDate(email.date, true)}</div>
                </div>
            </div>
            <div class="email-content-body">
                ${email.content.split('\n').map(line => `<p>${line}</p>`).join('')}
            </div>
        `;
    }

    // 获取用户列表并填充下拉框
    async function loadUserList() {
        try {
            const response = await fetch('/api/users');
            if (!response.ok) {
                throw new Error('获取用户列表失败');
            }
            const users = await response.json();
            
            const select = document.getElementById('recipientEmail');
            select.innerHTML = '<option value="">选择收件人</option>';
            
            users.forEach(user => {
                // 不显示当前用户
                const currentUserEmail = localStorage.getItem('userEmail');
                if (user.email && user.email !== currentUserEmail) {
                    const option = document.createElement('option');
                    option.value = user.email;
                    option.textContent = user.email;
                    select.appendChild(option);
                }
            });
        } catch (error) {
            console.error('获取用户列表失败:', error);
            alert('获取用户列表失败，请刷新页面重试');
        }
    }

    // 写邮件相关
    const composeBtn = document.getElementById('composeBtn');
    const composeModal = document.getElementById('composeModal');
    const cancelComposeBtn = document.getElementById('cancelCompose');
    const composeForm = document.getElementById('composeForm');

    // 打开写邮件窗口
    composeBtn.addEventListener('click', () => {
        composeModal.style.display = 'block';
        loadUserList(); // 加载用户列表
    });

    // 关闭写邮件窗口
    cancelComposeBtn.addEventListener('click', () => {
        composeModal.style.display = 'none';
        composeForm.reset();
    });

    // 点击模态框外部关闭
    composeModal.addEventListener('click', (e) => {
        if (e.target === composeModal) {
            composeModal.style.display = 'none';
            composeForm.reset();
        }
    });

    // 发送邮件
    composeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const recipientEmail = document.getElementById('recipientEmail').value;
        const subject = document.getElementById('emailSubject').value;
        const content = document.getElementById('emailBody').value;
        
        if (!recipientEmail || !subject || !content) {
            alert('请填写所有必填字段');
            return;
        }
        
        try {
            const response = await fetch('/api/send_email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    to: recipientEmail,
                    subject: subject,
                    content: content
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                alert('邮件发送成功！');
                composeModal.style.display = 'none';
                composeForm.reset();
                
                // 如果当前在已发送文件夹，刷新列表
                if (currentFolder === 'sent') {
                    loadEmails('sent');
                }
            } else {
                if (response.status === 401) {
                    // 如果未登录，重定向到登录页面
                    alert('登录已过期，请重新登录');
                    window.location.href = 'index.html';
                    return;
                }
                alert(result.error || '发送失败，请稍后重试');
            }
        } catch (error) {
            console.error('发送邮件失败:', error);
            alert('发送失败，请稍后重试');
        }
    });

    // 通知提示
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        `;

        document.body.appendChild(notification);

        // 3秒后自动消失
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // 日期格式化
    function formatDate(dateStr, full = false) {
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now - date;
        const oneDay = 24 * 60 * 60 * 1000;

        if (!full) {
            if (diff < oneDay) {
                return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            }
            if (diff < 7 * oneDay) {
                const days = ['日', '一', '二', '三', '四', '五', '六'];
                return `周${days[date.getDay()]}`;
            }
            return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
        }

        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // 初始加载收件箱
    loadEmails('inbox');

    // 退出登录功能
    document.getElementById('logoutBtn').addEventListener('click', async function() {
        try {
            // 清除本地存储的用户信息
            localStorage.removeItem('userEmail');
            
            // 发送退出登录请求到服务器
            const response = await fetch('/api/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Logout failed');
            }

            // 重定向到登录页面
            window.location.href = 'index.html';
        } catch (error) {
            console.error('Logout error:', error);
            showNotification('退出登录失败，请重试', 'error');
        }
    });
}); 