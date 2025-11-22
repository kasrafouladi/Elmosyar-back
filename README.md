# API Request Examples with cURL

## Base URL
```bash
curl http://89.106.206.119:8000/api
```

## 🔐 Authentication Endpoints

### Sign Up
```bash
curl -X POST http://89.106.206.119:8000/api/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123",
    "password2": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Signup successful. Please check your email to verify your account.",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile_picture": null,
    "bio": "",
    "website": "",
    "followers_count": 0,
    "following_count": 0,
    "is_email_verified": false,
    "date_joined": "2024-01-15T10:30:00Z"
  }
}
```

### Login
```bash
curl -X POST http://89.106.206.119:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "johndoe",
    "password": "securepassword123",
    "rememberMe": true
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile_picture": null,
    "bio": "",
    "website": "",
    "followers_count": 5,
    "following_count": 3,
    "is_email_verified": true,
    "date_joined": "2024-01-15T10:30:00Z"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

### Verify Token
```bash
curl -X POST http://89.106.206.119:8000/api/token/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Token is valid"
}
```

### Refresh Token
```bash
curl -X POST http://89.106.206.119:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

**Response:**
```json
{
  "success": true,
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Email Verification

```bash
curl http://89.106.206.119:8000/api/verify-email/0c0ce97e-48b4-4ef9-822a-71361f8ea018/
```

**Response:**
```json
{
  "success": true,
  "message": "Email verified successfully. You are now logged in.",
  "user": {
    "id": 2,
    "username": "johndoe",
    "first_name": "",
    "last_name": "",
    "profile_picture": null,
    "bio": null,
    "student_id": null,
    "followers_count": 0,
    "following_count": 0,
    "posts_count": 0,
    "email": "john@example.com",
    "is_email_verified": true,
    "created_at": "2025-11-22T18:17:15.335568+00:00"
  }
}
```

### Resend Verification Email
```bash
curl -X POST http://89.106.206.119:8000/api/resend-verification-email/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Verification email sent successfully. Please check your email."
}
```

### Request Password Reset
```bash
curl -X POST http://89.106.206.119:8000/api/password-reset/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "If this email exists in our system, a password reset link has been sent"
}
```

## 👤 Profile Endpoints

### Get Current User Profile
```bash
curl -X GET http://89.106.206.119:8000/api/profile/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile_picture": "/media/profile_pictures/john.jpg",
    "bio": "Software developer and tech enthusiast",
    "website": "https://johndoe.com",
    "followers_count": 15,
    "following_count": 8,
    "is_email_verified": true,
    "date_joined": "2024-01-15T10:30:00Z"
  }
}
```

### Get User Public Profile
```bash
curl -X GET http://89.106.206.119:8000/api/users/johndoe/profile/
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "profile_picture": "/media/profile_pictures/john.jpg",
    "bio": "Software developer and tech enthusiast",
    "website": "https://johndoe.com",
    "followers_count": 15,
    "following_count": 8,
    "date_joined": "2024-01-15T10:30:00Z"
  }
}
```

### Update Profile
```bash
curl -X PUT http://89.106.206.119:8000/api/profile/update/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Senior software engineer at Tech Corp",
    "website": "https://john-doe-portfolio.com"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile_picture": "/media/profile_pictures/john.jpg",
    "bio": "Senior software engineer at Tech Corp",
    "website": "https://john-doe-portfolio.com",
    "followers_count": 15,
    "following_count": 8,
    "is_email_verified": true,
    "date_joined": "2024-01-15T10:30:00Z"
  }
}
```

## 📝 Post Endpoints

### Get Posts
```bash
curl -X GET "http://89.106.206.119:8000/api/posts/?page=1&per_page=10&category=tech"
```

**Response:**
```json
{
  "success": true,
  "posts": [
    {
      "id": 1,
      "author": {
        "id": 1,
        "username": "johndoe",
        "profile_picture": "/media/profile_pictures/john.jpg"
      },
      "content": "Just launched my new project! 🚀",
      "category": "tech",
      "tags": "django,react,webdev",
      "media": [
        {
          "id": 1,
          "file": "/media/posts/project_screenshot.jpg",
          "media_type": "image"
        }
      ],
      "likes_count": 25,
      "dislikes_count": 2,
      "comments_count": 8,
      "reposts_count": 3,
      "user_reaction": "like",
      "is_saved": false,
      "created_at": "2024-01-15T14:30:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_pages": 5,
    "total_count": 48,
    "has_next": true,
    "has_previous": false
  }
}
```

### Create Post
```bash
curl -X POST http://89.106.206.119:8000/api/posts/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -F "content=Check out this amazing sunset! 🌅" \
  -F "category=photography" \
  -F "tags=sunset,nature" \
  -F "media=@/path/to/sunset.jpg"
```

**Response:**
```json
{
  "success": true,
  "post": {
    "id": 2,
    "author": {
      "id": 1,
      "username": "johndoe",
      "profile_picture": "/media/profile_pictures/john.jpg"
    },
    "content": "Check out this amazing sunset! 🌅",
    "category": "photography",
    "tags": "sunset,nature",
    "media": [
      {
        "id": 2,
        "file": "/media/posts/sunset.jpg",
        "media_type": "image"
      }
    ],
    "likes_count": 0,
    "dislikes_count": 0,
    "comments_count": 0,
    "reposts_count": 0,
    "user_reaction": null,
    "is_saved": false,
    "created_at": "2024-01-15T15:45:00Z",
    "updated_at": "2024-01-15T15:45:00Z"
  }
}
```

### Like Post
```bash
curl -X POST http://89.106.206.119:8000/api/posts/1/like/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "message": "Liked",
  "likes_count": 26,
  "dislikes_count": 2,
  "user_reaction": "like"
}
```

### Comment on Post
```bash
curl -X POST http://89.106.206.119:8000/api/posts/1/comment/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Great work! This looks amazing! 👏"
  }'
