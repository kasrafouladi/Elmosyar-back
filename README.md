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
    "password": "securepassword123"
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
    "first_name": "",
    "last_name": "",
    "profile_picture": null,
    "bio": null,
    "student_id": null,
    "is_email_verified": false,
    "followers_count": 0,
    "following_count": 0,
    "posts_count": 0,
    "created_at": "2024-01-15T10:30:00Z"
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
    "first_name": "",
    "last_name": "",
    "profile_picture": null,
    "bio": null,
    "student_id": null,
    "is_email_verified": true,
    "followers_count": 5,
    "following_count": 3,
    "posts_count": 12,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```


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
  "message": "Email verified successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "",
    "last_name": "",
    "profile_picture": null,
    "bio": null,
    "student_id": null,
    "is_email_verified": true,
    "followers_count": 0,
    "following_count": 0,
    "posts_count": 0,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
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
    "profile_picture": "/media/profiles/john.jpg",
    "bio": "Software developer and tech enthusiast",
    "info": "student",
    "phone_number" : "29385930",
    "student_id": "12345",
    "is_email_verified": true,
    "followers_count": 15,
    "following_count": 8,
    "posts_count": 25,
    "is_following": false,
    "is_me": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Get User Public Profile
```bash
curl -X GET http://89.106.206.119:8000/api/users/janedoe/profile/
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 2,
    "username": "janedoe",
    "first_name": "Jane",
    "last_name": "Doe",
    "profile_picture": "/media/profiles/jane.jpg",
    "bio": "Digital artist and designer",
    "student_id": null,
    "is_email_verified": true,
    "followers_count": 120,
    "following_count": 45,
    "posts_count": 67,
    "is_following": true,
    "is_me": false,
    "created_at": "2024-01-10T08:15:00Z"
  }
}
```

### Update Profile
```bash
curl -X PUT http://89.106.206.119:8000/api/profile/update/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "username": "janedoe",
    "first_name": "Jane",
    "last_name": "Doe",
    "bio": "Senior software engineer at Tech Corp",
    "student_id": "12345",
    "info": "student",
    "phone_number" : "29385930"
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
    "last_name": "Smith",
    "profile_picture": "/media/profiles/john.jpg",
    "bio": "Senior software engineer at Tech Corp",
    "student_id": "12345",
    "is_email_verified": true,
    "followers_count": 15,
    "following_count": 8,
    "posts_count": 25,
    "is_following": false,
    "is_me": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Update Profile Picture
```bash
curl -X POST http://89.106.206.119:8000/api/profile/update-picture/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -F "profile_picture=@/path/to/new_photo.jpg"
```

**Response:**
```json
{
  "success": true,
  "message": "Profile picture updated successfully",
  "profile_picture": "/media/profiles/new_photo.jpg"
}
```

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

## 📝 Post Endpoints

### Example Format JSON File for Regex Validation
**format.json for "products" category:**
```json
{
  "name": "^[a-zA-Z0-9\\s]{3,100}$",
  "price": "^[0-9]+(\\.[0-9]{1,2})?$",
  "status": "^(available|out of stock|discontinued)$",
  "category": "^(electronics|clothing|books|home)$",
  "rating": "^[1-5](\\.[0-9])?$",
  "stock": "^[0-9]+$"
}
```

## ⚠️ Related Error Responses

### Invalid Search JSON Format
```json
{
  "success": false,
  "message": "Invalid JSON in search parameter"
}
```

### Category Required for Advanced Search
```json
{
  "success": false,
  "message": "Category is required for advanced search"
}
```

### No Format Found for Category
```json
{
  "success": false,
  "message": "No format found for category: programming"
}
```

### Invalid Regex Pattern in Search
```json
{
  "success": false,
  "message": "Error in advanced search"
}
```

### Attribute Validation Failed
```json
{
  "success": false,
  "message": "Attribute 'price' does not match format pattern"
}
```

### Required Attributes Missing
```json
{
  "success": false,
  "message": "Attribute 'title' is required and cannot be removed"
}
```

### 📊 Post Attributes Structure

Posts now support structured data through the `attributes` field. This allows for advanced filtering and validation based on category-specific formats.

