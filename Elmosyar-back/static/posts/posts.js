// Posts JS: handles fetching, creating, liking, commenting, reposting
const API_BASE = window.location.origin;

function renderMedia(media) {
    if (!media || !media.url) return '';
    if (media.type === 'image' || media.type.startsWith('image/')) {
        return `<img src="${media.url}" style="max-width:300px;">`;
    } else if (media.type === 'video' || media.type.startsWith('video/')) {
        return `<video src="${media.url}" controls style="max-width:300px;"></video>`;
    } else if (media.type === 'audio' || media.type.startsWith('audio/')) {
        return `<audio src="${media.url}" controls></audio>`;
    } else {
        return `<a href="${media.url}" target="_blank">📎 Download file</a>`;
    }
}

// Dynamic category tabs
let lastCategories = [];
function renderCategoryTabs(selected, posts) {
    const tabs = document.getElementById('category-tabs');
    if (!tabs) return;
    // Extract unique categories from posts
    const cats = [{id:'',name:'All'}];
    const seen = new Set();
    posts.forEach(p => {
        if (p.category && !seen.has(p.category)) {
            cats.push({id:p.category,name:p.category});
            seen.add(p.category);
        }
    });
    lastCategories = cats;
    tabs.innerHTML = cats.map(cat => `<button class="cat-tab${cat.id===selected?' active':''}" data-id="${cat.id}">${cat.name}</button>`).join(' ');
    document.querySelectorAll('.cat-tab').forEach(b => b.addEventListener('click', e => {
        const id = e.currentTarget.getAttribute('data-id');
        fetchPosts(id);
    }));
}