```

**Response:**
```json
{
  "success": true,
  "comment": {
    "id": 1,
    "user": {
      "id": 2,
      "username": "janedoe",
      "profile_picture": "/media/profile_pictures/jane.jpg"
    },
    "content": "Great work! This looks amazing! 👏",
    "likes_count": 0,
    "is_liked": false,
    "created_at": "2024-01-15T16:00:00Z"
  },
  "comments_count": 9
}
```

## 🤝 Social Endpoints

### Follow User
```bash
curl -X POST http://89.106.206.119:8000/api/users/janedoe/follow/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "message": "You are now following janedoe",
  "followers_count": 16
}
```

### Get User Followers
```bash
curl -X GET "http://89.106.206.119:8000/api/users/johndoe/followers/?page=1&per_page=10"
```

**Response:**
```json
{
  "success": true,
  "followers": [
    {
      "id": 2,
      "username": "janedoe",
      "profile_picture": "/media/profile_pictures/jane.jpg",
      "bio": "Digital artist and designer",
      "followers_count": 120,
      "following_count": 45
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_pages": 2,
    "total_count": 16,
    "has_next": true,
    "has_previous": false
  }
}
```

## 🔔 Notification Endpoints

### Get Notifications
```bash
curl -X GET "http://89.106.206.119:8000/api/notifications/?page=1&per_page=10" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "notifications": [
    {
      "id": 1,
      "sender": {
        "id": 2,
        "username": "janedoe",
        "profile_picture": "/media/profile_pictures/jane.jpg"
      },
      "notif_type": "like",
      "message": "janedoe liked your post",
      "post": {
        "id": 1,
        "content": "Just launched my new project! 🚀"
      },
      "is_read": false,
      "created_at": "2024-01-15T16:30:00Z"
    }
  ],
  "unread_count": 3,
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_pages": 1,
    "total_count": 3,
    "has_next": false,
    "has_previous": false
  }
}
```

## 💬 Messaging Endpoints

### Get Conversations
```bash
curl -X GET http://89.106.206.119:8000/api/conversations/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "conversations": [
    {
      "id": 1,
      "participants": [
        {
          "id": 1,
          "username": "johndoe",
          "profile_picture": "/media/profile_pictures/john.jpg"
        },
        {
          "id": 2,
          "username": "janedoe",
          "profile_picture": "/media/profile_pictures/jane.jpg"
        }
      ],
      "last_message": {
        "id": 5,
        "content": "Looking forward to it!",
        "sender": 2,
        "is_read": true,
        "created_at": "2024-01-15T17:00:00Z"
      },
      "unread_count": 0,
      "updated_at": "2024-01-15T17:00:00Z"
    }
  ],
  "count": 1
}
```

### Send Message
```bash
curl -X POST http://89.106.206.119:8000/api/conversations/1/send/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hey! How are you doing?"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": {
    "id": 6,
    "conversation": 1,
    "sender": {
      "id": 1,
      "username": "johndoe",
      "profile_picture": "/media/profile_pictures/john.jpg"
    },
    "content": "Hey! How are you doing?",
    "image": null,
    "file": null,
    "is_read": false,
    "created_at": "2024-01-15T17:05:00Z"
  }
}
```

## 🏠 Basic Endpoint

### API Root
```bash
curl -X GET http://89.106.206.119:8000/api/
```

**Response:**
```json
{
  "success": true,
  "message": "API is running",
  "endpoints": {
    "auth": {
      "signup": "/api/signup/",
      "login": "/api/login/",
      "logout": "/api/logout/",
      "verify_email": "/api/verify-email/{token}/",
      "password_reset_request": "/api/password-reset/request/",
      "password_reset": "/api/password-reset/{token}/"
    },
    "profile": {
      "get_profile": "/api/profile/",
      "update_profile": "/api/profile/update/",
      "update_profile_picture": "/api/profile/update-picture/",
      "get_user_profile": "/api/users/{username}/profile/"
    }
    // ... (truncated for brevity)
  }
}
```

## ⚠️ Error Responses

### Validation Error Example
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "email": ["This field is required."],
    "password": ["This password is too short."]
  }
}
```