#### Example Post with Attributes:
```json
{
  "id": 45,
  "content": "Django REST Framework Tutorial",
  "category": "tutorials",
  "attributes": {
    "difficulty": "intermediate",
    "duration": "2 hours",
    "prerequisites": ["python", "django basics"],
    "resources": [
      {"type": "video", "url": "https://example.com/video"},
      {"type": "code", "url": "https://github.com/example"}
    ],
    "rating": 4.5,
    "tags": ["django", "rest", "api"]
  }
}
```

### Search Parameters:
- Use `search` query parameter with JSON object containing key-regex pairs
- Regex patterns are applied to post attributes
- Both format validation and search regex are applied
- Category must be specified for advanced search

### Validation Flow:
1. When creating/updating a post with attributes
2. System checks if category has a format file
3. Validates each attribute against corresponding regex pattern in format
4. Returns error if validation fails
5. During search, applies both format validation and search criteria


### Get Posts (with pagination and filters)
```bash
curl -X GET "http://89.106.206.119:8000/api/posts/?category=programming&search={\"difficulty\":\"^(easy|medium)$\",\"language\":\"^python$\"}" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "posts": [
    {
      "id": 45,
      "author_info": {
        "id": 1,
        "username": "johndoe",
        "first_name": "John",
        "last_name": "Doe",
        "profile_picture": "/media/profiles/john.jpg",
        "is_email_verified": true,
        "followers_count": 15,
        "following_count": 8,
        "posts_count": 25
      },
      "content": "Python tutorial for beginners",
      "category": "programming",
      "tags": "python,tutorial",
      "attributes": {
        "difficulty": "easy",
        "language": "python",
        "duration": "30min"
      },
      "likes_count": 12,
      "dislikes_count": 0,
      "comments_count": 5,
      "reposts_count": 3,
      "replies_count": 2,
      "user_reaction": "like",
      "is_saved": false,
      "created_at": "2024-01-15T14:30:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 3,
    "total_count": 45,
    "has_next": true,
    "has_previous": false
  }
}
```


### Get Post Detail
```bash
curl -X GET http://89.106.206.119:8000/api/posts/1/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
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
        "url": "/media/posts/project_screenshot.jpg",
        "media_type": "image",
        "caption": "",
        "order": 0,
        "file_size": 2048576
      }
    ],
    "likes_count": 25,
    "dislikes_count": 2,
    "comments_count": 8,
    "reposts_count": 3,
    "replies_count": 2,
    "user_reaction": "like",
    "is_saved": false,
    "comments": [
      {
        "id": 1,
        "user": 2,
        "user_info": {
          "id": 2,
          "username": "janedoe",
          "profile_picture": "/media/profile_pictures/jane.jpg"
        },
        "content": "Great work! This looks amazing! 👏",
        "likes_count": 2,
        "dislike_count": 1,
        "replies_count": 1,
        "is_liked": false,
        "is_disliked": false,
        "created_at": "2024-01-15T16:00:00Z"
      }
    ],
    "replies": [
      {
        "id": 3,
        "author": {
          "id": 2,
          "username": "janedoe",
          "profile_picture": "/media/profile_pictures/jane.jpg"
        },
        "content": "This is amazing! Great job!",
        "category": "tech",
        "tags": "",
        "media": [],
        "likes_count": 2,
        "dislikes_count": 0,
        "comments_count": 0,
        "reposts_count": 0,
        "replies_count": 0,
        "user_reaction": null,
        "is_saved": false,
        "created_at": "2024-01-15T16:30:00Z",
        "updated_at": "2024-01-15T16:30:00Z"
      }
    ],
    "created_at": "2024-01-15T14:30:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
}
```


