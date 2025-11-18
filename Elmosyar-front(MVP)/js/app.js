// Main application controller
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication status
    checkAuth();
    
    // Load initial page based on URL hash
    const hash = window.location.hash || '#home';
    const pageName = hash.substring(1).split('?')[0];
    showPage(pageName);
    
    // Handle browser back/forward
    window.addEventListener('hashchange', function() {
        const page = window.location.hash.substring(1).split('?')[0];
        showPage(page);
    });
});

function showPage(pageName) {
    // Default to home if empty
    if (!pageName || pageName === '') {
        pageName = 'home';
    }
    
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Show loading
    showLoading();
    
    // Load the requested page
    setTimeout(() => {
        loadPageContent(pageName);
    }, 100);
}

async function loadPageContent(pageName) {
    try {
        const response = await fetch(`pages/${pageName}.html`);
        
        if (!response.ok) {
            throw new Error('Page not found');
        }
        
        const html = await response.text();
        document.getElementById('main-content').innerHTML = html;
        
        // Initialize page-specific functionality
        await initializePage(pageName);
        
        // Update URL hash without triggering hashchange
        const currentHash = window.location.hash.substring(1).split('?')[0];
        if (currentHash !== pageName) {
            // Preserve query parameters if any
            const queryString = window.location.hash.includes('?') 
                ? '?' + window.location.hash.split('?')[1] 
                : '';
            window.history.pushState(null, '', `#${pageName}${queryString}`);
        }
        
    } catch (error) {
        console.error('Error loading page:', error);
        document.getElementById('main-content').innerHTML = `
            <div class="card">
                <h2>خطا در بارگذاری صفحه</h2>
                <p>صفحه مورد نظر یافت نشد.</p>
                <button class="btn btn-primary" onclick="showPage('home')">بازگشت به خانه</button>
            </div>
        `;
    } finally {
        hideLoading();
    }
}

async function initializePage(pageName) {
    // First handle URL parameters
    handleUrlParameters(pageName);
    
    // Then setup event listeners
    switch (pageName) {
        case 'home':
            if (currentUser) {
                await loadPosts('home-posts', '/api/posts/');
            } else {
                const homePostsContainer = document.getElementById('home-posts');
                if (homePostsContainer) {
                    homePostsContainer.innerHTML = `
                        <div class="card">
                            <p style="text-align: center; color: #657786;">
                                لطفا برای مشاهده پست‌ها 
                                <a href="#login" onclick="showPage('login')">وارد شوید</a>
                            </p>
                        </div>
                    `;
                }
            }
            break;
            
        case 'login':
            const loginForm = document.getElementById('login-form');
            if (loginForm) {
                loginForm.addEventListener('submit', handleLogin);
            }
            break;
            
        case 'signup':
            const signupForm = document.getElementById('signup-form');
            if (signupForm) {
                signupForm.addEventListener('submit', handleSignup);
            }
            break;
            
        case 'forgot-password':
            const forgotForm = document.getElementById('forgot-password-form');
            if (forgotForm) {
                forgotForm.addEventListener('submit', handleForgotPassword);
            }
            break;
            
        case 'reset-password':
            const resetForm = document.getElementById('reset-password-form');
            if (resetForm) {
                resetForm.addEventListener('submit', handleResetPassword);
            }
            break;
            
        case 'profile':
            // URL parameters are handled in handleUrlParameters
            break;
            
        case 'create-post':
            if (currentUser) {
                const postForm = document.getElementById('post-form');
                if (postForm) {
                    postForm.addEventListener('submit', handleCreatePost);
                }
            } else {
                showMessage('لطفا ابتدا وارد شوید', 'error');
                showPage('login');
            }
            break;
            
        case 'explore':
            const roomSearchForm = document.getElementById('room-search-form');
            if (roomSearchForm) {
                roomSearchForm.addEventListener('submit', handleRoomSearch);
            }
            break;
            
        case 'search':
            const userSearchForm = document.getElementById('user-search-form');
            if (userSearchForm) {
                userSearchForm.addEventListener('submit', handleUserSearch);
            }
            break;
            
        case 'post-detail':
        case 'user-posts':
            // Already handled by their respective functions
            break;
    }
}