### Authentication Error Example
```json
{
  "success": false,
  "message": "Authentication credentials were not provided."
}
```

### Not Found Error Example
```json
{
  "success": false,
  "message": "Not found."
}
```

## 🔑 Token Endpoints

### Logout
```bash
curl -X POST http://89.106.206.119:8000/api/logout/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

## 🖼️ Profile Picture Endpoints

### Delete Profile Picture
```bash
curl -X DELETE http://89.106.206.119:8000/api/profile/delete-picture/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```


**Response:**
```json
{
  "success": true,
  "message": "Profile picture deleted successfully"
}
```

## 🤝 Social Endpoints (Additional)

### Unfollow User
```bash
curl -X POST http://89.106.206.119:8000/api/users/janedoe/unfollow/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "message": "You have unfollowed janedoe",
  "followers_count": 15
}
```

### Get User Following
```bash
curl -X GET "http://89.106.206.119:8000/api/users/johndoe/following/?page=1&per_page=10"
```

**Response:**
```json
{
  "success": true,
  "following": [
    {
      "id": 2,
      "username": "janedoe",
      "profile_picture": "/media/profile_pictures/jane.jpg",
      "bio": "Digital artist and designer",
      "followers_count": 120,
      "following_count": 45
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_pages": 1,
    "total_count": 8,
    "has_next": false,
    "has_previous": false
  }
}
```

## 📝 Post Endpoints (Additional)

### Get Post Detail
```bash
curl -X GET http://89.106.206.119:8000/api/posts/1/
```