async function fetchPosts(category = '') {
    let url = category ? `${API_BASE}/api/posts/category/${category}/` : `${API_BASE}/api/posts/`;
    const res = await fetch(url, { credentials: 'same-origin' });
    const data = await res.json();
    const container = document.getElementById('posts-container');
    container.innerHTML = '';
    // Pass posts to category tab renderer
    renderCategoryTabs(category, data.posts || []);

    if (data.success && data.posts.length) {
        for (const post of data.posts) {
            let mediaHtml = '';
            if (post.media && post.media.length) {
                mediaHtml = '<div class="post-media">' + post.media.map(renderMedia).join('<br>') + '</div>';
            }
            const tagsHtml = post.tags.length ? `<div class="post-tags">📌 Tags: ${post.tags.join(', ')}</div>` : '';
            const mentionsHtml = post.mentions.length ? `<div class="post-mentions">@Mentions: ${post.mentions.join(', ')}</div>` : '';

            // Show repost/reply info
            let infoHtml = '';
            if (post.is_repost && post.original_post_id) {
                infoHtml += `<div class="post-info">🔄 Repost from <a href="#" class="show-original" data-id="${post.original_post_id}" data-postid="${post.id}">Post #${post.original_post_id}</a></div>`;
            }
            if (post.parent_id) {
                infoHtml += `<div class="post-info">↩️ Reply to <a href="#" class="show-parent" data-id="${post.parent_id}" data-postid="${post.id}">Post #${post.parent_id}</a></div>`;
            }

            container.innerHTML += `
                <div class="post">
                    <div class="post-header">
                        <span class="post-author">${post.author}</span>
                        <span class="post-date">${new Date(post.created_at).toLocaleString()}</span>
                    </div>
                    ${infoHtml}
                    <div id="parent-preview-${post.id}" class="parent-preview" style="display:none;"></div>
                    <div class="post-content">${post.content}</div>
                    ${mediaHtml}
                    ${tagsHtml}
                    ${mentionsHtml}
                    <div class="post-actions">
                        <button data-id="${post.id}" class="like-btn">👍 Like (${post.likes_count})</button>
                        <button data-id="${post.id}" class="dislike-btn">👎 Dislike (${post.dislikes_count || 0})</button>
                        <button data-id="${post.id}" class="comment-btn">💬 Comment (${post.comments_count})</button>
                        <button data-id="${post.id}" data-category="${post.category || ''}" class="reply-btn">↩️ Reply</button>
                        <button data-id="${post.id}" class="repost-btn">🔄 Repost (${post.reposts_count})</button>
                    </div>
                    <div id="comments-${post.id}" class="comment-section" style="display:none;"></div>
                </div>
            `;
        }

        // attach handlers
        document.querySelectorAll('.like-btn').forEach(b => b.addEventListener('click', async (e) => {
            const id = e.currentTarget.getAttribute('data-id');
            await fetch(`${API_BASE}/api/posts/${id}/like/`, { method: 'POST', credentials: 'same-origin' });
            fetchPosts(category);
        }));

        document.querySelectorAll('.repost-btn').forEach(b => b.addEventListener('click', async (e) => {
            const id = e.currentTarget.getAttribute('data-id');
            await fetch(`${API_BASE}/api/posts/${id}/repost/`, { method: 'POST', credentials: 'same-origin' });
            fetchPosts(category);
        }));

        document.querySelectorAll('.dislike-btn').forEach(b => b.addEventListener('click', async (e) => {
            const id = e.currentTarget.getAttribute('data-id');
            await fetch(`${API_BASE}/api/posts/${id}/dislike/`, { method: 'POST', credentials: 'same-origin' });
            fetchPosts(category);
        }));

        document.querySelectorAll('.reply-btn').forEach(b => b.addEventListener('click', (e) => {
            const id = e.currentTarget.getAttribute('data-id');
            const categoryVal = e.currentTarget.dataset.category || '';
            // set parent id into the post form hidden field
            const parentInput = document.getElementById('post-parent');
            const categoryInput = document.getElementById('post-category');
            if (parentInput) parentInput.value = id;
            if (categoryInput && categoryVal) categoryInput.value = categoryVal;
            // focus the form textarea
            const ta = document.getElementById('post-content');
            if (ta) { ta.focus(); ta.placeholder = 'Replying to post...'; }
        }));

        document.querySelectorAll('.comment-btn').forEach(b => b.addEventListener('click', (e) => {
            const id = e.currentTarget.getAttribute('data-id');
            toggleCommentBox(id);
        }));

        // Show parent/original post preview
        // inline preview renderers
        async function renderInlinePreview(targetPostId, containerId) {
            const previewRes = await fetch(`${API_BASE}/api/posts/${targetPostId}/`);
            const previewData = await previewRes.json();
            const container = document.getElementById(containerId);
            if (!container) return;
            if (previewData.success && previewData.post) {
                const p = previewData.post;
                const media = p.media && p.media.length ? '<div class="post-media-small">' + p.media.map(renderMedia).join('') + '</div>' : '';
                container.innerHTML = `
                    <div class="post-preview-card">
                        <div class="post-preview-header"><strong>${p.author}</strong> · <span class="post-date">${new Date(p.created_at).toLocaleString()}</span></div>
                        <div class="post-preview-content">${p.content}</div>
                        ${media}
                        <div class="post-preview-actions">↩️ Reply to <strong>${p.author}</strong> · 🔗 <a href="/posts/?thread=${p.id}" data-id="${p.id}" class="open-thread">Open thread</a></div>
                    </div>
                `;
                container.style.display = 'block';
                // attach open-thread handler
                const open = container.querySelector('.open-thread');
                if (open) open.addEventListener('click', (ev) => { ev.preventDefault(); window.location.href = `/posts/?thread=${p.id}`; });
            } else {
                container.innerHTML = '<div class="post-preview-card" style="color:#999;">Post not found.</div>';
                container.style.display = 'block';
            }
        }

        document.querySelectorAll('.show-parent').forEach(a => a.addEventListener('click', async (e) => {
            e.preventDefault();
            const id = e.currentTarget.getAttribute('data-id');
            const postId = e.currentTarget.dataset.postid;
            const containerId = `parent-preview-${postId}`;
            const container = document.getElementById(containerId);
            if (container && container.style.display === 'block') {
                container.style.display = 'none';
                container.innerHTML = '';
            } else {
                await renderInlinePreview(id, containerId);
            }
        }));

        document.querySelectorAll('.show-original').forEach(a => a.addEventListener('click', async (e) => {
            e.preventDefault();
            const id = e.currentTarget.getAttribute('data-id');
            const postId = e.currentTarget.dataset.postid;
            const containerId = `parent-preview-${postId}`;
            const container = document.getElementById(containerId);
            if (container && container.style.display === 'block') {
                container.style.display = 'none';
                container.innerHTML = '';
            } else {
                await renderInlinePreview(id, containerId);
            }
        }));

    } else {
        container.innerHTML = '<p style="text-align: center; color: #999;">No posts yet.</p>';
    }
}