### Create Post
```bash
curl -X POST http://89.106.206.119:8000/api/posts/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Advanced Python tutorial with OOP concepts",
    "category": "programming",
    "tags": "python,oop,advanced",
    "attributes": {
      "difficulty": "medium",
      "language": "python",
      "duration": "45min",
      "topics": ["classes", "inheritance", "polymorphism"]
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "post": {
    "id": 56,
    "author": 1,
    "author_info": {
      "id": 1,
      "username": "johndoe",
      "first_name": "John",
      "last_name": "Doe",
      "profile_picture": "/media/profiles/john.jpg",
      "is_email_verified": true,
      "followers_count": 15,
      "following_count": 8,
      "posts_count": 27
    },
    "content": "Advanced Python tutorial with OOP concepts",
    "created_at": "2024-01-16T09:15:00Z",
    "updated_at": "2024-01-16T09:15:00Z",
    "tags": "python,oop,advanced",
    "mentions": [],
    "media": [],
    "category": "programming",
    "parent": null,
    "is_repost": false,
    "original_post": null,
    "likes_count": 0,
    "dislikes_count": 0,
    "comments_count": 0,
    "reposts_count": 0,
    "replies_count": 0,
    "user_reaction": null,
    "is_saved": false,
    "attributes": {
      "difficulty": "medium",
      "language": "python",
      "duration": "45min",
      "topics": ["classes", "inheritance", "polymorphism"]
    }
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
    "id": 4,
    "author": {
      "id": 2,
      "username": "janedoe",
      "profile_picture": "/media/profile_pictures/jane.jpg"
    },
    "content": "Just launched my new project! 🚀",
    "category": "tech",
    "tags": "django,react,webdev",
    "media": [],
    "likes_count": 0,
    "dislikes_count": 0,
    "comments_count": 0,
    "reposts_count": 0,
    "replies_count": 0,
    "user_reaction": null,
    "is_saved": false,
    "is_repost": true,
    "original_post": {
      "id": 1,
      "author": {
        "id": 1,
        "username": "johndoe"
      }
    },
    "created_at": "2024-01-15T18:30:00Z",
    "updated_at": "2024-01-15T18:30:00Z"
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
        "url": "/media/posts/project_screenshot.jpg",
        "media_type": "image",
        "caption": "",
        "order": 0,
        "file_size": 2048576
      }
    ],
    "likes_count": 25,
    "dislikes_count": 2,
    "comments_count": 8,
    "reposts_count": 3,
    "replies_count": 2,
    "user_reaction": "like",
    "is_saved": false,
    "replies": [
      {
        "id": 3,
        "author": {
          "id": 2,
          "username": "janedoe",
          "profile_picture": "/media/profile_pictures/jane.jpg"
        },
        "content": "This is amazing! Great job!",
        "category": "tech",
        "tags": "",
        "media": [],
        "likes_count": 2,
        "dislikes_count": 0,
        "comments_count": 0,
        "reposts_count": 0,
        "replies_count": 0,
        "user_reaction": null,
        "is_saved": false,
        "created_at": "2024-01-15T16:30:00Z",
        "updated_at": "2024-01-15T16:30:00Z"
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
          "url": "/media/posts/project_screenshot.jpg",
          "media_type": "image",
          "caption": "",
          "order": 0,
          "file_size": 2048576
        }
      ],
      "likes_count": 25,
      "dislikes_count": 2,
      "comments_count": 8,
      "reposts_count": 3,
      "replies_count": 2,
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
curl -X PUT http://89.106.206.119:8000/api/posts/56/update/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "attributes": {
      "difficulty": "hard",
      "language": "python",
      "duration": "60min",
      "topics": ["classes", "inheritance", "polymorphism", "decorators"],
      "prerequisites": ["python basics", "functions"]
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Post updated successfully",
  "post": {
    "id": 56,
    "author": 1,
    "author_info": {
      "id": 1,
      "username": "johndoe",
      "first_name": "John",
      "last_name": "Doe",
      "profile_picture": "/media/profiles/john.jpg",
      "is_email_verified": true,
      "followers_count": 15,
      "following_count": 8,
      "posts_count": 27
    },
    "content": "Advanced Python tutorial with OOP concepts",
    "created_at": "2024-01-16T09:15:00Z",
    "updated_at": "2024-01-16T10:30:00Z",
    "tags": "python,oop,advanced",
    "attributes": {
      "difficulty": "hard",
      "language": "python",
      "duration": "60min",
      "topics": ["classes", "inheritance", "polymorphism", "decorators"],
      "prerequisites": ["python basics", "functions"]
    },
    "likes_count": 0,
    "dislikes_count": 0,
    "comments_count": 0,
    "reposts_count": 0,
    "replies_count": 0,
    "user_reaction": null,
    "is_saved": false
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
          "url": "/media/posts/project_screenshot.jpg",
          "media_type": "image",
          "caption": "",
          "order": 0,
          "file_size": 2048576
        }
      ],
      "likes_count": 25,
      "dislikes_count": 2,
      "comments_count": 8,
      "reposts_count": 3,
      "replies_count": 2,
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
          "url": "/media/posts/project_screenshot.jpg",
          "media_type": "image",
          "caption": "",
          "order": 0,
          "file_size": 2048576
        }
      ],
      "likes_count": 25,
      "dislikes_count": 2,
      "comments_count": 8,
      "reposts_count": 3,
      "replies_count": 2,
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
    "user": 2,
    "user_info": {
      "id": 2,
      "username": "janedoe",
      "first_name": "Jane",
      "last_name": "Doe",
      "profile_picture": "/media/profiles/jane.jpg",
      "is_email_verified": true,
      "followers_count": 120,
      "following_count": 45,
      "posts_count": 67
    },
    "post": 1,
    "content": "Great work! This looks amazing! 👏",
    "created_at": "2024-01-15T16:00:00Z",
    "parent": null,
    "likes_count": 0,
    "replies_count": 0,
    "is_liked": false
  },
  "comments_count": 9
}
```


