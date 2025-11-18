// Profile functionality
async function loadUserProfile(username) {
    showLoading();
    try {
        // First get user info
        const userResponse = await fetch(`${API_BASE}/api/users/${encodeURIComponent(username)}/posts/`, {
            credentials: 'include'
        });
        const userData = await userResponse.json();
        
        if (userData.success) {
            // Update profile header
            const profileHeader = document.getElementById('profile-header');
            if (profileHeader) {
                const user = {
                    username: userData.username,
                    first_name: '',
                    last_name: '',
                    bio: '',
                    profile_picture: null
                };
                
                // Try to get full user info if it's the current user
                if (currentUser && currentUser.username === username) {
                    try {
                        const profileResponse = await fetch(`${API_BASE}/api/profile/`, {
                            credentials: 'include'
                        });
                        const profileData = await profileResponse.json();
                        if (profileData.success) {
                            Object.assign(user, profileData.user);
                        }
                    } catch (e) {
                        console.log('Could not load full profile info');
                    }
                }
                
                profileHeader.innerHTML = `
                    <div class="profile-avatar">
                        ${user.profile_picture 
                            ? `<img src="${user.profile_picture}" alt="${user.username}" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`
                            : '👤'
                        }
                    </div>
                    <h1 class="profile-name">${user.first_name || user.last_name ? `${user.first_name} ${user.last_name}`.trim() : user.username}</h1>
                    <div class="profile-username">@${escapeHtml(user.username)}</div>
                    ${user.bio ? `<div class="profile-bio">${escapeHtml(user.bio)}</div>` : ''}
                    <div style="margin-top: 20px;">
                        <button class="btn btn-primary" onclick="showUserPosts('${escapeHtml(user.username).replace(/'/g, "\\'")}')">
                            📝 مشاهده همه پست‌ها
                        </button>
                    </div>
                `;
            }
            
            // Load recent user posts
            const container = document.getElementById('profile-posts');
            if (container) {
                if (userData.posts && userData.posts.length > 0) {
                    // Show only first 5 posts
                    const recentPosts = userData.posts.slice(0, 5);
                    container.innerHTML = `
                        <div class="card">
                            <h3>آخرین پست‌ها</h3>
                        </div>
                        ${recentPosts.map(post => renderPost(post)).join('')}
                    `;
                } else {
                    container.innerHTML = '<div class="card"><p style="text-align: center; color: #657786;">این کاربر هنوز پستی منتشر نکرده است</p></div>';
                }
            }
        } else {
            showMessage('کاربر یافت نشد', 'error');
            showPage('home');
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        showMessage('خطا در بارگذاری پروفایل', 'error');
    } finally {
        hideLoading();
    }
}

async function showUserPosts(username) {
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/api/users/${encodeURIComponent(username)}/posts/`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            await loadPageContent('user-posts');
            
            const header = document.getElementById('user-posts-header');
            if (header) {
                header.innerHTML = `
                    <h2>پست‌های @${escapeHtml(data.username)}</h2>
                    <a href="#profile?user=${encodeURIComponent(data.username)}" onclick="showUserProfile('${escapeHtml(data.username).replace(/'/g, "\\'")}'); return false;" class="btn btn-secondary">
                        ← بازگشت به پروفایل
                    </a>
                `;
            }
            
            const container = document.getElementById('user-posts-container');
            if (container) {
                if (data.posts && data.posts.length > 0) {
                    container.innerHTML = data.posts.map(post => {
                        // Add room link badge for user posts
                        let postHtml = renderPost(post);
                        if (post.category) {
                            postHtml = postHtml.replace('</div>', `
                                <div style="margin-top: 10px;">
                                    <a href="#explore?room=${encodeURIComponent(post.category)}" 
                                       onclick="event.stopPropagation(); showRoom('${escapeHtml(post.category).replace(/'/g, "\\'")}'); return false;" 
                                       class="btn btn-secondary" style="font-size: 13px; padding: 6px 14px;">
                                        مشاهده اتاق "${escapeHtml(post.category)}"
                                    </a>
                                </div>
                            </div>`);
                        }
                        return postHtml;
                    }).join('');
                } else {
                    container.innerHTML = '<div class="card"><p style="text-align: center; color: #657786;">این کاربر هنوز پستی منتشر نکرده است</p></div>';
                }
            }
        } else {
            showMessage('خطا در بارگذاری پست‌ها', 'error');
        }
    } catch (error) {
        console.error('Error loading user posts:', error);
        showMessage('خطا در بارگذاری پست‌ها', 'error');
    } finally {
        hideLoading();
    }
}

async function searchUsers(query) {
    if (!query.trim()) {
        showMessage('لطفا نام کاربری را وارد کنید', 'error');
        return;
    }
    
    showLoading();
    try {
        // Since we don't have a search API, we'll try to load the user's profile directly
        const response = await fetch(`${API_BASE}/api/users/${encodeURIComponent(query)}/posts/`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            showUserProfile(query);
        } else {
            const resultsContainer = document.getElementById('search-results');
            if (resultsContainer) {
                resultsContainer.innerHTML = '<div class="card"><p style="text-align: center; color: #657786;">کاربری با این نام یافت نشد</p></div>';
            }
        }
    } catch (error) {
        console.error('Error searching users:', error);
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '<div class="message error">خطا در جستجو</div>';
        }
    } finally {
        hideLoading();
    }
}

async function showRoom(roomName) {
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/api/posts/category/${encodeURIComponent(roomName)}/`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            await loadPageContent('explore');
            
            const roomInput = document.getElementById('room-name');
            if (roomInput) {
                roomInput.value = roomName;
            }
            
            const container = document.getElementById('room-posts-container');
            if (container) {
                container.innerHTML = 
                    `<div class="card">
                        <h3>📁 پست‌های اتاق: "${escapeHtml(data.category)}"</h3>
                        <p style="color: #657786; margin-top: 5px;">${data.posts.length} پست</p>
                    </div>` +
                    (data.posts && data.posts.length > 0 
                        ? data.posts.map(post => renderPost(post)).join('')
                        : '<div class="card"><p style="text-align: center; color: #657786;">پستی در این اتاق یافت نشد</p></div>'
                    );
            }
        } else {
            showMessage('خطا در بارگذاری اتاق', 'error');
        }
    } catch (error) {
        console.error('Error loading room:', error);
        showMessage('خطا در بارگذاری اتاق', 'error');
    } finally {
        hideLoading();
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { loadUserProfile, showUserPosts, searchUsers, showRoom };
}