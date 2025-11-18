// Posts functionality
async function loadPosts(containerId, endpoint) {
    showLoading();
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        const container = document.getElementById(containerId);
        
        if (data.success && data.posts.length > 0) {
            container.innerHTML = data.posts.map(post => renderPost(post)).join('');
        } else {
            container.innerHTML = '<div class="card"><p style="text-align: center; color: #657786;">پستی یافت نشد</p></div>';
        }
    } catch (error) {
        console.error('Error loading posts:', error);
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '<div class="message error">خطا در بارگذاری پست‌ها</div>';
        }
    } finally {
        hideLoading();
    }
}

function renderPost(post) {
    const mediaHtml = post.media && post.media.length > 0 
        ? post.media.map(media => {
            if (media.type === 'image') {
                return `<div class="post-media"><img src="${media.url}" alt="Post image"></div>`;
            } else if (media.type === 'video') {
                return `<div class="post-media"><video src="${media.url}" controls style="max-width: 100%; border-radius: 8px;"></video></div>`;
            }
            return '';
        }).join('') 
        : '';

    const tagsHtml = post.tags && post.tags.length > 0 
        ? `<div class="post-tags">${post.tags.map(tag => `<span class="tag">#${tag}</span>`).join('')}</div>` 
        : '';

    const roomHtml = post.category 
        ? `<a href="#explore?room=${encodeURIComponent(post.category)}" onclick="event.preventDefault(); showRoom('${escapeHtml(post.category).replace(/'/g, "\\'")}'); return false;" class="room-badge">🏠 ${escapeHtml(post.category)}</a>` 
        : '';

    // Handle author info
    const authorUsername = post.author_info ? post.author_info.username : post.author;
    const authorProfilePic = post.author_info ? post.author_info.profile_picture : null;

    return `
        <div class="post" data-post-id="${post.id}" onclick="showPostDetail(${post.id})" style="cursor: pointer;">
            <div class="post-header">
                <div class="post-avatar">
                    ${authorProfilePic 
                        ? `<img src="${authorProfilePic}" alt="${escapeHtml(authorUsername)}" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`
                        : '👤'
                    }
                </div>
                <div class="post-user">
                    <a href="#profile?user=${encodeURIComponent(authorUsername)}" onclick="event.stopPropagation(); showUserProfile('${escapeHtml(authorUsername).replace(/'/g, "\\'")}'); return false;" class="post-username">@${escapeHtml(authorUsername)}</a>
                    <div class="post-date">${formatDate(post.created_at)}</div>
                </div>
            </div>
            <div class="post-content">${escapeHtml(post.content)}</div>
            ${mediaHtml}
            ${tagsHtml}
            ${roomHtml}
            <div class="post-actions">
                <button class="action-btn ${post.likes_count > 0 ? 'liked' : ''}" onclick="event.stopPropagation(); likePost(${post.id}); return false;">
                    👍 ${post.likes_count}
                </button>
                <button class="action-btn" onclick="event.stopPropagation(); showPostDetail(${post.id}); return false;">
                    💬 ${post.comments_count}
                </button>
                <button class="action-btn">
                    🔄 ${post.reposts_count}
                </button>
                <button class="action-btn">
                    ↩️ ${post.replies_count || 0}
                </button>
            </div>
        </div>
    `;
}

async function createPost(formData) {
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/api/posts/`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('پست با موفقیت ایجاد شد!');
            const form = document.getElementById('post-form');
            if (form) form.reset();
            return true;
        } else {
            showMessage(data.message, 'error');
            return false;
        }
    } catch (error) {
        showMessage('خطا در ایجاد پست', 'error');
        return false;
    } finally {
        hideLoading();
    }
}

async function likePost(postId) {
    try {
        const response = await fetch(`${API_BASE}/api/posts/${postId}/like/`, {
            method: 'POST',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update like count in UI
            const postElement = document.querySelector(`[data-post-id="${postId}"]`);
            if (postElement) {
                const likeBtn = postElement.querySelector('.action-btn');
                if (likeBtn) {
                    likeBtn.innerHTML = `👍 ${data.likes_count}`;
                    if (data.likes_count > 0) {
                        likeBtn.classList.add('liked');
                    } else {
                        likeBtn.classList.remove('liked');
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error liking post:', error);
    }
}

async function showPostDetail(postId) {
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/api/posts/${postId}/`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            // Store current post ID for comments
            window.currentPostId = postId;
            
            // Load post detail page
            await loadPageContent('post-detail');
            
            // Render main post
            const postContent = document.getElementById('post-detail-content');
            if (postContent) {
                postContent.innerHTML = renderPost(data.post);
            }
            
            // Load comments
            await loadComments(postId, data.post.comments || []);
            
            // Load replies
            await loadReplies(postId, data.post.replies || []);
            
            // Setup comment form
            const commentForm = document.getElementById('comment-form');
            if (commentForm) {
                commentForm.onsubmit = async (e) => {
                    e.preventDefault();
                    await submitComment(postId);
                };
            }
        } else {
            showMessage('خطا در بارگذاری پست', 'error');
        }
    } catch (error) {
        console.error('Error loading post detail:', error);
        showMessage('خطا در بارگذاری پست', 'error');
    } finally {
        hideLoading();
    }
}

async function loadComments(postId, comments) {
    const container = document.getElementById('comments-container');
    if (!container) return;
    
    if (comments && comments.length > 0) {
        container.innerHTML = comments.map(comment => renderComment(comment)).join('');
    } else {
        container.innerHTML = '<p style="text-align: center; color: #657786; padding: 20px;">هنوز نظری وجود ندارد</p>';
    }
}

async function loadReplies(postId, replies) {
    const container = document.getElementById('replies-container');
    if (!container) return;
    
    if (replies && replies.length > 0) {
        container.innerHTML = replies.map(reply => renderPost(reply)).join('');
    } else {
        container.innerHTML = '<p style="text-align: center; color: #657786; padding: 20px;">هنوز پاسخی وجود ندارد</p>';
    }
}

function renderComment(comment) {
    return `
        <div class="post" style="margin-bottom: 15px;">
            <div class="post-header">
                <div class="post-avatar" style="width: 40px; height: 40px; font-size: 16px;">
                    👤
                </div>
                <div class="post-user">
                    <a href="#profile?user=${encodeURIComponent(comment.user)}" onclick="showUserProfile('${escapeHtml(comment.user).replace(/'/g, "\\'")}'); return false;" class="post-username">@${escapeHtml(comment.user)}</a>
                    <div class="post-date">${formatDate(comment.created_at)}</div>
                </div>
            </div>
            <div class="post-content">${escapeHtml(comment.content)}</div>
        </div>
    `;
}

async function submitComment(postId) {
    const contentInput = document.getElementById('comment-content');
    if (!contentInput) return;
    
    const content = contentInput.value.trim();
    if (!content) {
        showMessage('لطفا متن کامنت را وارد کنید', 'error');
        return;
    }
    
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/api/posts/${postId}/comment/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ content })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('کامنت با موفقیت ثبت شد');
            contentInput.value = '';
            // Reload post detail to show new comment
            showPostDetail(postId);
        } else {
            showMessage(data.message, 'error');
        }
    } catch (error) {
        showMessage('خطا در ثبت کامنت', 'error');
    } finally {
        hideLoading();
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { loadPosts, renderPost, createPost, likePost, showPostDetail };
}