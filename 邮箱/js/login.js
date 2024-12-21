// 表单切换功能
document.querySelectorAll('.tab-btn').forEach(button => {
    button.addEventListener('click', () => {
        // 移除所有按钮的active类
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        // 给当前按钮添加active类
        button.classList.add('active');
        
        // 切换表单显示
        const formType = button.getAttribute('data-form');
        document.querySelectorAll('form').forEach(form => {
            form.classList.remove('form-active');
        });
        document.getElementById(`${formType}Form`).classList.add('form-active');
    });
});

// 密码强度检查
function checkPasswordStrength(password) {
    let strength = 0;
    
    // 检查长度
    if (password.length >= 6) strength++;
    
    // 检查是否包含数字
    if (/\d/.test(password)) strength++;
    
    // 检查是否包含字母
    if (/[a-zA-Z]/.test(password)) strength++;
    
    return strength;
}

// 更新密码强度提示
function updatePasswordStrength(password) {
    const strengthDiv = document.querySelector('.password-strength');
    const strengthText = strengthDiv.querySelector('.strength-text');
    const strength = checkPasswordStrength(password);
    
    strengthDiv.style.display = password ? 'block' : 'none';
    
    // 移除所有强度类
    strengthDiv.classList.remove('strength-1', 'strength-2', 'strength-3');
    
    if (password) {
        strengthDiv.classList.add(`strength-${strength}`);
        switch (strength) {
            case 1:
                strengthText.textContent = '弱';
                break;
            case 2:
                strengthText.textContent = '中';
                break;
            case 3:
                strengthText.textContent = '强';
                break;
            default:
                strengthText.textContent = '非常弱';
        }
    }
}

// 监听密码输入
document.getElementById('registerPassword').addEventListener('input', (e) => {
    updatePasswordStrength(e.target.value);
});

// 登录功能
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // 保存用户信息到本地存储
            localStorage.setItem('userEmail', email);
            localStorage.setItem('isLoggedIn', 'true');
            
            // 跳转到仪表板页面
            window.location.href = 'dashboard.html';
        } else {
            alert(data.error || '登录失败，请检查邮箱和密码');
        }
    } catch (error) {
        console.error('登录错误:', error);
        alert('登录失败，请稍后重试');
    }
});

// 注册功能
document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    // 表单验证
    if (!email || !password || !confirmPassword) {
        showError('请填写所有字段');
        return;
    }

    // 验证邮箱格式
    if (!/@/.test(email) || !/\./.test(email)) {
        showError('请输入有效的邮箱地址');
        return;
    }

    // 验证密码强度
    const strength = checkPasswordStrength(password);
    if (strength < 2) {
        showError('密码强度不足，请按照要求设置密码');
        return;
    }

    // 验证密码一致性
    if (password !== confirmPassword) {
        showError('两次输入的密码不一致');
        return;
    }

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            // 注册成功，自动登录并跳转
            localStorage.setItem('userEmail', email);
            window.location.href = 'dashboard.html';
        } else {
            showError(data.error || '注册失败，请稍后重试');
        }
    } catch (error) {
        console.error('注册错误:', error);
        showError('注册失败，请稍后重试');
    }
});

// 显示错误信息
function showError(message) {
    // 移除已有的错误信息
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // 创建错误信息元素
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <i class="fas fa-exclamation-circle"></i>
        <span>${message}</span>
    `;
    
    // 将错误信息插入到当前活动表单中
    const activeForm = document.querySelector('form.form-active');
    activeForm.insertBefore(errorDiv, activeForm.querySelector('button'));
    
    // 3秒后自动移除错误信息
    setTimeout(() => {
        errorDiv.remove();
    }, 3000);
}

// 输入框焦点效果
document.querySelectorAll('.input-icon input').forEach(input => {
    input.addEventListener('focus', () => {
        input.parentElement.classList.add('focused');
    });
    
    input.addEventListener('blur', () => {
        input.parentElement.classList.remove('focused');
    });
});

// 一键填写功能
document.querySelectorAll('.copy-btn').forEach(button => {
    button.addEventListener('click', () => {
        const email = button.getAttribute('data-email');
        const password = button.getAttribute('data-password');
        
        // 切换到登录表单
        document.querySelector('[data-form="login"]').click();
        
        // 填写表单
        document.getElementById('loginEmail').value = email;
        document.getElementById('loginPassword').value = password;
        
        // 添加动画效果
        button.innerHTML = '<i class="fas fa-check"></i>已填写';
        button.style.background = 'var(--success)';
        
        // 3秒后恢复原样
        setTimeout(() => {
            button.innerHTML = '<i class="fas fa-copy"></i>一键填写';
            button.style.background = '';
        }, 3000);
    });
}); 