async function toggleCommentBox(postId) {
    const box = document.getElementById(`comments-${postId}`);
    if (box.style.display === 'none') {
        box.style.display = 'block';
        // fetch thread (replies)
        const res = await fetch(`${API_BASE}/api/posts/${postId}/thread/`);
        const data = await res.json();
        let repliesHtml = '';
        if (data.success && data.thread && data.thread.replies && data.thread.replies.length) {
            repliesHtml = '<div class="replies-list">' + data.thread.replies.map(r => `
                <div class="reply">
                    <span class="reply-author">${r.author}</span>:
                    <span class="reply-content">${r.content}</span>
                    <span class="reply-date">${new Date(r.created_at).toLocaleString()}</span>
                </div>
            `).join('') + '</div>';
        } else {
            repliesHtml = '<div class="replies-list" style="color:#999;">No replies yet.</div>';
        }
        box.innerHTML = `
            <div class="comment-box">
                <textarea id="comment-content-${postId}" placeholder="Write a comment..."></textarea>
                <button data-id="${postId}" class="submit-comment-btn">Send</button>
            </div>
            ${repliesHtml}
        `;
        box.querySelector('.submit-comment-btn').addEventListener('click', async (e) => {
            const id = e.currentTarget.getAttribute('data-id');
            const content = document.getElementById(`comment-content-${id}`).value;
            if (!content.trim()) { alert('Comment cannot be empty'); return; }
            await fetch(`${API_BASE}/api/posts/${id}/comment/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({ content })
            });
            fetchPosts();
        });
    } else {
        box.style.display = 'none';
    }
}

// Submit new post
function initPostForm() {
    const form = document.getElementById('post-form');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const content = document.getElementById('post-content').value;
        const tags = document.getElementById('post-tags').value;
        const mentions = document.getElementById('post-mentions').value;
        const parent = document.getElementById('post-parent') ? document.getElementById('post-parent').value : '';
        const category = document.getElementById('post-category') ? document.getElementById('post-category').value : '';
        const mediaInput = document.getElementById('post-media');

        const formData = new FormData();
        formData.append('content', content);
        formData.append('tags', tags);
        formData.append('mentions', mentions);
        if (parent) formData.append('parent', parent);
        if (category) formData.append('category', category);
        for (let file of mediaInput.files) formData.append('media', file);

        const res = await fetch(`${API_BASE}/api/posts/`, {
            method: 'POST',
            credentials: 'same-origin',
            body: formData
        });
        const data = await res.json();
        const msg = document.getElementById('post-message');
        if (data.success) {
            msg.className = 'message success';
            msg.textContent = '✓ Post created!';
            form.reset();
            // clear parent after posting a reply
            const parentInput = document.getElementById('post-parent');
            if (parentInput) parentInput.value = '';
            const categoryInput = document.getElementById('post-category');
            if (categoryInput) categoryInput.placeholder = 'Category / Room ID (optional)';
            fetchPosts();
        } else {
            msg.className = 'message error';
            msg.textContent = '✗ ' + (data.message || 'Error creating post.');
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initPostForm();
    // add category tabs container
    const postsList = document.getElementById('posts-list');
    if (postsList) {
        const tabsDiv = document.createElement('div');
        tabsDiv.id = 'category-tabs';
        tabsDiv.style = 'margin-bottom:20px;text-align:center;';
        postsList.prepend(tabsDiv);
    }
    fetchPosts();
});