**Response:**
```json
{
  "success": true,
  "post": {
    "id": 1,
    "author": {
      "id": 1,
      "username": "johndoe",
      "profile_picture": "/media/profile_pictures/john.jpg"
    },
    "content": "Just launched my new project! 🚀",
    "category": "tech",
    "tags": "django,react,webdev",
    "media": [
      {
        "id": 1,
        "file": "/media/posts/project_screenshot.jpg",
        "media_type": "image"
      }
    ],
    "likes_count": 25,
    "dislikes_count": 2,
    "comments_count": 8,
    "reposts_count": 3,
    "user_reaction": "like",
    "is_saved": false,
    "comments": [
      {
        "id": 1,
        "user": {
          "id": 2,
          "username": "janedoe",
          "profile_picture": "/media/profile_pictures/jane.jpg"
        },
        "content": "Great work! This looks amazing! 👏",
        "likes_count": 2,
        "is_liked": false,
        "created_at": "2024-01-15T16:00:00Z"
      }
    ],
    "replies": [],
    "created_at": "2024-01-15T14:30:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
}
```

### Dislike Post
```bash
curl -X POST http://89.106.206.119:8000/api/posts/1/dislike/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "message": "Disliked",
  "likes_count": 24,
  "dislikes_count": 3,
  "user_reaction": "dislike"
}
```

### Repost Post
```bash
curl -X POST http://89.106.206.119:8000/api/posts/1/repost/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "post": {
    "id": 3,
    "author": {
      "id": 2,
      "username": "janedoe",
      "profile_picture": "/media/profile_pictures/jane.jpg"
    },
    "content": "Just launched my new project! 🚀",
    "category": "tech",
    "tags": "django,react,webdev",
    "is_repost": true,
    "original_post": {
      "id": 1,
      "author": {
        "id": 1,
        "username": "johndoe"
      }
    },
    "likes_count": 0,
    "dislikes_count": 0,
    "comments_count": 0,
    "reposts_count": 0,
    "user_reaction": null,
    "is_saved": false,
    "created_at": "2024-01-15T17:30:00Z",
    "updated_at": "2024-01-15T17:30:00Z"
  }
}
```

### Get Post Thread
```bash
curl -X GET http://89.106.206.119:8000/api/posts/1/thread/
```

**Response:**
```json
{
  "success": true,
  "thread": {
    "id": 1,
    "author": {
      "id": 1,
      "username": "johndoe",
      "profile_picture": "/media/profile_pictures/john.jpg"
    },
    "content": "Just launched my new project! 🚀",
    "category": "tech",
    "tags": "django,react,webdev",
    "media": [
      {
        "id": 1,
        "file": "/media/posts/project_screenshot.jpg",
        "media_type": "image"
      }
    ],
    "likes_count": 25,
    "dislikes_count": 2,
    "comments_count": 8,
    "reposts_count": 3,
    "user_reaction": "like",
    "is_saved": false,
    "replies": [
      {
        "id": 2,
        "author": {
          "id": 2,
          "username": "janedoe",
          "profile_picture": "/media/profile_pictures/jane.jpg"
        },
        "content": "This is amazing! Great job!",
        "parent": 1,
        "likes_count": 2,
        "dislikes_count": 0,
        "comments_count": 0,
        "user_reaction": null,
        "is_saved": false,
        "created_at": "2024-01-15T16:30:00Z"
      }
    ],
    "created_at": "2024-01-15T14:30:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
}
```

### Save Post
```bash
curl -X POST http://89.106.206.119:8000/api/posts/1/save/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "message": "Post saved successfully"
}
```

### Unsave Post
```bash
curl -X POST http://89.106.206.119:8000/api/posts/1/unsave/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "message": "Post unsaved successfully"
}
```