function handleUrlParameters(pageName) {
    const urlParams = new URLSearchParams(window.location.hash.split('?')[1]);
    
    switch (pageName) {
        case 'profile':
            const user = urlParams.get('user');
            if (user) {
                loadUserProfile(decodeURIComponent(user));
            } else if (currentUser) {
                loadUserProfile(currentUser.username);
            } else {
                showMessage('لطفا ابتدا وارد شوید', 'error');
                showPage('login');
            }
            break;
            
        case 'explore':
            const room = urlParams.get('room');
            if (room) {
                showRoom(decodeURIComponent(room));
            }
            break;
            
        case 'reset-password':
            const token = urlParams.get('token');
            const resetForm = document.getElementById('reset-password-form');
            if (token && resetForm) {
                resetForm.dataset.token = token;
            } else if (!token) {
                showMessage('لینک بازیابی معتبر نیست', 'error');
                showPage('login');
            }
            break;
    }
}

// Form handlers
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const remember = document.getElementById('login-remember') ? document.getElementById('login-remember').checked : false;
    
    await login(email, password, remember);
}

async function handleSignup(e) {
    e.preventDefault();
    const username = document.getElementById('signup-username').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const passwordConfirm = document.getElementById('signup-confirm-password').value;
    
    if (password !== passwordConfirm) {
        showMessage('رمز عبور و تکرار آن مطابقت ندارند', 'error');
        return;
    }
    
    await signup(username, email, password, passwordConfirm);
}

async function handleForgotPassword(e) {
    e.preventDefault();
    const email = document.getElementById('reset-email').value;
    
    if (!email) {
        showMessage('لطفا ایمیل خود را وارد کنید', 'error');
        return;
    }
    
    await requestPasswordReset(email);
}

async function handleResetPassword(e) {
    e.preventDefault();
    
    const password = document.getElementById('new-password').value;
    const passwordConfirm = document.getElementById('confirm-password').value;
    const token = document.getElementById('reset-password-form').dataset.token;
    
    if (!token) {
        showMessage('لینک بازیابی معتبر نیست', 'error');
        return;
    }
    
    if (password !== passwordConfirm) {
        showMessage('رمز عبور و تکرار آن مطابقت ندارند', 'error');
        return;
    }
    
    if (password.length < 8) {
        showMessage('رمز عبور باید حداقل ۸ کاراکتر باشد', 'error');
        return;
    }
    
    await resetPassword(token, password, passwordConfirm);
}

async function handleCreatePost(e) {
    e.preventDefault();
    
    const content = document.getElementById('post-content').value;
    const category = document.getElementById('post-category').value;
    const tags = document.getElementById('post-tags').value;
    const mentions = document.getElementById('post-mentions').value;
    const mediaInput = document.getElementById('post-media');
    
    if (!content.trim() && (!mediaInput.files || mediaInput.files.length === 0)) {
        showMessage('لطفا محتوا یا فایل رسانه‌ای وارد کنید', 'error');
        return;
    }
    
    if (!category.trim()) {
        showMessage('نام اتاق الزامی است', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('content', content);
    formData.append('category', category);
    formData.append('tags', tags);
    formData.append('mentions', mentions);
    
    if (mediaInput.files) {
        for (let file of mediaInput.files) {
            formData.append('media', file);
        }
    }
    
    const success = await createPost(formData);
    if (success) {
        showPage('home');
    }
}

function handleRoomSearch(e) {
    e.preventDefault();
    const roomName = document.getElementById('room-name').value.trim();
    if (roomName) {
        showRoom(roomName);
    } else {
        showMessage('لطفا نام اتاق را وارد کنید', 'error');
    }
}

function handleUserSearch(e) {
    e.preventDefault();
    const username = document.getElementById('search-username').value.trim();
    if (username) {
        searchUsers(username);
    } else {
        showMessage('لطفا نام کاربری را وارد کنید', 'error');
    }
}

// Global functions for HTML onclick
window.showPage = showPage;
window.loadPageContent = loadPageContent;
window.showUserProfile = loadUserProfile;
window.showUserPosts = showUserPosts;
window.showRoom = showRoom;
window.logout = logout;
window.likePost = likePost;
window.showPostDetail = showPostDetail;
window.searchUsers = searchUsers;