### Like Comment
```bash
curl -X POST http://89.106.206.119:8000/api/comments/1/like/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "message": "Liked",
  "likes_count": 12,
  "dislikes_count": 2,
  "is_liked": true,
  "is_disliked": false
}
```

### Dislike Comment
```bash
curl -X POST http://89.106.206.119:8000/api/comments/1/dislike/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "success": true,
  "message": "Disliked",
  "likes_count": 12,
  "dislikes_count": 2,
  "is_liked": false,
  "is_disliked": true
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
    "user": 2,
    "user_info": {
      "id": 2,
      "username": "janedoe",
      "profile_picture": "/media/profile_pictures/jane.jpg"
    },
    "content": "Updated comment with more details!",
    "likes_count": 0,
    "replies_count": 0,
    "is_liked": false,
    "created_at": "2024-01-15T16:00:00Z"
  }
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
      "email": "jane@example.com",
      "first_name": "Jane",
      "last_name": "Doe",
      "profile_picture": "/media/profiles/jane.jpg",
      "bio": "Digital artist and designer",
      "student_id": null,
      "is_email_verified": true,
      "followers_count": 120,
      "following_count": 45,
      "posts_count": 67,
      "is_following": true,
      "is_me": false,
      "created_at": "2024-01-10T08:15:00Z"
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
      "email": "jane@example.com",
      "first_name": "Jane",
      "last_name": "Doe",
      "profile_picture": "/media/profiles/jane.jpg",
      "bio": "Digital artist and designer",
      "student_id": null,
      "is_email_verified": true,
      "followers_count": 120,
      "following_count": 45,
      "posts_count": 67,
      "is_following": true,
      "is_me": false,
      "created_at": "2024-01-10T08:15:00Z"
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
      "sender": 2,
      "sender_info": {
        "id": 2,
        "username": "janedoe",
        "first_name": "Jane",
        "last_name": "Doe",
        "profile_picture": "/media/profiles/jane.jpg",
        "is_email_verified": true,
        "followers_count": 120,
        "following_count": 45,
        "posts_count": 67
      },
      "notif_type": "like",
      "post": 1,
      "comment": null,
      "message": "janedoe liked your post",
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
      "other_user": {
        "id": 2,
        "username": "janedoe",
        "first_name": "Jane",
        "last_name": "Doe",
        "profile_picture": "/media/profiles/jane.jpg",
        "is_email_verified": true,
        "followers_count": 120,
        "following_count": 45,
        "posts_count": 67
      },
      "last_message": {
        "content": "Looking forward to it!",
        "sender": "janedoe",
        "created_at": "2024-01-15T17:00:00Z",
        "is_read": true
      },
      "unread_count": 0,
      "updated_at": "2024-01-15T17:00:00Z"
    }
  ],
  "count": 1
}
```

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
    "other_user": {
      "id": 2,
      "username": "janedoe",
      "first_name": "Jane",
      "last_name": "Doe",
      "profile_picture": "/media/profiles/jane.jpg",
      "is_email_verified": true,
      "followers_count": 120,
      "following_count": 45,
      "posts_count": 67
    },
    "last_message": null,
    "unread_count": 0,
    "updated_at": "2024-01-15T18:00:00Z"
  },
  "message": "Conversation started successfully"
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
    "sender": 1,
    "sender_info": {
      "id": 1,
      "username": "johndoe",
      "first_name": "John",
      "last_name": "Doe",
      "profile_picture": "/media/profiles/john.jpg",
      "is_email_verified": true,
      "followers_count": 15,
      "following_count": 8,
      "posts_count": 25
    },
    "content": "Hey! How are you doing?",
    "image": null,
    "file": null,
    "is_read": false,
    "created_at": "2024-01-15T17:05:00Z"
  }
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
    "other_user": {
      "id": 2,
      "username": "janedoe",
      "profile_picture": "/media/profile_pictures/jane.jpg"
    },
    "last_message": {
      "content": "Looking forward to it!",
      "sender": "janedoe",
      "created_at": "2024-01-15T17:00:00Z",
      "is_read": true
    },
    "unread_count": 0,
    "updated_at": "2024-01-15T17:00:00Z"
  },
  "messages": [
    {
      "id": 6,
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


## 📁 Category Format Endpoints

### Upload Category Format (Superuser Only)
```bash
curl -X POST http://89.106.206.119:8000/api/formats/upload/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: multipart/form-data" \
  -F "category=programming" \
  -F "format_file=@/path/to/format.json"
```

**Response:**
```json
{
  "success": true,
  "message": "Format uploaded successfully",
  "format": {
    "id": 1,
    "category": "programming",
    "file_url": "/media/category_formats/format_123.json",
    "created_by": 1,
    "created_by_info": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "first_name": "Admin",
      "last_name": "User",
      "profile_picture": "/media/profiles/admin.jpg",
      "is_email_verified": true,
      "followers_count": 15,
      "following_count": 8,
      "posts_count": 25
    },
    "created_at": "2024-01-15T12:00:00Z",
    "updated_at": "2024-01-15T12:00:00Z"
  }
}
```

### Get Category Format (Public)
```bash
curl -X GET http://89.106.206.119:8000/api/formats/programming/
```

**Response:**
```json
{
  "success": true,
  "category": "programming",
  "format": {
    "required_fields": ["title", "description", "code"],
    "optional_fields": ["tags", "language", "difficulty"],
    "max_length": 5000,
    "allowed_media_types": ["image", "code_snippet"],
    "validation_rules": {
      "title": {
        "min_length": 5,
        "max_length": 200
      },
      "code": {
        "max_size": 10000
      }
    }
  },
  "last_updated": "2024-01-15T12:00:00Z"
}
```

### Delete Category Format (Superuser Only)
```bash
curl -X DELETE http://89.106.206.119:8000/api/formats/programming/delete/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "success": true,
  "message": "Format deleted successfully"
}
```

### Example Format JSON File
**format.json:**
```json
{
  "required_fields": ["title", "description", "code"],
  "optional_fields": ["tags", "language", "difficulty"],
  "max_length": 5000,
  "allowed_media_types": ["image", "code_snippet"],
  "validation_rules": {
    "title": {
      "min_length": 5,
      "max_length": 200
    },
    "code": {
      "max_size": 10000
    }
  },
  "template": {
    "title": "Post Title",
    "description": "Describe your code...",
    "code": "// Your code here",
    "language": "python",
    "difficulty": "beginner"
  }
}
```

## 🏦 Wallet Endpoints

### Get User Wallet
```bash
curl -X GET http://89.106.206.119:8000/api/wallet/mywallet/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Successful Response:**
```json
{
  "error": false,
  "message": "کیف پول با موفقیت دریافت شد",
  "code": "USER_WALLET_FETCHED",
  "data": {
    "id": 1,
    "user": 1,
    "balance": 150000,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
}
```

**Error Response (Wallet Not Found):**
```json
{
  "error": true,
  "message": "کیف پول یافت نشد",
  "code": "USER_WALLET_NOT_FOUND"
}
```

### Deposit Funds (Increase Balance)
```bash
curl -X POST http://89.106.206.119:8000/api/wallet/deposit/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50000
  }'
```

**Successful Response:**
```json
{
  "error": false,
  "message": "موجودی با موفقیت افزایش یافت",
  "code": "WALLET_DEPOSIT_SUCCESSFUL",
  "data": {
    "transaction_id": 123,
    "new_balance": 200000,
    "previous_balance": 150000,
    "amount": 50000,
    "timestamp": "2024-01-15T15:30:00Z"
  }
}
```

**Error Responses:**

**Invalid Amount:**
```json
{
  "error": true,
  "message": "مقدار وارد شده نامعتبر است",
  "code": "WALLET_INVALID_AMOUNT"
}
```

**Server Error:**
```json
{
  "error": true,
  "message": "خطای داخلی سرور",
  "code": "SERVER_ERROR"
}
```

### Withdraw Funds (Decrease Balance)
```bash
curl -X POST http://89.106.206.119:8000/api/wallet/withdraw/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 20000
  }'
```

**Successful Response:**
```json
{
  "error": false,
  "message": "برداشت با موفقیت انجام شد",
  "code": "WALLET_WITHDRAW_SUCCESSFUL",
  "data": {
    "transaction_id": 124,
    "new_balance": 180000,
    "previous_balance": 200000,
    "amount": 20000,
    "timestamp": "2024-01-15T15:45:00Z"
  }
}
```

**Error Responses:**

**Insufficient Balance:**
```json
{
  "error": true,
  "message": "موجودی کافی نیست",
  "code": "INSUFFICIENT_BALANCE"
}
```

**Invalid Amount:**
```json
{
  "error": true,
  "message": "مقدار وارد شده نامعتبر است",
  "code": "WALLET_INVALID_AMOUNT"
}
```

### Transfer Funds to Another User
```bash
curl -X POST http://89.106.206.119:8000/api/wallet/transfer/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "to_user_id": 2,
    "amount": 30000
  }'