### Get Saved Posts
```bash
curl -X GET "http://89.106.206.119:8000/api/posts/saved/?page=1&per_page=10" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "posts": [
    {
      "id": 1,
      "author": {
        "id": 1,
        "username": "johndoe",
        "profile_picture": "/media/profile_pictures/john.jpg"
      },
      "content": "Just launched my new project! 🚀",
      "category": "tech",
      "tags": "django,react,webdev",
      "media": [
        {
          "id": 1,
          "file": "/media/posts/project_screenshot.jpg",
          "media_type": "image"
        }
      ],
      "likes_count": 25,
      "dislikes_count": 2,
      "comments_count": 8,
      "reposts_count": 3,
      "user_reaction": "like",
      "is_saved": true,
      "created_at": "2024-01-15T14:30:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_pages": 1,
    "total_count": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

### Delete Post
```bash
curl -X DELETE http://89.106.206.119:8000/api/posts/1/delete/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "message": "Post deleted successfully"
}
```

### Update Post
```bash
curl -X PUT http://89.106.206.119:8000/api/posts/1/update/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated content with more details about my project!",
    "tags": "django,react,webdev,update"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Post updated successfully",
  "post": {
    "id": 1,
    "author": {
      "id": 1,
      "username": "johndoe",
      "profile_picture": "/media/profile_pictures/john.jpg"
    },
    "content": "Updated content with more details about my project!",
    "category": "tech",
    "tags": "django,react,webdev,update",
    "media": [
      {
        "id": 1,
        "file": "/media/posts/project_screenshot.jpg",
        "media_type": "image"
      }
    ],
    "likes_count": 25,
    "dislikes_count": 2,
    "comments_count": 8,
    "reposts_count": 3,
    "user_reaction": "like",
    "is_saved": false,
    "created_at": "2024-01-15T14:30:00Z",
    "updated_at": "2024-01-15T18:30:00Z"
  }
}
```

### Get Posts by Category
```bash
curl -X GET "http://89.106.206.119:8000/api/posts/category/tech/?page=1&per_page=10"
```

**Response:**
```json
{
  "success": true,
  "posts": [
    {
      "id": 1,
      "author": {
        "id": 1,
        "username": "johndoe",
        "profile_picture": "/media/profile_pictures/john.jpg"
      },
      "content": "Just launched my new project! 🚀",
      "category": "tech",
      "tags": "django,react,webdev",
      "media": [
        {
          "id": 1,
          "file": "/media/posts/project_screenshot.jpg",
          "media_type": "image"
        }
      ],
      "likes_count": 25,
      "dislikes_count": 2,
      "comments_count": 8,
      "reposts_count": 3,
      "user_reaction": "like",
      "is_saved": false,
      "created_at": "2024-01-15T14:30:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ],
  "category": "tech",
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_pages": 5,
    "total_count": 48,
    "has_next": true,
    "has_previous": false
  }
}
```

### Get User Posts
```bash
curl -X GET "http://89.106.206.119:8000/api/users/johndoe/posts/?page=1&per_page=10"
```

**Response:**
```json
{
  "success": true,
  "posts": [
    {
      "id": 1,
      "author": {
        "id": 1,
        "username": "johndoe",
        "profile_picture": "/media/profile_pictures/john.jpg"
      },
      "content": "Just launched my new project! 🚀",
      "category": "tech",
      "tags": "django,react,webdev",
      "media": [
        {
          "id": 1,
          "file": "/media/posts/project_screenshot.jpg",
          "media_type": "image"
        }
      ],
      "likes_count": 25,
      "dislikes_count": 2,
      "comments_count": 8,
      "reposts_count": 3,
      "user_reaction": "like",
      "is_saved": false,
      "created_at": "2024-01-15T14:30:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ],
  "username": "johndoe",
  "user": {
    "id": 1,
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "profile_picture": "/media/profile_pictures/john.jpg",
    "bio": "Software developer and tech enthusiast",
    "website": "https://johndoe.com",
    "followers_count": 15,
    "following_count": 8,
    "date_joined": "2024-01-15T10:30:00Z"
  },
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_pages": 3,
    "total_count": 25,
    "has_next": true,
    "has_previous": false
  }
}
```

## 💬 Comment Endpoints

### Like Comment
```bash
curl -X POST http://89.106.206.119:8000/api/comments/1/like/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "message": "Comment liked",
  "likes_count": 1,
  "is_liked": true
}
```

### Delete Comment
```bash
curl -X DELETE http://89.106.206.119:8000/api/comments/1/delete/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "message": "Comment deleted successfully"
}
```

### Update Comment
```bash
curl -X PUT http://89.106.206.119:8000/api/comments/1/update/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated comment with more details!"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Comment updated successfully",
  "comment": {
    "id": 1,
    "user": {
      "id": 2,
      "username": "janedoe",
      "profile_picture": "/media/profile_pictures/jane.jpg"
    },
    "content": "Updated comment with more details!",
    "likes_count": 0,
    "is_liked": false,
    "created_at": "2024-01-15T16:00:00Z"
  }
}
```

## 🔔 Notification Endpoints (Additional)

### Mark Notifications as Read
```bash
curl -X POST http://89.106.206.119:8000/api/notifications/mark-read/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "ids": [1, 2, 3]
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Notifications marked as read"
}
```

## 💬 Messaging Endpoints (Additional)

### Start Conversation
```bash
curl -X POST http://89.106.206.119:8000/api/conversations/start/janedoe/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "conversation": {
    "id": 2,
    "participants": [
      {
        "id": 1,
        "username": "johndoe",
        "profile_picture": "/media/profile_pictures/john.jpg"
      },
      {
        "id": 2,
        "username": "janedoe",
        "profile_picture": "/media/profile_pictures/jane.jpg"
      }
    ],
    "last_message": null,
    "unread_count": 0,
    "updated_at": "2024-01-15T18:00:00Z"
  },
  "message": "Conversation started successfully"
}
```

### Get Conversation Detail
```bash
curl -X GET "http://89.106.206.119:8000/api/conversations/1/?page=1&per_page=20" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "conversation": {
    "id": 1,
    "participants": [
      {
        "id": 1,
        "username": "johndoe",
        "profile_picture": "/media/profile_pictures/john.jpg"
      },
      {
        "id": 2,
        "username": "janedoe",
        "profile_picture": "/media/profile_pictures/jane.jpg"
      }
    ],
    "last_message": {
      "id": 6,
      "content": "Hey! How are you doing?",
      "sender": 1,
      "is_read": true,
      "created_at": "2024-01-15T17:05:00Z"
    },
    "unread_count": 0,
    "updated_at": "2024-01-15T17:05:00Z"
  },
  "messages": [
    {
      "id": 6,
      "conversation": 1,
      "sender": {
        "id": 1,
        "username": "johndoe",
        "profile_picture": "/media/profile_pictures/john.jpg"
      },
      "content": "Hey! How are you doing?",
      "image": null,
      "file": null,
      "is_read": true,
      "created_at": "2024-01-15T17:05:00Z"
    },
    {
      "id": 5,
      "conversation": 1,
      "sender": {
        "id": 2,
        "username": "janedoe",
        "profile_picture": "/media/profile_pictures/jane.jpg"
      },
      "content": "Looking forward to it!",
      "image": null,
      "file": null,
      "is_read": true,
      "created_at": "2024-01-15T17:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 1,
    "total_count": 6,
    "has_next": false,
    "has_previous": false
  }
}
```

### Delete Message
```bash
curl -X DELETE http://89.106.206.119:8000/api/messages/1/delete/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "message": "Message deleted successfully"
}
```

### Update Message
```bash
curl -X PUT http://89.106.206.119:8000/api/messages/1/update/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated message content!"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Message updated successfully",
  "message_data": {
    "id": 1,
    "conversation": 1,
    "sender": {
      "id": 1,
      "username": "johndoe",
      "profile_picture": "/media/profile_pictures/john.jpg"
    },
    "content": "Updated message content!",
    "image": null,
    "file": null,
    "is_read": true,
    "created_at": "2024-01-15T16:30:00Z"
  }
}
```

## 🔐 Password Reset Endpoint

### Reset Password
```bash
curl -X POST http://89.106.206.119:8000/api/password-reset/0c0ce97e-48b4-4ef9-822a-71361f8ea018/ \
  -H "Content-Type: application/json" \
  -d '{
    "password": "newsecurepassword123",
    "password_confirm": "newsecurepassword123"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Password reset successfully. You can now login."
}
```

```

این endpointهای جدید را به فایل README.md موجود اضافه کنید تا مستندات کامل شود.