```

**Successful Response:**
```json
{
  "error": false,
  "message": "انتقال با موفقیت انجام شد",
  "code": "WALLET_TRANSFER_SUCCESSFUL",
  "data": {
    "transaction_id": 125,
    "sender_new_balance": 150000,
    "receiver_new_balance": 80000,
    "amount": 30000,
    "receiver_username": "janedoe",
    "timestamp": "2024-01-15T16:00:00Z"
  }
}
```

**Error Responses:**

**User Not Found:**
```json
{
  "error": true,
  "message": "کاربر وارد شده یافت نشد",
  "code": "USER_NOT_FOUND"
}
```

**Insufficient Balance:**
```json
{
  "error": true,
  "message": "موجودی کافی نیست",
  "code": "INSUFFICIENT_BALANCE"
}
```

**Invalid Amount:**
```json
{
  "error": true,
  "message": "مقدار وارد شده نامعتبر است",
  "code": "WALLET_INVALID_AMOUNT"
}
```

### Get User Transactions (History)
```bash
curl -X GET http://89.106.206.119:8000/api/wallet/transactions/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Successful Response:**
```json
{
  "error": false,
  "message": "تراکنش های کاربر یافت شد",
  "code": "USER_TRANSACTION_FETCHED",
  "data": [
    {
      "id": 123,
      "wallet": 1,
      "amount": 50000,
      "transaction_type": "deposit",
      "status": "completed",
      "description": "افزایش موجودی",
      "related_user": null,
      "registered_in": "2024-01-15T15:30:00Z"
    },
    {
      "id": 124,
      "wallet": 1,
      "amount": 20000,
      "transaction_type": "withdraw",
      "status": "completed",
      "description": "برداشت وجه",
      "related_user": null,
      "registered_in": "2024-01-15T15:45:00Z"
    },
    {
      "id": 125,
      "wallet": 1,
      "amount": 30000,
      "transaction_type": "transfer",
      "status": "completed",
      "description": "انتقال به janedoe",
      "related_user": 2,
      "registered_in": "2024-01-15T16:00:00Z"
    }
  ]
}
```

**Error Responses:**

**Wallet Not Found:**
```json
{
  "error": true,
  "message": "کیف پول یافت نشد",
  "code": "USER_WALLET_NOT_FOUND"
}
```

**No Transactions:**
```json
{
  "error": true,
  "message": "تراکنشی وجود ندارد",
  "code": "USER_TRANSACTION_NOT_EXIST"
}
```

## ⚠️ Error Responses

### Format Not Found
```json
{
  "success": false,
  "message": "No format found for category: programming"
}
```

### Permission Denied (Non-Superuser)
```json
{
  "success": false,
  "message": "Only superusers can upload format files"
}
```

### Invalid JSON File
```json
{
  "success": false,
  "message": "Invalid JSON file"
}
```

### File Type Error
```json
{
  "success": false,
  "message": "Only JSON files are allowed"
}
```

### Missing Required Fields
```json
{
  "success": false,
  "message": "Category is required"
}
```

### Validation Error
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

### Authentication Error
```json
{
  "success": false,
  "message": "Authentication credentials were not provided."
}
```

### Not Found Error
```json
{
  "success": false,
  "message": "Not found."
}
```

### Permission Error
```json
{
  "success": false,
  "message": "You do not have permission to perform this action."
}
```
